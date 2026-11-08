import threading

import pytest

from core import ledger
from core.contracts import LedgerEntry


@pytest.fixture(autouse=True)
def fresh(monkeypatch):
    monkeypatch.delenv("GV_LEDGER_PATH", raising=False)
    ledger.reset()
    yield
    ledger.reset()


def test_seq_starts_at_one_and_increases():
    a = ledger.record("local_only")
    b = ledger.record("kb_hit")
    c = ledger.record("bucket", "b05", ["q1", "q2"])
    assert [a.seq, b.seq, c.seq] == [1, 2, 3]
    assert all(isinstance(e, LedgerEntry) for e in (a, b, c))


def test_bytes_out_is_utf8_size_of_texts():
    e = ledger.record("bucket", "b01", ["abc", "é"])
    assert e.bytes_out == 3 + 2
    assert ledger.outbound(e.seq) == ["abc", "é"]


def test_zero_byte_kinds():
    for kind in ("local_only", "kb_hit", "blocked"):
        e = ledger.record(kind)
        assert e.bytes_out == 0
        assert ledger.outbound(e.seq) == []


def test_zero_byte_kinds_reject_texts():
    with pytest.raises(ValueError):
        ledger.record("kb_hit", texts=["leak"])


def test_sending_kinds_need_bucket_and_texts():
    with pytest.raises(ValueError):
        ledger.record("bucket", None, ["q"])
    with pytest.raises(ValueError):
        ledger.record("cover", "b02", [])


def test_personal_fields_never_recorded_as_sent():
    with pytest.raises(ValueError):
        ledger.record("bucket", "b01", ["q"], personal_fields_sent=1)
    assert ledger.feed(0) == []


def test_unknown_kind():
    with pytest.raises(ValueError):
        ledger.record("upload")


def test_feed_since():
    for _ in range(5):
        ledger.record("local_only")
    assert [e.seq for e in ledger.feed(0)] == [1, 2, 3, 4, 5]
    assert [e.seq for e in ledger.feed(3)] == [4, 5]
    assert ledger.feed(5) == []
    assert ledger.feed(99) == []


def test_feed_returns_copy():
    ledger.record("local_only")
    ledger.feed(0).clear()
    assert len(ledger.feed(0)) == 1


def test_totals():
    ledger.record("local_only")
    ledger.record("bucket", "b05", ["abcd"] * 8)
    ledger.record("cover", "b09", ["xy"] * 8)
    t = ledger.totals()
    assert t["entries"] == 3
    assert t["bytes_out"] == 32 + 16
    assert t["personal_fields_sent"] == 0
    assert t["by_kind"]["bucket"] == 1 and t["by_kind"]["cover"] == 1
    assert t["by_kind"]["local_only"] == 1 and t["by_kind"]["kb_hit"] == 0


def test_concurrent_records_get_unique_seq():
    def go():
        for _ in range(50):
            ledger.record("local_only")
    ts = [threading.Thread(target=go) for _ in range(4)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    seqs = [e.seq for e in ledger.feed(0)]
    assert seqs == list(range(1, 201))


def test_jsonl_persistence(tmp_path, monkeypatch):
    path = tmp_path / "ledger.jsonl"
    monkeypatch.setenv("GV_LEDGER_PATH", str(path))
    ledger.reset()
    ledger.record("bucket", "b05", ["q1", "q2"])
    ledger.record("kb_hit")
    # simulate a restart: drop in-memory state, reload from file
    ledger._entries.clear()
    ledger._texts.clear()
    ledger._loaded = False
    assert [e.seq for e in ledger.feed(0)] == [1, 2]
    assert ledger.outbound(1) == ["q1", "q2"]
    assert ledger.record("local_only").seq == 3
    ledger.reset()
    assert not path.exists()
