"""Agent C: knowledge-pack sync (D-027), allergy keys (A-011), no-data pairs (A queue 8)."""
import time

import pytest
from fastapi.testclient import TestClient

import app as app_module
from core import actions, merge
from core.contracts import Answer, Flag, LedgerEntry
from core.interfaces import load_profile

client = TestClient(app_module.app)
PROFILE = load_profile()
REAL_SYNC = app_module.sync_pack is not None


@pytest.fixture(autouse=True)
def fresh_sync():
    app_module._sync.update(running=False, result=None, finished=None)
    app_module._pack_seqs.clear()
    yield


def _wait_sync(c, timeout=10):
    deadline = time.time() + timeout
    while time.time() < deadline:
        s = c.get("/api/sync").json()
        if not s["running"]:
            return s
        time.sleep(0.05)
    raise AssertionError("sync did not finish")


# ---------- knowledge pack sync ----------

def test_sync_unavailable_without_b_router(monkeypatch):
    monkeypatch.setattr(app_module, "sync_pack", None)
    assert client.post("/api/sync").status_code == 409
    assert client.get("/api/sync").json()["available"] is False


def test_sync_refuses_while_offline(monkeypatch):
    monkeypatch.setattr(app_module, "sync_pack", lambda: {"sent": 0})
    monkeypatch.setattr(app_module, "_cloud", lambda: {"online": False, "demo": True, "forced_offline": True, "toggle": True})
    assert client.post("/api/sync").status_code == 409


def test_sync_runs_in_background_and_marks_pack_rows(monkeypatch):
    rows = []

    def fake_feed(since=0):
        return [r for r in rows if r.seq > since]

    def fake_sync():
        from datetime import datetime, timezone
        for i in range(3):
            rows.append(LedgerEntry(seq=len(rows) + 1, ts=datetime.now(timezone.utc), bucket_id=f"b0{i}",
                                    kind="cover", bytes_out=900))
        return {"sent": 3, "blocked": 0, "skipped": 0, "facts": 24, "offline": False}

    monkeypatch.setattr(app_module, "sync_pack", fake_sync)
    monkeypatch.setattr(app_module, "ledger_feed", fake_feed)
    monkeypatch.setattr(app_module, "_cloud", lambda: {"online": True, "demo": True, "forced_offline": False, "toggle": True})
    assert client.post("/api/sync").status_code == 200        # starts in the background (may already be done)
    s = _wait_sync(client)
    assert s["result"]["sent"] == 3 and s["finished"]
    assert app_module._pack_seqs == {1, 2, 3}
    entries = client.get("/api/ledger").json()["entries"]
    assert [e["pack"] for e in entries] == [True, True, True]


def test_sync_error_never_sticks(monkeypatch):
    def boom():
        raise RuntimeError("x")
    monkeypatch.setattr(app_module, "sync_pack", boom)
    monkeypatch.setattr(app_module, "_cloud", lambda: {"online": True, "demo": True, "forced_offline": False, "toggle": True})
    client.post("/api/sync")
    s = _wait_sync(client)
    assert s["running"] is False and s["result"] == {"error": "RuntimeError"}


@pytest.mark.skipif(not REAL_SYNC, reason="needs B's router (integrated build)")
def test_real_sync_fills_the_kb_and_rows_are_labeled_pack(tmp_path, monkeypatch):
    import json
    from core import decoys
    cache = tmp_path / "pack"; cache.mkdir()
    (cache / "all.json").write_text(json.dumps({k: "General guidance exists for this topic." for k in decoys.universe()}))
    monkeypatch.setenv("GV_CLOUD_CACHE", str(cache))
    client.post("/api/sync")
    s = _wait_sync(client)
    assert s["result"]["sent"] >= 1 and s["result"]["facts"] >= 8
    led = client.get("/api/ledger").json()
    pack = [e for e in led["entries"] if e["pack"]]
    assert pack and all(e["personal_fields_sent"] == 0 for e in pack)
    assert led["learned"]["fresh"] >= s["result"]["facts"]


# ---------- allergy keys and names with underscores ----------

AL = Flag(id="AL-001", key="allergy:penicillin|amoxicillin", severity="high", engine="allergy",
          evidence=["allergy on record: penicillin", "amoxicillin is a penicillin"])


def test_allergy_key_is_not_a_gene():
    drugs, genes, conds = merge._key_parts(AL.key)
    assert drugs == ["amoxicillin"] and genes == [] and conds == ["allergy:penicillin"]
    assert merge.describe(AL, PROFILE) == "AL-001 (high): amoxicillin and your penicillin allergy on record."


def test_allergy_question_names_the_allergen():
    q = actions.question_for(AL, PROFILE)
    assert q == "I'm allergic to penicillin. Does amoxicillin relate to that allergy?"


def test_allergy_word_does_not_make_flags_relevant():
    a = Answer(state="known", text="Allergy questions are best asked at the pharmacy.", sent_to_cloud=True)
    assert merge.relevant_flags(a, [AL]) == []


def test_underscored_ingredients_read_as_words():
    f = Flag(id="CR-9", key="penicillin_v|warfarin", severity="medium", engine="class_rule", evidence=[])
    assert "penicillin v" in actions.question_for(f, PROFILE)
    assert "penicillin v" in merge.describe(f, PROFILE)


# ---------- no-data pairs ----------

def test_check_carries_no_data_pairs(monkeypatch):
    monkeypatch.setattr(app_module, "no_data_keys",
                        lambda drug, profile: ["clopidogrel|pantoprazole"] if drug.ingredient == "pantoprazole" else [])
    d = client.post("/api/check", json={"text": "pantoprazole"}).json()
    assert d["no_data"] == ["clopidogrel|pantoprazole"]


def test_no_data_empty_without_a_rules_helper(monkeypatch):
    monkeypatch.setattr(app_module, "no_data_keys", None)
    assert client.post("/api/check", json={"text": "pantoprazole"}).json()["no_data"] == []
