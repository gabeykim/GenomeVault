"""M3 capture: label photo -> generic ingredients (PLAN F2, M3, S2; CONTRACTS `capture.from_image`, D-020).

`from_image(data, mime)` reads the text on a medication label photo and hands it to
`normalize.to_ingredients`. It returns `[]` for anything it cannot read and never raises, so the phone
page can always fall back to typed input (`from_text`).

Text sources, all on this machine (I2: no network, no new Python dependency):

1. **Embedded label text.** A PNG text chunk (`tEXt`/`zTXt`/`iTXt`) with keyword `gv:label`, or a
   JPEG comment segment that starts with `gv:label`. The bundled demo photos and the tests use this,
   so S2 runs the same way with no OCR engine installed (I8). `demo_png(text)` builds such an image.
2. **Local vision model** (D-029), only if `local_llm.VLM_MODEL` is set (`LOCAL_VLM_MODEL`, e.g.
   `qwen2.5vl:7b` under Ollama on localhost, I2). It is asked for `{brand_name, ingredient,
   strength_mg}` as JSON. The model only reads: each name still goes through the exact-key
   `normalize` table, so an unknown or misspelled name gives `[]` (I4, never a guess). If the brand
   and the ingredient both resolve but name different drugs, the answer is `[]` too. If the model is
   not configured, not running, or answers with something that is not that JSON, this source is
   skipped and the next one runs.
3. **Tesseract OCR**, only if the `tesseract` program is on PATH. It runs as a local subprocess on the
   image bytes, with a timeout.

`GV_OCR` picks the sources: `auto` (default: 1, then 2, then 3), `embedded`, `vlm`, `tesseract`, or
`off`. In `auto`, the first source that reads anything decides; later ones don't run.

Label text from sources 1 and 3 goes through `label_drugs`: one label is one product, so drug names in
its warnings ("do not take aspirin or ibuprofen") are not added. Typed text (`from_text`) keeps every
name.

The photo goes only to the localhost model (I2). The label text (which can include a name, Rx number
or pharmacy) never leaves this module: only the `Drug` list is returned, and no label text is logged
or stored. The only log line is a one-time setup hint when the vision model is skipped (`_skip`).
"""
from __future__ import annotations

import base64
import json
import logging
import os
import re
import shutil
import struct
import subprocess
import zlib

from .contracts import Drug
from .normalize import to_ingredients

LABEL_KEY = b"gv:label"
MAX_BYTES = 15 * 1024 * 1024           # larger uploads are refused as unreadable
OCR_TIMEOUT_S = 30
_PNG_SIG = b"\x89PNG\r\n\x1a\n"
_TEXT_CAP = 20_000                     # characters of label text passed to normalize
_SENTENCE_END = re.compile(r"(?<=[.;!?])\s+")   # "12.5" has no space after the dot, so it stays whole
# Words that open a label warning or direction about *other* drugs ("Do not take aspirin", "Avoid
# omeprazole", "Tell your doctor if you take clopidogrel"). A piece where one comes before any drug
# name is a warning, never the product line.
_WARNING_CUE = re.compile(
    r"\b(?:do not|don'?t|never|avoid|unless|without|except|caution|warnings?|consult|"
    r"ask (?:a|your)|tell your|if you|such as|interact\w*|stop (?:use|taking)|allerg\w*|"
    r"may (?:cause|increase))\b", re.IGNORECASE)


_VLM_PROMPT = (
    "Read this medication label. Reply with JSON only, exactly these keys: "
    '{"brand_name": string or null, "ingredient": string or null, "strength_mg": number or null}. '
    "Copy names as printed on the label. Use null for anything not printed. Do not guess."
)
_VLM_FIELD_CAP = 200                   # characters kept from each field the model returns
_STRENGTH_OK = set("0123456789./ ,mgcuµ")


