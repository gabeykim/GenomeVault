"""Agent C: offline badge and "Wi-Fi off" switch (BRIEF C queue 7; F8, S6; cloud.status from D-020)."""
import pytest
from fastapi.testclient import TestClient

import app as app_module

client = TestClient(app_module.app)
HAS_SWITCH = app_module.cloud_set_offline is not None
REAL_ROUTER = app_module.MODES["router.route"] == "real"


def test_status_and_ledger_carry_cloud_state():
    for c in (client.get("/api/status").json()["cloud"], client.get("/api/ledger").json()["cloud"]):
        assert set(c) == {"online", "demo", "forced_offline", "toggle"}
        assert c["toggle"] is HAS_SWITCH


def test_switch_unavailable_without_b_cloud(monkeypatch):
    monkeypatch.setattr(app_module, "cloud_set_offline", None)
    r = client.post("/api/offline", json={"offline": True})
    assert r.status_code == 409


def test_switch_round_trip_with_a_fake_cloud(monkeypatch):
    state = {"forced": None}
    monkeypatch.setattr(app_module, "cloud_set_offline", lambda v: state.update(forced=v))
    monkeypatch.setattr(app_module, "cloud_status",
                        lambda: {"online": not state["forced"], "demo": True, "forced_offline": bool(state["forced"])})
    off = client.post("/api/offline", json={"offline": True}).json()
    assert off == {"online": False, "demo": True, "forced_offline": True, "toggle": True}
    on = client.post("/api/offline", json={"offline": False}).json()
    assert on["online"] is True and state["forced"] is None   # "off" returns control to GV_OFFLINE / network


def test_offline_body_is_validated():
    assert client.post("/api/offline", json={}).status_code == 422


def test_ui_has_the_switch():
    html = (app_module.UI_DIR / "index.html").read_text()
    assert 'id="net"' in html and 'role="switch"' in html and 'aria-label="Wi-Fi off"' in html


@pytest.mark.skipif(not (HAS_SWITCH and REAL_ROUTER), reason="needs B's cloud + router (integrated build)")
def test_s6_wifi_off_sends_nothing_but_local_checks_work():
    assert client.post("/api/offline", json={"offline": True}).json()["online"] is False
    before = client.get("/api/ledger").json()["totals"]["bytes_out"]
    a = client.post("/api/ask", json={"question": "What should I bring up with my cardiologist?"}).json()
    assert a["sent_to_cloud"] is False
    assert client.get("/api/ledger").json()["totals"]["bytes_out"] == before, "nothing leaves while offline"
    assert client.post("/api/check", json={"text": "clopidogrel"}).json()["flags"], "local checks still work"
    assert client.post("/api/offline", json={"offline": False}).json()["forced_offline"] is False
