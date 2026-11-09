"""G3 (human request 20261108-1516): capture.from_image on full pharmacy labels for Alex's five discharge
meds plus an amoxicillin label (S6 penicillin-allergy beat). Each label must give exactly the right Drug,
and an unknown or look-alike name must give no Drug, so C's confirm/edit step gets clean input (F2, M3,
S2, I4).

Every label below is synthetic (I1): made-up pharmacy, patient, prescriber and Rx numbers. Each one has
the parts a real label has, including a warning line that names *other* drugs; those must not be added
(A-013). The labels are tested through every local text path: PNG iTXt, JPEG comment, faked tesseract
OCR text, and a faked local vision-model reply (D-029). No real OCR engine or model is needed.
"""
import struct

import pytest

from core import capture, local_llm, rules
from core.contracts import Drug

from .test_alex_flags import _alex

HEAD = "SYNTHETIC PHARMACY  555-0100\nRx# 00001{n}   ALEX SAMPLE   DR. R. EXAMPLE\n"

# ingredient -> (label text, expected Drug, (brand, ingredient, strength) as a vision model would read it)
LABELS = {
    "aspirin": (
        HEAD.format(n=21) + "ASPIRIN 81 MG EC TABLET\nGeneric for: ECOTRIN LOW STRENGTH\n"
        "TAKE 1 TABLET BY MOUTH ONCE DAILY WITH FOOD\n"
        "Do not take ibuprofen or naproxen without asking your doctor.\nQTY: 90   REFILLS: 3",
        Drug(ingredient="aspirin", dose_mg=81), ("Ecotrin", "aspirin", 81)),
    "clopidogrel": (
        HEAD.format(n=22) + "CLOPIDOGREL 75 MG TABLET\nGeneric for: PLAVIX\nTAKE 1 TABLET BY MOUTH ONCE DAILY\n"
        "Do not stop taking unless told by your cardiologist. Avoid omeprazole and esomeprazole.\n"
        "QTY: 30   REFILLS: 11",
        Drug(ingredient="clopidogrel", dose_mg=75), ("Plavix", "clopidogrel", 75)),
    "omeprazole": (
        HEAD.format(n=23) + "OMEPRAZOLE DR 20 MG CAPSULE\nGeneric for: PRILOSEC\n"
        "TAKE 1 CAPSULE BY MOUTH DAILY BEFORE BREAKFAST\n"
        "Swallow whole. Tell your doctor if you take clopidogrel.\nQTY: 30   REFILLS: 5",
        Drug(ingredient="omeprazole", dose_mg=20), ("Prilosec", "omeprazole", 20)),
    "simvastatin": (
        HEAD.format(n=24) + "SIMVASTATIN 40 MG TABLET\nGeneric for: ZOCOR\nTAKE 1 TABLET BY MOUTH AT BEDTIME\n"
        "Avoid grapefruit juice. Do not take with gemfibrozil, amiodarone or clarithromycin.\n"
        "QTY: 30   REFILLS: 5",
        Drug(ingredient="simvastatin", dose_mg=40), ("Zocor", "simvastatin", 40)),
    "lisinopril": (
        HEAD.format(n=25) + "LISINOPRIL 10 MG TABLET\nGeneric for: ZESTRIL / PRINIVIL\n"
        "TAKE 1 TABLET BY MOUTH ONCE DAILY\n"
        "May cause dizziness. Avoid potassium supplements and ibuprofen unless your doctor approves.\n"
        "QTY: 30   REFILLS: 5",
        Drug(ingredient="lisinopril", dose_mg=10), ("Zestril", "lisinopril", 10)),
    "amoxicillin": (
        HEAD.format(n=26) + "AMOXICILLIN 500 MG CAPSULE\nGeneric for: AMOXIL\n"
        "TAKE 1 CAPSULE BY MOUTH 3 TIMES DAILY FOR 10 DAYS\n"
        "Finish all of this medication unless told otherwise.\nQTY: 30   REFILLS: 0",
        Drug(ingredient="amoxicillin", dose_mg=500), ("Amoxil", "amoxicillin", 500)),
}

# Labels whose product name is not in the table: a look-alike of Plavix, a made-up drug, and a label
# whose product line is unreadable but whose warning names a real drug. All must give no Drug (I4).
UNKNOWN = {
    "look-alike": HEAD.format(n=31) + "PLAVLX 75 MG TABLET\nTAKE 1 TABLET BY MOUTH ONCE DAILY\nQTY: 30",
    "made-up": HEAD.format(n=32) + "FOOZOLAMIDE 10 MG TABLET\nTAKE 1 TABLET DAILY\nQTY: 30",
    "header only": HEAD.format(n=33) + "QTY: 30   REFILLS: 0",
}

# The flags each discharge med gives Alex when typed (PLAN P5, test_alex_flags); amoxicillin -> AL-001.
FLAG_IDS = {"aspirin": [], "clopidogrel": ["X1", "X2"], "omeprazole": ["X2"], "simvastatin": ["X3"],
            "lisinopril": ["X4"], "amoxicillin": ["AL-001"]}


def _jpeg(text: str) -> bytes:
    comment = capture.LABEL_KEY + b": " + text.encode("utf-8")
    app0 = b"\xff\xe0" + struct.pack(">H", 16) + b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    com = b"\xff\xfe" + struct.pack(">H", len(comment) + 2) + comment
    return b"\xff\xd8" + app0 + com + b"\xff\xda\x00\x08\x01\x01\x00\x00\x3f\x00" + b"\x00" * 16 + b"\xff\xd9"


