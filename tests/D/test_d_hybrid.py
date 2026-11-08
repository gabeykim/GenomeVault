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
    m = latency_cost.run(write=False)["modes"]
    assert m["hybrid"]["personal_fields_sent"] == 0 < m["cloud_only"]["personal_fields_sent"]
    assert m["hybrid"]["cloud_calls"] < m["cloud_only"]["cloud_calls"]
    assert m["local_only"]["cloud_calls"] == 0


def test_offline_warm_beats_cold_and_sends_nothing():   # E4, F8, I8
    r = offline.run(write=False)
    assert r["warm_answered"] >= r["cold_answered"] > 0
    assert r["matches_offline_state_cold"] == r["n"]    # every cold answer is the state queries.json predicts
    assert r["cold_rows"]["Q15"]["state"] == "known"     # S6 offline ibuprofen still flagged
