"""Agent C: merge.personalize (BRIEF C queue 2, M9). Never 'safe', no start/stop (I7); tiers (I6)."""
import json
import re
from datetime import date
from pathlib import Path

import pytest

from core import merge
from core.contracts import Answer, Fact, Flag
from core.interfaces import load_profile

MOCKS = Path(__file__).resolve().parents[2] / "mocks"
PROFILE = load_profile()
FLAGS = [Flag.model_validate(f) for f in json.loads((MOCKS / "flags.json").read_text())]
TODAY = date(2026, 11, 8)

BANNED = re.compile(r"\bsafe(r|st|ly)?\b|\b(stop|start|quit|discontinue)\s+taking\b|\bswitch to\b", re.I)


def fact(key="clopidogrel|omeprazole", text="Omeprazole reduces clopidogrel activation.", tier="cloud", source="cloud"):
    return Fact(key=key, text=text, tier=tier, source=source, fetched=TODAY, expires=TODAY)


def test_known_answer_is_personalized_with_relevant_flags():
    a = Answer(state="known", text="Clopidogrel response differs by CYP2C19 metabolizer type.", sent_to_cloud=True)
    out = merge.personalize(a, FLAGS, PROFILE)
    assert out.startswith("In general: Clopidogrel response differs")
    assert "For you:" in out
    assert "X1 (high)" in out and "X2 (high)" in out
    assert "*2/*2" in out and "75 mg" in out          # the user's own genotype and dose, locally
    assert "X3" not in out and "X4" not in out        # unrelated flags stay out


def test_flag_description_uses_profile_labs_and_trend():
    x4 = next(f for f in FLAGS if f.id == "X4")
    s = merge.describe(x4, PROFILE)
    assert "lisinopril 10 mg" in s and "potassium 5.2" in s and "eGFR 62 → 48" in s


def test_lab_names_match_whole_words_only():
    flag = Flag(id="T1", key="aspirin|clopidogrel", severity="low", engine="drug_drug",
                evidence=["discuss alternatives"])  # "alternatives" must not pull in the ALT lab
    assert "ALT" not in merge.describe(flag, PROFILE)


def test_cloud_text_and_facts_are_labeled_verify():  # I6
    a = Answer(state="known", text="PPIs differ in CYP2C19 inhibition.", facts=[fact()], sent_to_cloud=True)
    out = merge.personalize(a, FLAGS, PROFILE)
    assert "(AI-summarized, verify.)" in out
    assert "AI-summarized, verify: Omeprazole reduces clopidogrel activation." in out


def test_fact_already_in_the_answer_is_shown_once():
    # The router may set Answer.text to the fact's own text (found in the A+B+C integration run).
    f = fact(text="Omeprazole reduces clopidogrel activation.")
    a = Answer(state="known", text="Omeprazole reduces clopidogrel activation.", facts=[f], sent_to_cloud=True)
    out = merge.personalize(a, FLAGS, PROFILE)
    assert out.count("Omeprazole reduces clopidogrel activation") == 1
    assert out.startswith("In general: Omeprazole reduces clopidogrel activation. (AI-summarized, verify.)")


def test_curated_fact_in_the_answer_keeps_its_source_label():
    f = fact(text="Omeprazole reduces clopidogrel activation", tier="curated", source="CPIC 2022")
    a = Answer(state="known", text="Omeprazole reduces clopidogrel activation.", facts=[f])
    out = merge.personalize(a, FLAGS, PROFILE)
    assert out.count("Omeprazole reduces clopidogrel activation") == 1
    assert "(Curated (CPIC 2022).)" in out and "AI-summarized" not in out


def test_other_facts_still_get_their_own_paragraph():
    covered = fact(text="Omeprazole reduces clopidogrel activation.")
    other = fact(key="CYP2C19:poor_metabolizer|clopidogrel", text="CYP2C19 poor metabolizers activate less clopidogrel.")
    a = Answer(state="known", text="Omeprazole reduces clopidogrel activation.", facts=[covered, other],
               sent_to_cloud=True)
    out = merge.personalize(a, FLAGS, PROFILE)
    assert "AI-summarized, verify: CYP2C19 poor metabolizers activate less clopidogrel." in out
    assert out.count("Omeprazole reduces clopidogrel activation") == 1


def test_curated_facts_name_their_source():
    a = Answer(state="known", text="", facts=[fact(tier="curated", source="CPIC 2022")])
    assert "Curated (CPIC 2022):" in merge.personalize(a, FLAGS, PROFILE)


