"""D queue item 4: E2 learning curve, E3 latency/cost, E4 offline on the simulated P6 backend."""
from eval import latency_cost, learning_curve, offline
from eval.backends import SimBackend
from eval.universe import load_partition, load_queries


def test_learning_curve_falls():                     # E2, F6
    r = learning_curve.run(write=False)
    assert r["total_cloud_calls"] < 20
    assert r["cloud_calls_last5"] <= r["cloud_calls_first5"]
    assert r["repeat_q19_is_local"]                   # S6: related question answered from the KB, 0 bytes


def test_repeat_question_is_kb_hit():
    be, q = SimBackend(load_partition()), load_queries()[0]
    assert be.ask(q).cloud_calls >= 1 and be.ask(q).cloud_calls == 0


def test_pantoprazole_never_borrows_omeprazole():   # I4, S6
    be = SimBackend(load_partition(), offline=True)
    qs = {q["id"]: q for q in load_queries()}
    be.kb.add("clopidogrel|omeprazole")
    assert be.ask(qs["Q07"]).state == "no_data"


def test_hybrid_sends_no_personal_fields():         # E3, I3
    m = latency_cost.run(write=False, live=False)["modes"]
    assert m["hybrid"]["personal_fields_sent"] == 0 < m["cloud_only"]["personal_fields_sent"]
    assert m["hybrid"]["cloud_calls"] < m["cloud_only"]["cloud_calls"]
    assert m["local_only"]["cloud_calls"] == 0


def test_offline_warm_beats_cold_and_sends_nothing():   # E4, F8, I8
    r = offline.run(write=False, live=False)   # spec check on the P6 model; live runs are reported, not asserted
    assert r["warm_answered"] >= r["cold_answered"] > 0
    assert r["matches_offline_state_cold"] == r["n"]    # every cold answer is the state queries.json predicts
    assert r["cold_rows"]["Q15"]["state"] == "known"     # S6 offline ibuprofen still flagged


def test_live_backend_dedupes_flags_by_key_not_id():      # A-003: X5 is four flags sharing one id
    from types import SimpleNamespace
    from core.contracts import Answer, Flag
    from eval.backends import LiveBackend
    x5 = [Flag(id="X5", key=k, severity="high", engine="class_rule", evidence=["e"])
          for k in ("aspirin|ibuprofen", "clopidogrel|ibuprofen", "ibuprofen|lisinopril", "ibuprofen|egfr<60")]
    seen = {}
    be = object.__new__(LiveBackend)
    be.check = lambda drug, profile: x5 + x5[:1]               # one duplicate key on purpose
    be.check_all = None
    be.profile = SimpleNamespace(meds=[])
    be.router = SimpleNamespace(route=lambda text, flags: seen.setdefault("flags", flags) and Answer(state="known", text="t"))
    be.ledger = SimpleNamespace(feed=lambda since: [])
    be.seq = 0
    q = next(q for q in load_queries() if q["id"] == "Q15")
    be.ask(q)
    assert sorted(f.key for f in seen["flags"]) == sorted(f.key for f in x5)


def test_full_pack_sync_answers_most_offline():          # B-010 model
    r = offline.run(write=False, live=False)
    assert r["synced_answered"] >= r["warm_answered"]


def test_gate_and_slide_numbers_from_one_run():          # G4
    from eval import gate, redteam, run_all, wording
    rt, lc = redteam.run(trials=200, seed=3, write=False), learning_curve.run(write=False)
    lat, off, wd = latency_cost.run(write=False, live=False), offline.run(write=False, live=False), wording.run(write=False)
    rows = gate.check(rt, lc, lat, off, wd)
    assert {r["status"] for r in rows} <= {"PASS", "WARN", "FAIL"}
    assert not [r for r in rows if r["status"] == "FAIL"], [r for r in rows if r["status"] == "FAIL"]
    md = run_all.write_numbers(rt, lc, lat, off, wd)
    assert "| Fixed buckets: repeat-ask attacker |" in md and "(E1c)" in md


def test_unbacked_known_answer_fails_the_gate():          # I4: a missing key is no_data, never 'checked, nothing found'
    from eval import gate, redteam, wording
    from eval.backends import Result
    assert Result("Q16", "known").unbacked                       # no flag, no fact
    assert not Result("Q01", "known", local_flags=1).unbacked
    assert Result("Q01", "no_data", local_flags=1).effective_state == "known"
    off = offline.run(write=False, live=False)
    assert off["unbacked_known"] == []                           # the P6 model never does this
    off["unbacked_known"] = ["Q16"]
    rows = gate.check(redteam.run(trials=100, seed=2, write=False), learning_curve.run(write=False),
                      latency_cost.run(write=False, live=False), off, wording.run(write=False))
    assert next(r for r in rows if r["id"] == "I4")["status"] == "FAIL"


def test_curated_note_answers_q08_offline():               # A-008: EX-001 is a curated, exact-key local fact
    qs = {q["id"]: q for q in load_queries()}
    be = SimBackend(load_partition(), offline=True)
    r = be.ask(qs["Q08"])
    assert r.effective_state == "known" and not r.unbacked and r.cloud_calls == 0
