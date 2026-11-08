"""Agent C: phone page (BRIEF C queue 5; F2, S2, S6; capture.from_image per D-020).

The phone reaches the laptop over the local network, so any request not from this machine must be paired.
"""
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app as app_module
from core.contracts import Drug

ROOT = Path(__file__).resolve().parents[2]
PHONE = ROOT / "phone"
local = TestClient(app_module.app)                                  # host "testclient" = this laptop
remote = TestClient(app_module.app, client=("192.168.1.50", 50000))  # a phone on the Wi-Fi
REAL_CAPTURE = app_module.MODES.get("capture.from_image") == "real"


@pytest.fixture(autouse=True)
def fresh_phone_state():
    app_module._captures.clear()
    app_module._fails.update(n=0, until=0.0)
    remote.cookies.clear()
    yield


# ---------- pairing gate ----------

def test_remote_requests_need_pairing():
    assert remote.get("/api/profile").status_code == 401
    assert remote.get("/api/flags").status_code == 401
    assert remote.post("/api/capture", content=b"x", headers={"Content-Type": "image/png"}).status_code == 401
    assert remote.get("/").status_code == 401


def test_phone_page_and_assets_open_without_pairing():
    assert remote.get("/phone").status_code == 200
    assert remote.get("/phone-assets/phone.js").status_code == 200
    assert remote.get("/phone-assets/samples/clopidogrel.png").status_code == 200


def test_wrong_code_then_right_code():
    assert remote.post("/api/phone/pair", json={"code": "nope"}).status_code == 403
    r = remote.post("/api/phone/pair", json={"code": app_module.PHONE_CODE.lower()})   # case-insensitive
    assert r.status_code == 200
    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=strict" in cookie
    assert remote.get("/api/profile").status_code == 200


def test_lockout_after_ten_misses():
    for _ in range(10):
        remote.post("/api/phone/pair", json={"code": "wrong1"})
    assert remote.post("/api/phone/pair", json={"code": app_module.PHONE_CODE}).status_code == 423


def test_pairing_code_shown_only_on_the_laptop():
    assert local.get("/api/phone").json()["code"] == app_module.PHONE_CODE
    remote.post("/api/phone/pair", json={"code": app_module.PHONE_CODE})
    assert remote.get("/api/phone").status_code == 403          # even a paired phone can't read the code


def test_laptop_needs_no_pairing():
    assert local.get("/api/profile").status_code == 200


# ---------- capture ----------

def test_capture_only_reads_then_confirm_runs_rules(monkeypatch):  # D-029
    monkeypatch.setattr(app_module, "from_image",
                        lambda data, mime: [Drug(ingredient="clopidogrel", dose_mg=75)] if data else [])
    d = local.post("/api/capture", content=b"\x89PNGfake", headers={"Content-Type": "image/png"}).json()
    assert d == {"read": True, "drugs": [{"ingredient": "clopidogrel", "dose_mg": 75.0}]}   # no rules yet
    assert local.get("/api/captures").json()["captures"] == []                               # nothing shown yet
    c = local.post("/api/capture/confirm", json={"drugs": d["drugs"], "source": "sample"}).json()
    assert {"X1", "X2"} <= {f["id"] for f in c["flags"]}
    caps = local.get("/api/captures").json()["captures"]
    assert caps[-1]["source"] == "sample" and caps[-1]["drugs"][0]["ingredient"] == "clopidogrel"


def test_confirm_validates_input():
    assert local.post("/api/capture/confirm", json={"drugs": []}).status_code == 422
    assert local.post("/api/capture/confirm", json={"drugs": [{"ingredient": "x"}], "source": "email"}).status_code == 422
    assert remote.post("/api/capture/confirm", json={"drugs": [{"ingredient": "x"}]}).status_code == 401


def test_unreadable_photo_is_honest_and_not_recorded(monkeypatch):
    monkeypatch.setattr(app_module, "from_image", lambda data, mime: [])
    d = local.post("/api/capture", content=b"\xff\xd8\xffjpeg", headers={"Content-Type": "image/jpeg"}).json()
    assert d == {"read": False, "drugs": []}
    assert local.get("/api/captures").json()["captures"] == []


def test_non_image_upload_is_not_read(monkeypatch):
    called = []
    monkeypatch.setattr(app_module, "from_image", lambda data, mime: called.append(mime) or [])
    local.post("/api/capture", content=b"hello", headers={"Content-Type": "text/plain"})
    assert called == []


def test_oversized_photo_rejected(monkeypatch):
    monkeypatch.setattr(app_module, "MAX_UPLOAD", 10)
    assert local.post("/api/capture", content=b"x" * 11, headers={"Content-Type": "image/png"}).status_code == 413


def test_capture_sends_nothing():
    before = local.get("/api/ledger").json()["totals"]["bytes_out"]
    local.post("/api/capture", content=(PHONE / "samples" / "clopidogrel.png").read_bytes(),
               headers={"Content-Type": "image/png"})
    assert local.get("/api/ledger").json()["totals"]["bytes_out"] == before


def test_typed_on_phone_shows_on_laptop():
    local.post("/api/check", json={"text": "clopidogrel", "via": "phone"})
    assert local.get("/api/captures").json()["captures"][-1]["source"] == "typed"
    local.post("/api/check", json={"text": "clopidogrel"})        # typed on the laptop: not a phone capture
    assert len(local.get("/api/captures").json()["captures"]) == 1
    assert local.post("/api/check", json={"text": "x", "via": "email"}).status_code == 422


@pytest.mark.skipif(not REAL_CAPTURE, reason="needs A's capture.py (integrated build)")
@pytest.mark.parametrize("sample,ingredient,flag_ids", [("clopidogrel.png", "clopidogrel", {"X1", "X2"}),
                                                        ("ibuprofen.png", "ibuprofen", {"X5"})])
def test_sample_labels_read_with_a_real_reader(sample, ingredient, flag_ids):
    d = local.post("/api/capture", content=(PHONE / "samples" / sample).read_bytes(),
                   headers={"Content-Type": "image/png"}).json()
    assert d["drugs"][0]["ingredient"] == ingredient
    c = local.post("/api/capture/confirm", json={"drugs": d["drugs"], "source": "sample"}).json()
    assert flag_ids <= {f["id"] for f in c["flags"]}


# ---------- the page itself ----------

def _phone_text():
    return "\n".join(p.read_text() for p in PHONE.rglob("*") if p.suffix in {".html", ".css", ".js"})


def test_phone_page_never_says_safe():  # I7
    # CSS env(safe-area-inset-*) keeps content clear of the notch; it is not wording.
    assert not re.search(r"\bsafe\b(?!-area-inset)", _phone_text(), re.I)


def test_phone_page_loads_no_external_assets():  # I8
    assert not re.search(r"(src|href)\s*=\s*[\"']?(https?:)?//", _phone_text())
    assert "@import" not in _phone_text()


def test_no_voice_input():  # browser speech recognition sends audio to a cloud service
    assert "SpeechRecognition" not in _phone_text()
