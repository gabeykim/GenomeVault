"""A-025: a skipped vision model says why, once, with no label content (to-A 1602, D-029, F2, I2).

On the demo laptop a `.env` without `LOCAL_VLM_MODEL` made `GV_OCR=vlm` return `[]` in 0.0 s with no
hint. These tests check the one-time log line: WARNING when the user asked for the model, DEBUG in
`auto` (no model is the normal I8 path), and never any label text. The model is faked."""
import logging

import pytest

from core import capture, local_llm
from core.contracts import Drug

from tests.A.test_capture_vlm import _plain_png, FakeVLM

SECRET = "PATIENT Jane Q Synthetic RX#0000-SYN"     # I1: synthetic; must never reach the log


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setattr(capture.shutil, "which", lambda name: None)
    monkeypatch.setattr(capture, "_skipped", set())
    monkeypatch.delenv("GV_OCR", raising=False)


def _records(caplog):
    return [r for r in caplog.records if r.name == "genomevault.capture"]


@pytest.mark.parametrize("value", ["", "set-me"])
def test_vlm_mode_without_model_warns_once(monkeypatch, caplog, value):
    monkeypatch.setattr(local_llm, "VLM_MODEL", value, raising=False)
    monkeypatch.setenv("GV_OCR", "vlm")
    caplog.set_level(logging.DEBUG, logger="genomevault.capture")
    for _ in range(3):
        assert capture.from_image(_plain_png(), "image/png") == []
    (rec,) = _records(caplog)
    assert rec.levelno == logging.WARNING
    assert "LOCAL_VLM_MODEL=qwen2.5vl:7b" in rec.getMessage()


def test_auto_mode_without_model_is_quiet(monkeypatch, caplog):
    monkeypatch.setattr(local_llm, "VLM_MODEL", "set-me", raising=False)
    caplog.set_level(logging.INFO, logger="genomevault.capture")
    assert capture.from_image(capture.demo_png("Plavix 75 mg"), "image/png") == [Drug(ingredient="clopidogrel", dose_mg=75)]
    assert capture.from_image(_plain_png(), "image/png") == []
    assert _records(caplog) == []


def test_model_down_warns_with_type_only_and_no_label_text(monkeypatch, caplog):
    monkeypatch.setattr(local_llm, "VLM_MODEL", "qwen2.5vl:7b", raising=False)
    monkeypatch.setattr(local_llm, "generate", FakeVLM(exc=ConnectionError(SECRET)))
    monkeypatch.setenv("GV_OCR", "vlm")
    caplog.set_level(logging.DEBUG, logger="genomevault.capture")
    img = capture.demo_png(SECRET)
    assert capture.from_image(img, "image/png") == []
    assert capture.from_image(img, "image/png") == []
    (rec,) = _records(caplog)
    msg = rec.getMessage()
    assert rec.levelno == logging.WARNING and "qwen2.5vl:7b" in msg and "ConnectionError" in msg
    assert "Jane" not in msg and "RX#" not in msg


def test_bad_json_warns_once_and_falls_through_in_auto(monkeypatch, caplog):
    monkeypatch.setattr(local_llm, "VLM_MODEL", "qwen2.5vl:7b", raising=False)
    monkeypatch.setattr(local_llm, "generate", FakeVLM(reply="not json " + SECRET))
    monkeypatch.setattr(capture, "tesseract_text", lambda data: "SIMVASTATIN 40 MG")
    caplog.set_level(logging.DEBUG, logger="genomevault.capture")
    assert capture.from_image(_plain_png(), "image/png") == [Drug(ingredient="simvastatin", dose_mg=40)]
    (rec,) = _records(caplog)
    assert rec.levelno == logging.DEBUG and "Jane" not in rec.getMessage()


def test_good_read_logs_nothing(monkeypatch, caplog):
    monkeypatch.setattr(local_llm, "VLM_MODEL", "qwen2.5vl:7b", raising=False)
    monkeypatch.setattr(local_llm, "generate",
                        FakeVLM(reply={"brand_name": "Plavix", "ingredient": "clopidogrel", "strength_mg": 75}))
    monkeypatch.setenv("GV_OCR", "vlm")
    caplog.set_level(logging.DEBUG, logger="genomevault.capture")
    assert capture.from_image(_plain_png(), "image/png") == [Drug(ingredient="clopidogrel", dose_mg=75)]
    assert _records(caplog) == []