def from_image(data: bytes, mime: str) -> list[Drug]:
    """Label photo -> ingredients. `[]` if the image is unreadable or names no known drug."""
    try:
        if not _acceptable(data, mime):
            return []
        mode = _mode()
        if mode in ("auto", "embedded"):
            text = embedded_text(data, sniff(data))
            if text or mode == "embedded":
                return label_drugs(text)
        if mode in ("auto", "vlm"):
            drugs = vlm_drugs(data)
            if drugs is not None or mode == "vlm":
                return drugs or []
        if mode in ("auto", "tesseract"):
            return label_drugs(tesseract_text(data))
        return []
    except Exception:                  # a bad upload must never break the phone page
        return []


def from_text(text: str) -> list[Drug]:
    """Typed fallback (F2): the same normalizer the photo path ends in. Typed text keeps every name
    (the user typed what they take); only label text gets the one-product rule of `label_drugs`."""
    return to_ingredients(text or "")


def label_drugs(text: str) -> list[Drug]:
    """Label text -> the drugs of the one product the label is for.

    A label also names drugs the user is *not* taking, in warnings ("Do not take aspirin or other
    NSAIDs such as ibuprofen"). Reading the whole text would add those, and a Plavix label alone would
    fire X5. So the text is cut into lines and sentences and only the first piece that names a drug
    counts (labels print the product before warnings). A combination pill stays whole, because both
    names sit in that one piece. If that piece has no strength, the strength comes from a later piece
    naming exactly the same ingredients ("PLAVIX" ... "clopidogrel 75 mg"), or from the very next
    piece when name and strength were split across lines ("LISINOPRIL-HCTZ" / "20-12.5 MG").

    Warning pieces never count (`_is_warning`). Without this, a label whose product line could not be
    read (an OCR misread "PLAVLX") would be taken for the drug in its warning ("Avoid omeprazole"),
    and C's confirm step would offer a drug the user does not take. Such a label gives `[]` (I4)."""
    pieces = [p.strip() for line in (text or "")[:_TEXT_CAP].splitlines()
              for p in _SENTENCE_END.split(line) if p.strip()]
    named = [(i, to_ingredients(p)) for i, p in enumerate(pieces)]
    named = [(i, d) for i, d in named if d and not _is_warning(pieces[i])]
    if not named:
        return []
    first, drugs = named[0]
    if any(d.dose_mg is not None for d in drugs):
        return drugs
    names = {d.ingredient for d in drugs}
    for _, later in named[1:]:
        if {d.ingredient for d in later} == names and any(d.dose_mg is not None for d in later):
            return later
    if first + 1 < len(pieces):
        joined = to_ingredients(f"{pieces[first]} {pieces[first + 1]}")
        if {d.ingredient for d in joined} == names:
            return joined
    return drugs


def _is_warning(piece: str) -> bool:
    """True if a warning cue comes before any drug name in this piece ("Do not take aspirin"), so
    "CLOPIDOGREL 75 MG - do not crush" is still a product line."""
    cue = _WARNING_CUE.search(piece)
    return bool(cue) and not to_ingredients(piece[:cue.start()])


def read_text(data: bytes, mime: str) -> str:
    """Label text from the text sources (embedded, tesseract; the vision model returns fields, not
    text), or "" if none can be read. Stays local (see module doc)."""
    if not _acceptable(data, mime):
        return ""
    kind, mode = sniff(data), _mode()
    text = ""
    if mode in ("auto", "embedded"):
        text = embedded_text(data, kind)
    if not text and mode in ("auto", "tesseract"):
        text = tesseract_text(data)
    return text[:_TEXT_CAP]


def _acceptable(data: bytes, mime: str) -> bool:
    return bool(sniff(data)) and str(mime or "").lower().startswith("image/") and len(data) <= MAX_BYTES


def _mode() -> str:
    return os.environ.get("GV_OCR", "auto").strip().lower()


