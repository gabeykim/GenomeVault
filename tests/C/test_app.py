"""Agent C: app.py + two-pane UI (BRIEF C queue 1), on the real modules since G2 (D-032)."""
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app as app_module

client = TestClient(app_module.app)
UI = Path(app_module.UI_DIR)


def test_index_serves_two_pane_ui_with_disclaimer():
    r = client.get("/")
    assert r.status_code == 200
    html = r.text
    assert "Demo, not medical advice" in html
    assert 'id="profile"' in html and 'id="flags"' in html and 'id="chat"' in html
    assert 'id="ledger"' in html
    assert "Stays on this device" in html


def test_static_assets_served():
    assert client.get("/ui/app.js").status_code == 200
    assert client.get("/ui/style.css").status_code == 200


def test_status_reports_all_modules_real():
    s = client.get("/api/status").json()
    assert set(s["modules"]) >= {"rules.check", "router.route", "ledger.feed", "merge.personalize"}
    assert set(s["modules"].values()) == {"real"}, "no stand-ins after G2 (D-014, D-032)"


def test_app_has_no_stand_ins():
    import app
    for name in ("_MockLedger", "_mock_ledger", "_mock_to_ingredients", "_resolve", "LEDGER_IS_MOCK", "_note"):
        assert not hasattr(app, name), name
    assert app.route.__module__ == "core.router" and app.ledger_feed.__module__ == "core.ledger"


def test_profile_comes_from_device():
    p = client.get("/api/profile").json()
    assert p["phenotypes"]["CYP2C19"] == "poor_metabolizer"
    assert any(m["ingredient"] == "clopidogrel" for m in p["meds"])


def test_flags_for_discharge_meds_are_x1_to_x4():
    data = client.get("/api/flags").json()
    assert [f["id"] for f in data["flags"]] == ["X1", "X2", "X3", "X4"]


def test_local_check_sends_nothing():
    before = client.get("/api/ledger").json()["totals"]["bytes_out"]
    data = client.post("/api/check", json={"text": "Clopidogrel"}).json()
    assert {"X1", "X2"} <= {f["id"] for f in data["flags"]}
    after = client.get("/api/ledger").json()["totals"]["bytes_out"]
    assert after == before


def test_check_rejects_empty_input():
    assert client.post("/api/check", json={"text": ""}).status_code == 422


# B's router is the only ledger writer (D-032).


def test_ask_returns_a_state():
    a = client.post("/api/ask", json={"question": "What should I bring up with my cardiologist?"}).json()
    assert a["state"] in {"known", "none_listed", "no_data"}
    assert a["text"]


def test_every_ask_leaves_a_ledger_entry():
    since = client.get("/api/ledger").json()["totals"]["count"]
    client.post("/api/ask", json={"question": "What should I bring up with my cardiologist?"})
    assert client.get(f"/api/ledger?since={since}").json()["entries"], "every ask leaves a ledger entry"


def test_app_writes_no_ledger_entries():
    before = client.get("/api/ledger").json()["totals"]["count"]
    client.post("/api/check", json={"text": "aspirin"})   # local only: the router is not involved
    assert client.get("/api/ledger").json()["totals"]["count"] == before


def test_ledger_never_reports_personal_fields():
    client.post("/api/ask", json={"question": "Anything about my statin?"})
    led = client.get("/api/ledger").json()
    assert led["totals"]["personal_fields_sent"] == 0
    assert all(e["personal_fields_sent"] == 0 for e in led["entries"])


def test_ledger_since_filters():
    client.post("/api/ask", json={"question": "Anything about aspirin?"})
    total = client.get("/api/ledger").json()["totals"]["count"]
    assert total >= 1
    assert client.get(f"/api/ledger?since={total}").json()["entries"] == []
    assert len(client.get(f"/api/ledger?since={total - 1}").json()["entries"]) == 1


def test_cloud_facts_carry_verify_label():
    from datetime import date
    from core.contracts import Fact
    f = Fact(key="k", text="t", tier="cloud", source="cloud", fetched=date.today(), expires=date.today())
    assert app_module.tier_label(f) == "AI-summarized, verify"


def _ui_text():
    return "\n".join(p.read_text() for p in UI.rglob("*") if p.is_file())


def test_ui_never_says_safe():  # I7
    assert not re.search(r"\bsafe\b", _ui_text(), re.IGNORECASE)


def test_ui_loads_no_external_assets():  # I8: demo must work with no network
    assert not re.search(r"(src|href)\s*=\s*[\"']?(https?:)?//", _ui_text())
    assert "@import" not in _ui_text()
