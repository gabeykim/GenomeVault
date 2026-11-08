from core.interfaces import load_profile, check
from core.contracts import Drug, Bucket, pair_key
import pytest

def test_mock_profile_loads():
    p = load_profile()
    assert p.phenotypes["CYP2C19"] == "poor_metabolizer"

def test_mock_flags_for_clopidogrel():
    ids = {f.id for f in check(Drug(ingredient="clopidogrel"), load_profile())}
    assert {"X1", "X2"} <= ids

def test_pair_key_is_canonical():
    assert pair_key("Omeprazole", "clopidogrel") == "clopidogrel|omeprazole"

def test_bucket_must_hold_eight():
    with pytest.raises(ValueError):
        Bucket(id="B0", version="v1", keys=["a"] * 8)

def test_new_contract_stubs():
    from core.interfaces import to_ingredients, feed, from_image, status
    assert isinstance(to_ingredients("aspirin, clopidogrel"), list)
    assert from_image(b"", "image/png")[0].ingredient == "clopidogrel"
    assert feed(0) == []
    s = status()
    assert set(s) == {"online", "demo"}
    assert isinstance(s["online"], bool) and isinstance(s["demo"], bool)