def vlm_drugs(data: bytes) -> list[Drug] | None:
    """Drugs read by the local vision model (D-029). `None` if the model is unavailable or its answer
    is not the expected JSON (so the next source runs); `[]` if it read the label but no name is in
    the table, or the brand and ingredient disagree. Each skip reason is logged once (`_skip`)."""
    model = ""
    try:
        from . import local_llm
        model = getattr(local_llm, "VLM_MODEL", "") or ""
        if not model or model == "set-me":
            return _skip("unset", "no vision model configured: add LOCAL_VLM_MODEL=qwen2.5vl:7b to .env "
                                  "(see .env.example), so label photos skip the model")
        raw = local_llm.generate(_VLM_PROMPT, images=[base64.b64encode(bytes(data)).decode("ascii")],
                                 format="json", model=model)
    except Exception as exc:           # not running, old client without images=
        return _skip("down", f"vision model {model or '?'} did not answer ({type(exc).__name__}); "
                             "is Ollama running with that model pulled?")
    try:
        fields = json.loads(raw)
    except Exception:
        fields = None
    if not isinstance(fields, dict):
        return _skip("json", f"vision model {model} did not reply with the expected JSON")
    brand, ingredient = _field(fields.get("brand_name")), _field(fields.get("ingredient"))
    if not brand and not ingredient:
        return None                    # read nothing: a normal outcome, not a setup problem
    return drugs_from_fields(brand, ingredient, fields.get("strength_mg"))


_log = logging.getLogger("genomevault.capture")
_skipped: set[str] = set()


def _skip(reason: str, message: str) -> None:
    """Log once per process why the vision model was skipped. With `GV_OCR=vlm` the user asked for the
    model, so this is a WARNING (a missing `LOCAL_VLM_MODEL` used to return `[]` in 0.0 s with no
    hint, to-A 1602); in `auto` it is DEBUG, because running without a model is the normal I8 path.
    The message names only the setting and the model: never label text or any image content."""
    if reason not in _skipped:
        _skipped.add(reason)
        _log.log(logging.WARNING if _mode() == "vlm" else logging.DEBUG, "capture: %s", message)
    return None


def drugs_from_fields(brand: str, ingredient: str, strength=None) -> list[Drug]:
    """{brand_name, ingredient, strength_mg} -> Drugs through the exact-key table (I4).

    Each name is normalized on its own. If both resolve, one ingredient set must contain the other
    (a model that reads "Zestoretic" but only "lisinopril" keeps both of Zestoretic's); otherwise
    they name different drugs and the answer is `[]`. The strength is applied by `normalize`'s own
    dose parser, so a combination strength like "20/12.5" splits the same way typed text does."""
    from_brand = {d.ingredient for d in to_ingredients(brand)} if brand else set()
    from_ing = {d.ingredient for d in to_ingredients(ingredient)} if ingredient else set()
    if from_brand and from_ing and not (from_brand <= from_ing or from_ing <= from_brand):
        return []
    name = brand if len(from_brand) >= len(from_ing) else ingredient
    if not name or not (from_brand | from_ing):
        return []
    dose = _strength(strength)
    drugs = to_ingredients(f"{name} {dose}" if dose else name)
    return drugs if {d.ingredient for d in drugs} == (from_brand | from_ing) else []


def _field(value) -> str:
    return value.strip()[:_VLM_FIELD_CAP] if isinstance(value, str) else ""


def _strength(value) -> str:
    """The model's strength as dose text for `normalize`, or "" if it isn't a plain strength."""
    if isinstance(value, bool) or value is None:
        return ""
    if isinstance(value, (int, float)):
        return f"{value:g} mg" if 0 < value < 100_000 else ""
    if isinstance(value, str):
        v = value.strip().lower()[:30]
        if v and v[0].isdigit() and set(v) <= _STRENGTH_OK:
            return v if any(c.isalpha() for c in v) else f"{v} mg"
    return ""


