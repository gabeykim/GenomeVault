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


# B-066: GV_TAIL never overrides a local answer, and never pairs one product's own ingredients ---------

from core.rules import check_all  # noqa: E402

_ALLERGY = Flag(id="A1", key="penicillin|amoxicillin", severity="high", engine="allergy",
                evidence=["penicillin allergy"], needs_cloud=True)
_X1 = Flag(id="X1", key="CYP2C19:poor_metabolizer|clopidogrel", severity="high", engine="gene_drug",
           evidence=["CYP2C19 poor metabolizer"], needs_cloud=True)
_CR = Flag(id="CR-001", key="aspirin|naproxen", severity="high", engine="class_rule",
           evidence=["NSAID + antiplatelet"], needs_cloud=False)


def _sent_texts() -> list[str]:
    return [t for e in ledger.feed(0) for t in ledger.outbound(e.seq)]


def test_combo_product_ingredients_are_not_a_pair():
    q = "Is ezetimibe-simvastatin 10-40 mg OK with my clopidogrel?"
    keys = router._question_keys(q)
    assert pair_key("ezetimibe", "simvastatin") not in keys
    assert pair_key("clopidogrel", "simvastatin") in keys and pair_key("clopidogrel", "ezetimibe") in keys
    assert pair_key("amoxicillin", "clavulanate") not in router._question_keys("Can I take amox-clav?")


def test_combo_question_sends_tail_pair_but_never_strength_or_own_pair(env):
    q = "Is ezetimibe-simvastatin 10-40 mg OK with my clopidogrel?"
    router.route(q, [])
    texts = [t.lower() for t in _sent_texts()]
    assert texts and all("10-40" not in t and q.lower() not in t for t in texts)
    own = topic_for_key(pair_key("ezetimibe", "simvastatin")).text.lower()
    assert own not in texts
    assert all(e.personal_fields_sent == 0 for e in ledger.feed(0))


def test_amox_clav_allergy_stays_local_with_tail():
    a = router.route("Can I take amox-clav?", [_ALLERGY])
    assert not a.sent_to_cloud and [e.kind for e in ledger.feed(0)] == ["local_only"]


def test_local_only_flags_with_a_lab_word_send_nothing_with_tail():
    local = [f for f in check_all(load_profile()) if not f.needs_cloud]
    assert local
    a = router.route("Is my simvastatin dose and my potassium ok?", local)
    assert not a.sent_to_cloud and a.state == "known" and a.text == router.LOCAL_TEXT


def test_covering_flag_with_a_lab_word_asks_no_tail_drug_lab_key():
    router.route("I am 58, CYP2C19 *2/*2, eGFR 48 - clopidogrel?", [_X1])
    assert [e for e in ledger.feed(0) if e.kind == "bucket"]          # X1's core bucket still goes
    assert not any(e.bucket_id.startswith("tail-") for e in ledger.feed(0))


def test_substitution_question_asks_no_tail_pair(monkeypatch):
    monkeypatch.delenv("DEMO")
    a = router.route("What about naproxen instead of ibuprofen?", [_CR])
    assert a.state == "known" and a.text == router.LOCAL_TEXT and not a.sent_to_cloud


def test_named_tail_pair_with_unrelated_covering_flag_is_still_asked(env):
    _cache_bucket(env, [PAIR])
    router.route("Can I take amoxicillin with warfarin?", [_ALLERGY])
    assert any(e.bucket_id.startswith("tail-") for e in ledger.feed(0) if e.kind == "bucket")
