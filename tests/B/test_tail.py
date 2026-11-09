"""D-040 part 2: long-tail partition (GV_TAIL) and the consented single send (I3, I4, I5, P6)."""
import json

import pytest

from core import kb, ledger, router
from core.contracts import Flag, pair_key
from core.decoys import (TAIL_VERSION, bucket_for, load_aliases, load_buckets, tail_bucket_for,
                         tail_member, universe)
from core.generalize import topic_for_key
from core.interfaces import load_profile
from core.validator import check_outbound

PAIR = pair_key("amoxicillin", "warfarin")


@pytest.fixture(autouse=True)
def env(tmp_path, monkeypatch):
    for v in ("ANTHROPIC_API_KEY", "GV_LEDGER_PATH", "GV_KB_PATH", "GV_OFFLINE", "GV_DEMO_LIVE_FALLBACK"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setattr(router.cloud, "_forced", None)
    monkeypatch.setenv("DEMO", "1")
    monkeypatch.setenv("GV_TAIL", "1")
    monkeypatch.setenv("GV_CLOUD_CACHE", str(tmp_path))
    ledger.reset()
    kb.reset()
    yield tmp_path
    ledger.reset()
    kb.reset()


def _cache_bucket(tmp_path, keys):
    (tmp_path / "tail.json").write_text(json.dumps({k: f"General fact about {k}." for k in keys}))


def test_tail_file_is_a_fixed_partition_disjoint_from_core():
    tail = load_buckets(TAIL_VERSION)
    keys = [k for b in tail for k in b.keys]
    assert len(keys) == len(set(keys)) and all(len(b.keys) == 8 for b in tail)
    assert not set(keys) & (set(universe()) | set(load_aliases()))
    assert all(b.id.startswith("tail-") and b.version == TAIL_VERSION for b in tail)
    for k in keys:
        topic_for_key(k)                                  # every key generalizes
    assert PAIR in keys


def test_tail_is_built_reproducibly():
    import importlib.util
    import pathlib
    p = pathlib.Path(__file__).resolve().parents[2] / "data" / "buckets" / "build_tail_v1.py"
    spec = importlib.util.spec_from_file_location("build_tail_v1", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    committed = json.loads((p.parent / "tail-v1.json").read_text())
    assert mod.build()["buckets"] == committed["buckets"]


def test_core_first_and_band_variants_map_to_one_tail_key():
    core_key = universe()[0]
    assert tail_member(core_key) is None
    m = tail_member("amoxicillin|egfr<30")
    assert m == tail_member("amoxicillin|egfr<60") and m is not None
    assert tail_bucket_for("madeupdrug|warfarin") is None


def test_tail_pair_sent_as_whole_bucket(env):
    b = tail_bucket_for(PAIR)
    _cache_bucket(env, b.keys)
    a = router.route("Can I take amoxicillin with warfarin?", [])
    assert a.state == "known" and a.sent_to_cloud
    assert a.facts[0].key == PAIR
    [e] = ledger.feed(0)
    assert e.kind == "bucket" and e.bucket_id == b.id and e.bucket_id.startswith("tail")
    texts = ledger.outbound(e.seq)
    assert len(texts) == 8 and "Can I take" not in " ".join(texts)
    assert check_outbound(texts, load_profile(), allow=[d for k in b.keys for d in k.split("|")])
    assert all(kb.get(k) is not None for k in b.keys)  # all 8 answers stored
    again = router.route("amoxicillin and warfarin?", [])
    assert again.state == "known" and not again.sent_to_cloud


def test_tail_off_is_unchanged(env, monkeypatch):
    monkeypatch.delenv("GV_TAIL")
    _cache_bucket(env, tail_bucket_for(PAIR).keys)
    a = router.route("Can I take amoxicillin with warfarin?", [])
    assert a.state == "no_data" and not a.sent_to_cloud
    assert router.single_candidates("amoxicillin with warfarin?", []) == []


def test_tail_offline_sends_nothing(env, monkeypatch):
    monkeypatch.setenv("GV_OFFLINE", "1")
    a = router.route("Can I take amoxicillin with warfarin?", [])
    assert a.state == "no_data" and a.text == router.OFFLINE_TEXT and not a.sent_to_cloud
    assert ledger.feed(0) == []


def test_tail_cache_miss_is_no_data(env):
    a = router.route("Can I take amoxicillin with warfarin?", [])
    assert a.state == "no_data" and a.facts == []


def test_tail_lab_band_variant_gets_member_answer(env):
    m = tail_member("amoxicillin|egfr<30")
    _cache_bucket(env, tail_bucket_for(m).keys)
    flag = Flag(id="T", key="amoxicillin|egfr<30", severity="medium", engine="drug_lab",
                evidence=[], needs_cloud=True)
    a = router.route("Is my amoxicillin ok for my kidneys?", [flag])
    assert a.state == "known" and [f.key for f in a.facts] == ["amoxicillin|egfr<30"]
    [e] = ledger.feed(0)
    assert e.bucket_id == tail_bucket_for(m).id


def test_single_refuses_partition_keys():
    with pytest.raises(ValueError):
        router.send_single(PAIR)
    with pytest.raises(ValueError):
        router.send_single(universe()[0])


def test_single_send_marked_not_hidden(env):
    key = pair_key("madeupdrug", "warfarin")
    assert bucket_for(key) is None and tail_member(key) is None
    (env / "single.json").write_text(json.dumps({key: "A general fact."}))
    a = router.send_single(key)
    assert a.state == "known" and a.sent_to_cloud
    [e] = ledger.feed(0)
    assert e.kind == "bucket" and e.bucket_id == "single"
    assert ledger.outbound(e.seq) == [topic_for_key(key).text]


def test_single_send_offline_and_flag_off(env, monkeypatch):
    key = pair_key("madeupdrug", "warfarin")
    monkeypatch.setenv("GV_OFFLINE", "1")
    assert router.send_single(key).state == "no_data"
    monkeypatch.delenv("GV_OFFLINE")
    monkeypatch.delenv("GV_TAIL")
    assert router.send_single(key).state == "no_data"
    assert ledger.feed(0) == []


def test_single_send_leak_blocks(env, monkeypatch):
    real = router.topic_for_key
    monkeypatch.setattr(router, "topic_for_key",
                        lambda k: real(k).model_copy(update={"text": real(k).text + " eGFR 48"}))
    a = router.send_single(pair_key("madeupdrug", "warfarin"))
    assert a.state == "no_data" and not a.sent_to_cloud
    [e] = ledger.feed(0)
    assert e.kind == "blocked" and e.bytes_out == 0


def test_single_candidates_empty_for_tail_pairs():
    assert router.single_candidates("Can I take amoxicillin with warfarin?", []) == []


def test_cover_can_draw_tail(env, monkeypatch):
    monkeypatch.setattr(router._cover_rng, "random", lambda: 0.1)
    e = router.send_cover()
    assert e is not None and e.kind == "cover" and e.bucket_id.startswith("tail-")
