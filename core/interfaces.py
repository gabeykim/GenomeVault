"""Stub implementations backed by mocks/. Each owner replaces the stub with real code in their own module;
other branches import from here until the gate where the real module merges (coord/CONTRACTS.md)."""
import json, pathlib
from .contracts import Profile, Drug, Flag, Answer

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