def _strip_text(png: bytes) -> bytes:
    """The same PNG with its label text removed: a camera photo with nothing embedded."""
    pos, out = len(capture._PNG_SIG), [capture._PNG_SIG]
    while pos + 8 <= len(png):
        (length,) = struct.unpack(">I", png[pos:pos + 4])
        ctype = png[pos + 4:pos + 8]
        if ctype != b"iTXt":
            out.append(png[pos:pos + 12 + length])
        pos += 12 + length
    return b"".join(out)


@pytest.fixture(autouse=True)
def _local_only(monkeypatch):
    """No real tesseract or vision model; the tests that need one fake it."""
    monkeypatch.setattr(capture.shutil, "which", lambda name: None)
    monkeypatch.setattr(local_llm, "VLM_MODEL", "", raising=False)
    monkeypatch.delenv("GV_OCR", raising=False)


def _vlm(monkeypatch, brand, ingredient, strength):
    monkeypatch.setattr(local_llm, "VLM_MODEL", "qwen2.5vl:7b", raising=False)
    reply = {"brand_name": brand, "ingredient": ingredient, "strength_mg": strength}
    monkeypatch.setattr(local_llm, "generate", lambda *a, **kw: __import__("json").dumps(reply))


@pytest.mark.parametrize("med", LABELS)
def test_png_label_gives_exactly_the_right_drug(med):
    text, want, _ = LABELS[med]
    assert capture.from_image(capture.demo_png(text), "image/png") == [want]


@pytest.mark.parametrize("med", LABELS)
def test_jpeg_label_gives_exactly_the_right_drug(med):
    text, want, _ = LABELS[med]
    assert capture.from_image(_jpeg(text), "image/jpeg") == [want]


@pytest.mark.parametrize("med", LABELS)
def test_ocr_text_of_label_gives_exactly_the_right_drug(monkeypatch, med):
    text, want, _ = LABELS[med]
    monkeypatch.setattr(capture, "tesseract_text", lambda data: text)
    assert capture.from_image(_strip_text(capture.demo_png("x")), "image/png") == [want]


@pytest.mark.parametrize("med", LABELS)
@pytest.mark.parametrize("which", ["brand+ingredient", "brand only", "ingredient only"])
def test_vision_model_read_gives_exactly_the_right_drug(monkeypatch, med, which):
    _, want, (brand, ingredient, strength) = LABELS[med]
    if which == "brand only":
        ingredient = None
    if which == "ingredient only":
        brand = None
    _vlm(monkeypatch, brand, ingredient, strength)
    assert capture.from_image(_strip_text(capture.demo_png("x")), "image/png") == [want]


@pytest.mark.parametrize("name", UNKNOWN)
def test_unknown_label_gives_no_drug(monkeypatch, name):
    text = UNKNOWN[name]
    assert capture.from_image(capture.demo_png(text), "image/png") == []
    assert capture.from_image(_jpeg(text), "image/jpeg") == []
    monkeypatch.setattr(capture, "tesseract_text", lambda data: text)
    assert capture.from_image(_strip_text(capture.demo_png("x")), "image/png") == []


@pytest.mark.parametrize("brand", ["Plavlx", "Foozol", "Amoxyl"])
def test_vision_model_misread_gives_no_drug(monkeypatch, brand):
    _vlm(monkeypatch, brand, None, 75)
    assert capture.from_image(_strip_text(capture.demo_png("x")), "image/png") == []


@pytest.mark.parametrize("warning", [
    "Do not take aspirin or ibuprofen.",
    "Avoid omeprazole and esomeprazole.",
    "Tell your doctor if you take clopidogrel.",
    "Ask a doctor before use if you take a blood thinner such as warfarin.",
    "May cause bleeding with aspirin 81 mg.",
])
def test_warning_drug_never_becomes_the_product(monkeypatch, warning):
    """An unreadable product line (OCR misread "PLAVLX") must not let the warning's drug stand in for
    the product: a misread Plavix label saying "Avoid omeprazole" would otherwise offer omeprazole and
    raise a false X2. The label gives no Drug, and C falls back to typed input."""
    text = HEAD.format(n=34) + f"PLAVLX 75 MG TABLET\nTAKE 1 TABLET DAILY\n{warning}\nQTY: 30"
    assert capture.from_image(capture.demo_png(text), "image/png") == []
    monkeypatch.setattr(capture, "tesseract_text", lambda data: text)
    assert capture.from_image(_strip_text(capture.demo_png("x")), "image/png") == []


@pytest.mark.parametrize("label, want", [
    ("CLOPIDOGREL 75 MG TABLET - do not crush or chew", Drug(ingredient="clopidogrel", dose_mg=75)),
    ("SIMVASTATIN 40 MG TAB  avoid grapefruit", Drug(ingredient="simvastatin", dose_mg=40)),
    ("Generic for: PLAVIX\nclopidogrel 75 mg", Drug(ingredient="clopidogrel", dose_mg=75)),
])
def test_cue_after_the_drug_name_is_still_the_product(label, want):
    assert capture.from_image(capture.demo_png(label), "image/png") == [want]


@pytest.mark.parametrize("med", LABELS)
def test_photo_gives_same_flags_as_typing_the_med(med):
    """C's confirm step gets input that flags exactly like the typed name: X1-X4 for the discharge
    meds, AL-001 for amoxicillin (Alex's penicillin allergy), nothing extra from label warnings."""
    text, want, _ = LABELS[med]
    alex = _alex()
    (drug,) = capture.from_image(capture.demo_png(text), "image/png")
    assert drug == want
    assert sorted(f.id for f in rules.check(drug, alex)) == FLAG_IDS[med]
    assert rules.check(drug, alex) == rules.check(capture.from_text(f"{med} {want.dose_mg:g} mg")[0], alex)
