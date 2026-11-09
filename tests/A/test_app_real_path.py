"""A-018 (after G2): C's merged app, wired to A's real modules, shows exactly what A's code computes.

C's own app tests swap A's functions for stand-ins. These tests don't: they go through the real
FastAPI app with the real graph, rules, normalize and capture modules, so if the wiring or A's
output drifts from PLAN P5 (X1-X5, no_data for clopidogrel|pantoprazole, CYP2D6 not assessed),
this suite goes red. Only local endpoints are used: nothing here calls route() or the cloud (I2).
"""
from fastapi.testclient import TestClient

import app as app_module
from core import graph, rules
from core.contracts import Drug

client = TestClient(app_module.app)    # no `with`: the lifespan (cover traffic) never starts

X1_TO_X4 = {
    "X1": "CYP2C19:poor_metabolizer|clopidogrel",
    "X2": "clopidogrel|omeprazole",
    "X3": "SLCO1B1:decreased_function|simvastatin|dose>20mg",
    "X4": "lisinopril|potassium>5.0",
}
X5_KEYS = {"aspirin|ibuprofen", "clopidogrel|ibuprofen", "ibuprofen|lisinopril", "ibuprofen|egfr<60"}


def test_app_uses_a_real_modules_not_mocks():
    modules = client.get("/api/status").json()["modules"]
    for name in ("graph.load_profile", "rules.check", "normalize.to_ingredients", "capture.from_image"):
        assert modules[name] == "real", name
    extras = client.get("/api/status").json()["extras"]
    for name in ("rules.expected_notes_all", "rules.expected_notes", "rules.no_data_keys"):
        assert extras[name], name


def test_profile_endpoint_is_alex_from_data_with_cyp2d6_not_assessed():
    p = client.get("/api/profile").json()
    assert p["phenotypes"]["CYP2D6"] == "not_assessed"          # D-021, D-031
    assert p["genotypes"]["CYP2D6"] == "not_assessed"
    assert p["phenotypes"]["CYP2C19"] == "poor_metabolizer"
    assert sorted(m["ingredient"] for m in p["meds"]) == [
        "aspirin", "clopidogrel", "lisinopril", "omeprazole", "simvastatin"]


def test_flags_endpoint_is_exactly_x1_to_x4_from_real_rules():
    d = client.get("/api/flags").json()
    assert {f["id"]: f["key"] for f in d["flags"]} == X1_TO_X4
    assert len(d["flags"]) == 4                                 # X2 reached from both drugs, shown once
    want = [f.model_dump() for f in rules.check_all(graph.load_profile())]
    assert sorted(d["flags"], key=lambda f: f["key"]) == sorted(want, key=lambda f: f["key"])
    assert all("safe" not in e.lower() for f in d["flags"] for e in f["evidence"])


def test_flags_endpoint_notes_come_from_real_expected_notes():
    d = client.get("/api/flags").json()
    keys = {n["key"] for n in d["notes"]}
    assert keys and keys <= rules.expected_keys()
    assert not keys & {f["key"] for f in d["flags"]}            # a note is never also a flag (D-021)


def test_typed_brand_advil_reaches_x5_on_four_keys():
    d = client.post("/api/check", json={"text": "Advil"}).json()
    assert [x["ingredient"] for x in d["drugs"]] == ["ibuprofen"]
    assert {f["id"] for f in d["flags"]} == {"X5"}
    assert {f["key"] for f in d["flags"]} == X5_KEYS


def test_typed_pantoprazole_is_no_data_never_extrapolated():
    d = client.post("/api/check", json={"text": "Protonix 40 mg"}).json()
    assert [x["ingredient"] for x in d["drugs"]] == ["pantoprazole"]
    assert d["flags"] == []
    assert "clopidogrel|pantoprazole" in d["no_data"]           # S6: absent, not "no interaction" (I4)


def test_typed_unknown_name_gives_nothing_not_a_guess():
    d = client.post("/api/check", json={"text": "Zzzfakeamine"}).json()
    assert d["drugs"] == [] and d["flags"] == [] and d["no_data"] == []


def test_confirmed_label_simvastatin_dose_decides_x3():
    hi = client.post("/api/capture/confirm", json={"drugs": [{"ingredient": "simvastatin", "dose_mg": 40}]}).json()
    lo = client.post("/api/capture/confirm", json={"drugs": [{"ingredient": "simvastatin", "dose_mg": 20}]}).json()
    assert [f["id"] for f in hi["flags"]] == ["X3"]
    assert lo["flags"] == []


def test_question_naming_ibuprofen_adds_x5_to_routed_flags():
    """B-025 via C: a question's named drugs reach route() with their local flags. Checked without
    calling route(): _named_drugs is the app's own step that feeds it."""
    p = graph.load_profile()
    named = app_module._named_drugs("Can I take Advil for my back?", p)
    assert named == [Drug(ingredient="ibuprofen")]
    assert X5_KEYS <= {f.key for f in app_module._flags_for(p.meds + named, p)}
    assert app_module._named_drugs("Is my clopidogrel still OK?", p) == []    # already on the list
