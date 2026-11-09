"""Stub implementations backed by mocks/. Each owner replaces the stub with real code in their own module;
other branches import from here until the gate where the real module merges (coord/CONTRACTS.md)."""
import json, os, pathlib
from .contracts import Profile, Drug, Flag, Answer, LedgerEntry

MOCKS = pathlib.Path(__file__).resolve().parent.parent / "mocks"

def load_profile() -> Profile:                                   # A, real at G1
    return Profile.model_validate_json((MOCKS / "alex_profile.json").read_text())

def check(drug: Drug, profile: Profile) -> list[Flag]:           # A, real at G1
    flags = [Flag.model_validate(f) for f in json.loads((MOCKS / "flags.json").read_text())]
    return [f for f in flags if drug.ingredient in f.key]

def route(question: str, flags: list[Flag]) -> Answer:           # B, real at G2
    return Answer.model_validate_json((MOCKS / "answer.json").read_text())

def personalize(answer: Answer, flags: list[Flag], profile: Profile) -> str:   # C, real at G2
    return f"[mock] {answer.text}"

def to_ingredients(text: str) -> list[Drug]:                     # A (normalize), real at G1
    return [Drug(ingredient=w.strip().lower()) for w in text.split(",") if w.strip()]

def feed(since: int) -> list[LedgerEntry]:                       # B (ledger), real at G2
    return []

def from_image(data: bytes, mime: str) -> list[Drug]:            # A (capture), real at G3; [] if unreadable
    return [Drug(ingredient="clopidogrel", dose_mg=75)]

def status() -> dict:                                            # B (cloud), real at G3; sends nothing (I2)
    return {"online": True, "demo": os.getenv("DEMO") == "1"}

def suggest(text: str) -> list[dict]:                            # A (normalize), D-040/D-041; flag-off behavior
    return []

def single_candidates(question: str, flags: list[Flag]) -> list[str]:   # B (router), D-040/D-041; flag-off
    return []

def send_single(key: str) -> Answer:                             # B (router), D-040/D-041; flag-off, sends nothing
    return Answer(state="no_data", text="[mock] single send off", facts=[], sent_to_cloud=False)
