"""Agent C, D-040 part 4: adaptive questions in the UI API (assumed names, "Did you mean", consent).

A's normalize.suggest and B's single_candidates / send_single are stood in here with the shapes C
proposed (to-A / to-B 1705), so these tests pin C's behavior whatever lands first. With the flags off
(or the functions missing), every response is exactly today's.
"""
from datetime import date

import pytest
from fastapi.testclient import TestClient

import app as app_module
from core.contracts import Answer, Drug, Fact, Flag

client = TestClient(app_module.app)
TYPO = "clopidogrl"


def fake_suggest(kind):
    def suggest(text):
        if TYPO not in text.lower():
            return []
        if kind == "assumed":
            return [{"term": TYPO, "assumed": "clopidogrel", "choices": ["clopidogrel"]}]
        return [{"term": TYPO, "assumed": None, "choices": ["clopidogrel", "clonidine", "clozapine"]}]
    return suggest


@pytest.fixture
def fuzzy(monkeypatch):
    def on(kind="assumed"):
        monkeypatch.setenv("GV_FUZZY", "1")
        monkeypatch.setattr(app_module, "suggest_names", fake_suggest(kind))
    return on


# ---------- flags off: today's UI ----------

def test_flag_off_leaves_check_and_ask_unchanged(monkeypatch):
    monkeypatch.delenv("GV_FUZZY", raising=False)
    monkeypatch.setattr(app_module, "suggest_names", fake_suggest("assumed"))
    c = client.post("/api/check", json={"text": TYPO}).json()
    assert "assumed" not in c and "held" not in c and c["drugs"] == []
    a = client.post("/api/ask", json={"question": f"Can I take {TYPO}?"}).json()
    assert "assumed" not in a and "consent" not in a and a["state"] != "held"


def test_missing_functions_are_off(monkeypatch):
    monkeypatch.setenv("GV_FUZZY", "1")
    monkeypatch.setattr(app_module, "suggest_names", None)
    monkeypatch.setattr(app_module, "single_candidates", None)
    assert client.get("/api/status").json()["adaptive"] == {"fuzzy": False, "single": False}
    assert "assumed" not in client.post("/api/check", json={"text": TYPO}).json()


# ---------- assumed name ----------

def test_check_assumes_a_clear_typo_and_says_so(fuzzy):
    fuzzy("assumed")
    c = client.post("/api/check", json={"text": TYPO}).json()
    assert c["assumed"] == [{"term": TYPO, "name": "clopidogrel"}]
    assert [d["ingredient"] for d in c["drugs"]] == ["clopidogrel"]
    assert c["input"] == TYPO                                   # the UI still shows what was typed


def test_not_what_i_meant_uses_the_text_as_typed(fuzzy):
    fuzzy("assumed")
    c = client.post("/api/check", json={"text": TYPO, "no_assume": True}).json()
    assert "assumed" not in c and c["drugs"] == []


def test_ask_routes_the_corrected_question(fuzzy, monkeypatch):
    fuzzy("assumed")
    seen = {}
    monkeypatch.setattr(app_module, "route", lambda q, flags: seen.setdefault("q", q) and Answer(state="known", text="Local."))
    a = client.post("/api/ask", json={"question": f"Is {TYPO} ok with my aspirin?"}).json()
    assert seen["q"] == "Is clopidogrel ok with my aspirin?"
    assert a["assumed"][0]["name"] == "clopidogrel"


# ---------- "Did you mean": hold until picked ----------

def test_choices_hold_the_check(fuzzy, monkeypatch):
    fuzzy("choices")
    calls = []
    monkeypatch.setattr(app_module, "check", lambda d, p: calls.append(d) or [])
    c = client.post("/api/check", json={"text": TYPO}).json()
    assert c["held"] is True and c["choices"][0]["choices"] == ["clopidogrel", "clonidine", "clozapine"]
    assert c["drugs"] == [] and calls == []


def test_choices_hold_the_question_and_send_nothing(fuzzy, monkeypatch):
    fuzzy("choices")
    called = []
    monkeypatch.setattr(app_module, "route", lambda q, f: called.append(q) or Answer(state="known", text="x"))
    before = client.get("/api/ledger").json()["totals"]["bytes_out"]
    a = client.post("/api/ask", json={"question": f"Can I take {TYPO}?"}).json()
    assert a["state"] == "held" and a["sent_to_cloud"] is False and called == []
    assert client.get("/api/ledger").json()["totals"]["bytes_out"] == before


# ---------- consent for a term no group covers ----------

@pytest.fixture
def single(monkeypatch):
    sent = []
    monkeypatch.setattr(app_module, "single_candidates", lambda q, flags: ["obscurol|clopidogrel"] if "obscurol" in q else [])
    monkeypatch.setattr(app_module, "send_single", lambda key: sent.append(key) or Answer(
        state="known", text="General answer.", sent_to_cloud=True,
        facts=[Fact(key=key, text="General answer.", tier="cloud", source="cloud:test",
                    fetched=date(2026, 11, 8), expires=date(2026, 12, 8))]))
    monkeypatch.setattr(app_module, "route", lambda q, f: Answer(state="no_data", text="No data."))
    monkeypatch.setattr(app_module, "cloud_status", lambda: {"online": True, "demo": True})
    return sent


def test_no_data_with_an_uncovered_term_asks_first(single):
    a = client.post("/api/ask", json={"question": "Can I take obscurol?"}).json()
    assert a["consent"] == {"question": "Can I take obscurol?", "keys": ["obscurol|clopidogrel"]}
    assert single == [], "nothing is sent before the user says yes"


def test_yes_sends_only_what_the_router_offered(single):
    q = "Can I take obscurol?"
    r = client.post("/api/ask/single", json={"question": q, "key": "obscurol|clopidogrel"})
    assert r.status_code == 200 and r.json()["single"] is True and single == ["obscurol|clopidogrel"]
    bad = client.post("/api/ask/single", json={"question": q, "key": "aspirin|warfarin"})
    assert bad.status_code == 400 and single == ["obscurol|clopidogrel"]


def test_offline_never_offers_or_sends(single, monkeypatch):
    monkeypatch.setattr(app_module, "cloud_status", lambda: {"online": False, "demo": True})
    a = client.post("/api/ask", json={"question": "Can I take obscurol?"}).json()
    assert "consent" not in a
    r = client.post("/api/ask/single", json={"question": "Can I take obscurol?", "key": "obscurol|clopidogrel"})
    assert r.status_code == 409 and single == []


def test_known_answers_never_offer_a_single_send(single, monkeypatch):
    monkeypatch.setattr(app_module, "route", lambda q, f: Answer(state="known", text="Local."))
    assert "consent" not in client.post("/api/ask", json={"question": "Can I take obscurol?"}).json()


# ---------- the page ----------

def test_ui_has_the_d040_wording_and_ledger_labels():
    js = (app_module.UI_DIR / "app.js").read_text()
    for s in ("I'm assuming you mean", "Not what I meant", "Did you mean",
              "This question can't be hidden in a group of 8.", "Send it on its own",
              "Single question sent, not hidden", "Tail group of 8 sent"):
        assert s in js, s