def test_no_data_never_implies_no_interaction():
    out = merge.personalize(Answer(state="no_data", text=""), FLAGS, PROFILE)
    assert "no data" in out.lower()
    assert "does not mean there is no interaction" in out
    assert "X1 and X2 are still worth raising" in out


def test_none_listed_names_source_and_is_not_a_guarantee():
    a = Answer(state="none_listed", text="", facts=[fact(key="aspirin|lisinopril", text="No interaction listed.",
                                                         tier="curated", source="DrugBank")])
    out = merge.personalize(a, FLAGS, PROFILE)
    assert "No interaction is listed for this in DrugBank" in out
    assert "not a guarantee" in out


@pytest.mark.parametrize("bad", [
    "Pantoprazole is a safe alternative.",
    "Pantoprazole is safer.",
    "It is safe to take both.",
    "You should stop taking omeprazole.",
    "Start taking pantoprazole instead.",
    "Switch to pantoprazole.",
    "Discontinue simvastatin.",
    "Lower your dose of simvastatin.",
])
def test_guard_removes_unsafe_wording_from_cloud_text(bad):  # I7
    a = Answer(state="known", text=f"PPIs differ in CYP2C19 inhibition. {bad}", facts=[fact(text=bad)],
               sent_to_cloud=True)
    out = merge.personalize(a, FLAGS, PROFILE)
    assert not BANNED.search(out), out
    assert "PPIs differ in CYP2C19 inhibition." in out
    assert out.startswith("In general:")


def test_every_output_ends_with_pharmacist_closing():
    for state in ("known", "none_listed", "no_data"):
        out = merge.personalize(Answer(state=state, text="General text."), FLAGS, PROFILE)
        assert out.endswith(merge.CLOSING)


def test_all_banned_text_still_returns_something():
    a = Answer(state="known", text="It is safe.", sent_to_cloud=True)
    out = merge.personalize(a, [], PROFILE)
    assert out == merge.CLOSING


def test_validator_checks_only_the_general_text(monkeypatch):
    seen = []

    def fake_check(text, facts):
        seen.append(text)
        return True

    monkeypatch.setattr(merge, "_output_check", lambda: fake_check)
    a = Answer(state="known", text="Clopidogrel response differs by CYP2C19 type.", sent_to_cloud=True)
    out = merge.personalize(a, FLAGS, PROFILE)
    assert seen == ["Clopidogrel response differs by CYP2C19 type."]   # not the personal paragraph
    assert "75 mg" in out


def test_failed_validator_withholds_general_text_but_keeps_flags(monkeypatch):
    monkeypatch.setattr(merge, "_output_check", lambda: (lambda text, facts: False))
    a = Answer(state="known", text="Clopidogrel needs 300 mg loading in everyone.", sent_to_cloud=True)
    out = merge.personalize(a, FLAGS, PROFILE)
    assert "300 mg" not in out
    assert out.startswith(merge.WITHHELD)
    assert "For you:" in out


def test_app_uses_real_merge():
    import app
    assert app.MODES["merge.personalize"] == "real"


# ---------- structure: lead with the asked pair (C-021) ----------

def _router_answer(*facts):
    """What B's router returns: Answer.text is the facts' texts joined by blank lines (B-006)."""
    return Answer(state="known", text="\n\n".join(f.text for f in facts), facts=list(facts), sent_to_cloud=True)


X1F = fact(key="CYP2C19:poor_metabolizer|clopidogrel", text="Clopidogrel is a prodrug activated by CYP2C19.\n\nMore detail.")
X2F = fact(key="clopidogrel|omeprazole", text="An interaction with omeprazole is listed.")
PANF = fact(key="clopidogrel|pantoprazole", text="An interaction with pantoprazole is classed as minor.\n\nOutcome data are mixed.")


def test_question_pair_leads_when_flags_cover_the_rest():  # Q07
    secs = merge.structure(_router_answer(X1F, X2F, PANF), FLAGS, PROFILE)
    facts = [s for s in secs if s["kind"] == "fact"]
    assert [s["key"] for s in facts] == ["clopidogrel|pantoprazole", "CYP2C19:poor_metabolizer|clopidogrel",
                                         "clopidogrel|omeprazole"]
    assert facts[0]["primary"] and not facts[1]["primary"]
    assert facts[0]["paragraphs"] == ["An interaction with pantoprazole is classed as minor.", "Outcome data are mixed."]
    out = merge.personalize(_router_answer(X1F, X2F, PANF), FLAGS, PROFILE)
    assert out.startswith("In general: An interaction with pantoprazole is classed as minor.")
    assert out.count("pantoprazole is classed as minor") == 1


