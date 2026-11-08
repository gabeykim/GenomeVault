"""Pack sync traffic is the same for every user (I5, E1): two different synthetic profiles send
byte-identical buckets, so an observer of `sync_pack` learns nothing about who is syncing."""
import json
from datetime import date

import pytest

from core import cloud, kb, ledger, router
from core.contracts import Drug, Lab, Profile
from core.decoys import load_buckets

# A second synthetic patient (I1), different from Alex in every field. Some of the meds are in the
# bucket universe on purpose, so the leakage check sees profile words inside cover topics.
BEA = Profile(
    genotypes={"rs9923231": "TT", "rs1057910": "AC"},
    phenotypes={"VKORC1": "high_sensitivity", "CYP2C9": "intermediate_metabolizer"},
    meds=[Drug(ingredient="warfarin", dose_mg=5), Drug(ingredient="metformin", dose_mg=1000),
          Drug(ingredient="amiodarone", dose_mg=200)],
    conditions=["atrial fibrillation", "type 2 diabetes"],
    allergies=["sulfa"],
    labs=[Lab(test="INR", value=3.4, unit="", date=date(2026, 10, 30)),
          Lab(test="eGFR", value=52, unit="mL/min/1.73m2", date=date(2026, 10, 1))],
)


@pytest.fixture(autouse=True)
def demo_cache(tmp_path, monkeypatch):
    for v in ("ANTHROPIC_API_KEY", "GV_LEDGER_PATH", "GV_KB_PATH", "GV_OFFLINE", "GV_DELAY_S",
              "GV_COVER_INTERVAL_S"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setattr(cloud, "_forced", None)
    monkeypatch.setattr(cloud, "_transport", None)
    monkeypatch.setattr(cloud, "_last_failure", None)
    (tmp_path / "all.json").write_text(json.dumps({k: f"General fact about {k}." for b in load_buckets()
                                                   for k in b.keys}))
    monkeypatch.setenv("DEMO", "1")
    monkeypatch.setenv("GV_CLOUD_CACHE", str(tmp_path))
    ledger.reset()
    kb.reset()
    yield
    cloud.set_offline(None)
    ledger.reset()
    kb.reset()


def _traffic(monkeypatch, profile=None):
    """Sync from a cold device as `profile` (None: Alex) and return what went out, per bucket."""
    if profile is not None:
        monkeypatch.setattr(router, "_profile", lambda: profile)
    ledger.reset()
    kb.reset()
    r = router.sync_pack()
    out = {e.bucket_id: (e.kind, e.bytes_out, e.personal_fields_sent, tuple(ledger.outbound(e.seq)))
           for e in ledger.feed(0)}
    return r, out


def test_two_profiles_send_identical_pack_traffic(monkeypatch):
    r_alex, alex = _traffic(monkeypatch)
    r_bea, bea = _traffic(monkeypatch, BEA)
    assert r_alex == r_bea and r_alex["blocked"] == 0
    assert alex == bea                                   # same buckets, same text, same bytes
    assert set(alex) == {b.id for b in load_buckets()}
    assert all(kind == "cover" and pf == 0 for kind, _, pf, _ in alex.values())


def test_no_profile_value_of_the_second_patient_leaves(monkeypatch):
    _, bea = _traffic(monkeypatch, BEA)
    sent = " ".join(t for *_, texts in bea.values() for t in texts).lower()
    for word in ("rs9923231", "rs1057910", "high_sensitivity", "intermediate_metabolizer",
                 "atrial fibrillation", "diabetes", "sulfa", "3.4", " 52"):
        assert word not in sent, word
