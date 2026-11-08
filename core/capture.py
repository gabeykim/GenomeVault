"""M3 capture: label photo -> generic ingredients (PLAN F2, M3, S2; CONTRACTS `capture.from_image`, D-020).

`from_image(data, mime)` reads the text on a medication label photo and hands it to
`normalize.to_ingredients`. It returns `[]` for anything it cannot read and never raises, so the phone
page can always fall back to typed input (`from_text`).

Text sources, all on this machine (I2: no network, no new Python dependency):

1. **Embedded label text.** A PNG text chunk (`tEXt`/`zTXt`/`iTXt`) with keyword `gv:label`, or a
   JPEG comment segment that starts with `gv:label`. The bundled demo photos and the tests use this,
   so S2 runs the same way with no OCR engine installed (I8). `demo_png(text)` builds such an image.
2. **Tesseract OCR**, only if the `tesseract` program is on PATH. It runs as a local subprocess on the
   image bytes, with a timeout.

`GV_OCR` picks the sources: `auto` (default: 1 then 2), `embedded`, `tesseract`, or `off`.

The label text (which can include a name, Rx number or pharmacy) never leaves this module: only the
`Drug` list is returned, and nothing is logged or stored.
"""
from __future__ import annotations

import os
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


def from_image(data: bytes, mime: str) -> list[Drug]:
    """Label photo -> ingredients. `[]` if the image is unreadable or names no known drug."""
    try:
        text = read_text(data, mime)
    except Exception:                  # a bad upload must never break the phone page
        return []
    return to_ingredients(text) if text else []


def from_text(text: str) -> list[Drug]:
    """Typed fallback (F2): the same normalizer the photo path ends in."""
    return to_ingredients(text or "")


def read_text(data: bytes, mime: str) -> str:
    """Label text from the image, or "" if none can be read. Stays local (see module doc)."""
    kind = sniff(data)
    if not kind or not str(mime or "").lower().startswith("image/") or len(data) > MAX_BYTES:
        return ""
    mode = os.environ.get("GV_OCR", "auto").strip().lower()
    if mode == "off":
        return ""
    text = ""
    if mode in ("auto", "embedded"):
        text = embedded_text(data, kind)
    if not text and mode in ("auto", "tesseract"):
        text = tesseract_text(data)
    return text[:_TEXT_CAP]


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