def test_router_order_kept_when_every_fact_is_flag_backed():  # Q18
    secs = merge.structure(_router_answer(X1F, X2F), FLAGS, PROFILE)
    assert [s["key"] for s in secs if s["kind"] == "fact"] == ["CYP2C19:poor_metabolizer|clopidogrel", "clopidogrel|omeprazole"]


def test_sections_end_with_personal_then_closing():
    kinds = [s["kind"] for s in merge.structure(_router_answer(X1F, PANF), FLAGS, PROFILE)]
    assert kinds[-2:] == ["personal", "closing"]


def test_every_fact_section_carries_its_tier_label():  # I6
    for s in merge.structure(_router_answer(X1F, PANF), FLAGS, PROFILE):
        if s["kind"] == "fact":
            assert s["label"] == "AI-summarized, verify" and s["tier"] == "cloud"


def test_withheld_applies_to_router_answers_too(monkeypatch):
    monkeypatch.setattr(merge, "_output_check", lambda: (lambda text, facts: False))
    secs = merge.structure(_router_answer(X1F, PANF), FLAGS, PROFILE)
    assert secs[0] == {"kind": "lead", "paragraphs": [merge.WITHHELD]}
    assert not [s for s in secs if s["kind"] == "fact"]


def test_guard_still_applies_inside_sections():  # I7
    bad = fact(key="clopidogrel|pantoprazole", text="Pantoprazole is safer. Outcome data are mixed.")
    secs = merge.structure(_router_answer(X1F, bad), FLAGS, PROFILE)
    joined = " ".join(p for s in secs for p in s["paragraphs"])
    assert not BANNED.search(joined) and "Outcome data are mixed." in joined


def test_ask_endpoint_returns_sections():
    from fastapi.testclient import TestClient
    import app
    d = TestClient(app.app).post("/api/ask", json={"question": "What should I bring up with my cardiologist?"}).json()
    assert d["sections"] and d["sections"][-1]["kind"] == "closing"


# ---------- questions that name a drug not on the list (B-025, Q15) ----------

X5_FLAGS = [Flag(id="X5", key="aspirin|ibuprofen", severity="high", engine="class_rule",
                 evidence=["ibuprofen is an NSAID", "aspirin is an antiplatelet"]),
            Flag(id="X5", key="clopidogrel|ibuprofen", severity="high", engine="class_rule",
                 evidence=["ibuprofen is an NSAID", "clopidogrel is an antiplatelet"])]


def test_flags_for_a_drug_not_taken_are_described_even_if_the_answer_names_no_drug():
    local = Answer(state="known", text="Answered from the local tables on this device.")   # router LOCAL_TEXT style
    out = merge.personalize(local, FLAGS + X5_FLAGS, PROFILE)
    assert "For you: X5 (high): aspirin 81 mg and ibuprofen." in out
    assert "X1" not in out.split("For you:")[1]      # current-med flags still need a mention to show


def test_named_drug_flags_reach_the_router(monkeypatch):
    import app
    from fastapi.testclient import TestClient
    from core.contracts import Drug
    seen = {}
    monkeypatch.setattr(app, "to_ingredients", lambda text: [Drug(ingredient="ibuprofen")] if "ibuprofen" in text else [])
    monkeypatch.setattr(app, "check", lambda d, p: list(X5_FLAGS) if d.ingredient == "ibuprofen" else [])
    monkeypatch.setattr(app, "route", lambda q, flags: seen.setdefault("flags", flags) and Answer(state="known", text="Local."))
    TestClient(app.app).post("/api/ask", json={"question": "Can I take ibuprofen for a headache?"})
    assert {f.key for f in seen["flags"]} == {"aspirin|ibuprofen", "clopidogrel|ibuprofen"}


def test_lab_token_from_a_key_reads_with_profile_spelling():
    f = Flag(id="X5", key="ibuprofen|egfr<60", severity="high", engine="drug_lab", evidence=["eGFR 48"])
    assert "your eGFR 62 → 48" in merge.describe(f, PROFILE)
