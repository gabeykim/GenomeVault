"""G2 end to end against A's real code (merged at G1, D-022): graph.load_profile -> rules.check_all ->
router.route -> ledger. No mocks for the profile or the flags; only the cloud is replayed (DEMO=1, I8)
from a temporary cache that answers every key of the partition."""
import json

import pytest

from core import cloud, kb, ledger, router, rules
from core.contracts import Drug
from core.decoys import bucket_for, load_buckets
from core.graph import load_profile
from core.validator import _key_drugs, check_outbound, check_output, wording_problems


@pytest.fixture(autouse=True)
def demo_cache(tmp_path, monkeypatch):
    for v in ("ANTHROPIC_API_KEY", "GV_LEDGER_PATH", "GV_KB_PATH", "GV_OFFLINE", "GV_GRAPH_DB"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setattr(cloud, "_forced", None)
    for b in load_buckets():
        (tmp_path / f"{b.id}.json").write_text(
            json.dumps({k: f"General fact about {k}." for k in b.keys}))
    monkeypatch.setenv("DEMO", "1")
    monkeypatch.setenv("GV_CLOUD_CACHE", str(tmp_path))
    ledger.reset()
    kb.reset()
    yield
    ledger.reset()
    kb.reset()


@pytest.fixture
def alex():
    p = load_profile()
    return p, rules.check_all(p)


def test_real_flags_that_need_cloud_all_have_a_bucket(alex):
    _, flags = alex
    ids = {f.id for f in flags}
    assert {"X1", "X2", "X3", "X4"} <= ids                       # G1 (D-022)
    cloud_keys = [f.key for f in flags if f.needs_cloud and f.engine != "allergy"]
    assert cloud_keys, "Alex's discharge meds must need at least one cloud fact (S4)"
    assert all(bucket_for(k) is not None for k in cloud_keys)


def test_one_question_end_to_end_with_real_rules_and_live_ledger(alex):
    profile, flags = alex
    a = router.route("Is anything on my discharge list a problem with my genetics?", flags)
    assert a.state == "known" and a.sent_to_cloud
    wanted = {f.key for f in flags if f.needs_cloud and f.engine != "allergy"}
    assert {f.key for f in a.facts} == wanted                    # every cloud-needing flag answered
    assert check_output(a.text, a.facts)                         # I4
    assert not wording_problems(a.text)                          # I7

    entries = [e for e in ledger.feed(0) if e.kind == "bucket"]
    assert {e.bucket_id for e in entries} == {bucket_for(k).id for k in wanted}
    genotype_strings = [g for g in profile.genotypes.values() if g]
    for e in entries:
        texts = ledger.outbound(e.seq)
        assert len(texts) == 8 and len(set(texts)) == 8         # whole bucket, 8 distinct topics (I5)
        assert e.bytes_out > 0 and e.personal_fields_sent == 0
        bucket = next(b for b in load_buckets() if b.id == e.bucket_id)
        allow = set().union(*(_key_drugs(k) for k in bucket.keys))
        assert check_outbound(texts, profile, allow=allow)      # I3 with the real profile
        for t in texts:
            assert not any(g in t for g in genotype_strings)


def test_repeat_question_is_kb_hit_zero_bytes(alex):
    _, flags = alex
    router.route("first time", flags)
    n = len(ledger.feed(0))
    b = router.route("second time", flags)
    assert b.state == "known" and not b.sent_to_cloud
    later = ledger.feed(0)[n:]
    assert [e.kind for e in later] == ["kb_hit"] and all(e.bytes_out == 0 for e in later)


def test_local_only_flags_send_nothing(alex):
    _, flags = alex
    local = [f for f in flags if not f.needs_cloud]
    assert local                                                 # X3, X4 are answered on-device
    a = router.route("Is my simvastatin dose and my potassium ok?", local)
    assert not a.sent_to_cloud
    assert [e.kind for e in ledger.feed(0)] == ["local_only"]


def test_offline_ibuprofen_x5_sends_nothing(alex):
    # S6: offline, a new NSAID is still flagged locally (X5) and nothing leaves (F8).
    profile, _ = alex
    x5 = rules.check(Drug(ingredient="ibuprofen", dose_mg=400), profile)
    assert any(f.id == "X5" for f in x5)
    cloud.set_offline(True)
    try:
        a = router.route("Can I take ibuprofen for my back?", x5)
    finally:
        cloud.set_offline(None)
    assert not a.sent_to_cloud
    assert all(e.bytes_out == 0 for e in ledger.feed(0))
