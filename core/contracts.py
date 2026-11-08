"""Shared types every branch codes against. Integrator-owned; changes are Alters (proposal first)."""
from datetime import date, datetime
from typing import Literal, Optional
from pydantic import BaseModel, field_validator


class Drug(BaseModel):
    ingredient: str                      # normalized generic name, lowercase
    dose_mg: Optional[float] = None


class Lab(BaseModel):
    test: str                            # e.g. "eGFR", "potassium"
    value: float
    unit: str
    date: date
    stale: bool = False                  # set by graph.py (labs older than 90 days)


class Profile(BaseModel):                # never leaves the device
    genotypes: dict[str, str]
    phenotypes: dict[str, str]
    meds: list[Drug]
    conditions: list[str]
    allergies: list[str]
    labs: list[Lab]


def pair_key(a: str, b: str) -> str:
    """Canonical exact key for a drug pair: sorted ingredients joined by '|'."""
    return "|".join(sorted([a.lower(), b.lower()]))


class Flag(BaseModel):
    id: str                              # X1..X5 for Alex
    key: str                             # exact key, e.g. "CYP2C19:poor_metabolizer|clopidogrel"
    severity: Literal["high", "medium", "low"]
    engine: Literal["gene_drug", "drug_drug", "drug_lab", "allergy", "class_rule"]
    evidence: list[str]                  # local-only explanation
    needs_cloud: bool = False


class Topic(BaseModel):                  # generalized, outbound-safe question
    key: str
    text: str


class Fact(BaseModel):
    key: str
    text: str
    tier: Literal["curated", "cloud"]
    source: str
    fetched: date
    expires: date


class Answer(BaseModel):
    state: Literal["known", "none_listed", "no_data"]
    text: str
    facts: list[Fact] = []
    sent_to_cloud: bool = False


class Bucket(BaseModel):
    id: str
    version: str
    keys: list[str]

    @field_validator("keys")
    @classmethod
    def eight(cls, v):
        if len(v) != 8 or len(set(v)) != 8:
            raise ValueError("a bucket holds exactly 8 distinct keys (I5)")
        return v


class LedgerEntry(BaseModel):
    seq: int
    ts: datetime
    bucket_id: Optional[str]
    kind: Literal["bucket", "cover", "kb_hit", "local_only", "blocked"]
    bytes_out: int
    personal_fields_sent: int = 0        # must stay 0 (I3)