def sniff(data: bytes) -> str:
    """Image type from the magic bytes (the stated MIME type is not trusted). "" if not an image."""
    if not isinstance(data, (bytes, bytearray)) or len(data) < 12:
        return ""
    head = bytes(data[:12])
    if head.startswith(_PNG_SIG):
        return "png"
    if head.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    if head[:4] in (b"II*\x00", b"MM\x00*"):
        return "tiff"
    if head[:2] == b"BM":
        return "bmp"
    if head[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    return ""


def embedded_text(data: bytes, kind: str) -> str:
    if kind == "png":
        return _png_label(bytes(data))
    if kind == "jpeg":
        return _jpeg_label(bytes(data))
    return ""


def _png_label(data: bytes) -> str:
    pos, parts = len(_PNG_SIG), []
    while pos + 8 <= len(data):
        length, ctype = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        if len(body) < length:
            break                                    # truncated file: keep what was read
        if ctype in (b"tEXt", b"zTXt", b"iTXt"):
            text = _png_text_chunk(ctype, body)
            if text is not None:
                parts.append(text)
        if ctype == b"IEND":
            break
        pos += 12 + length
    return "\n".join(p for p in parts if p).strip()


def _png_text_chunk(ctype: bytes, body: bytes) -> str | None:
    key, sep, rest = body.partition(b"\x00")
    if not sep or key != LABEL_KEY:
        return None
    try:
        if ctype == b"tEXt":
            return rest.decode("latin-1")
        if ctype == b"zTXt":                         # compression method byte, then zlib data
            return zlib.decompress(rest[1:]).decode("latin-1") if rest[:1] == b"\x00" else None
        flag, method = rest[0], rest[1]               # iTXt: flag, method, lang\0, translated\0, text
        _lang, _, rest = rest[2:].partition(b"\x00")
        _tkey, _, text = rest.partition(b"\x00")
        if flag:
            if method != 0:
                return None
            text = zlib.decompress(text)
        return text.decode("utf-8")
    except (IndexError, zlib.error, UnicodeDecodeError):
        return None


def _jpeg_label(data: bytes) -> str:
    pos, parts = 2, []
    while pos + 4 <= len(data) and data[pos] == 0xFF:
        marker = data[pos + 1]
        if marker == 0xFF:                           # fill byte
            pos += 1
            continue
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            pos += 2
            continue
        if marker in (0xDA, 0xD9):                   # start of scan / end: no more headers
            break
        (length,) = struct.unpack(">H", data[pos + 2:pos + 4])
        if length < 2:
            break
        seg = data[pos + 4:pos + 2 + length]
        if marker == 0xFE and seg.startswith(LABEL_KEY):
            parts.append(seg[len(LABEL_KEY):].lstrip(b":\x00 \n").decode("utf-8", "replace"))
        pos += 2 + length
    return "\n".join(p for p in parts if p).strip()


def tesseract_text(data: bytes) -> str:
    """OCR with a local `tesseract` binary if one is installed; "" otherwise or on any failure."""
    exe = shutil.which("tesseract")
    if not exe:
        return ""
    try:
        out = subprocess.run([exe, "stdin", "stdout"], input=bytes(data), capture_output=True,
                             timeout=OCR_TIMEOUT_S, check=False)
    except (OSError, subprocess.SubprocessError):
        return ""
    if out.returncode != 0:
        return ""
    return out.stdout.decode("utf-8", "replace").strip()


def demo_png(label_text: str, width: int = 64, height: int = 40) -> bytes:
    """A small plain synthetic PNG carrying `label_text` as embedded label text (for demo and tests;
    I1: the text must be synthetic)."""
    raw = b"".join(b"\x00" + b"\xf4\xf1\xe8" * width for _ in range(height))

    def chunk(ctype: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + ctype + body + struct.pack(">I", zlib.crc32(ctype + body))

    itxt = LABEL_KEY + b"\x00\x00\x00\x00\x00" + label_text.encode("utf-8")
    return (_PNG_SIG
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"iTXt", itxt)
            + chunk(b"IDAT", zlib.compress(raw))
            + chunk(b"IEND", b""))
