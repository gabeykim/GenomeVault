# CONTRACTS

Human-readable summary of `core/contracts.py` and `core/interfaces.py`. Integrator-owned. Changing either is an **Alters** change: proposal first.

| Function | Owner | Signature | Mock until |
| --- | --- | --- | --- |
| `rules.check` | A | `(drug: Drug, profile: Profile) -> list[Flag]` | G1 |
| `normalize.to_ingredients` | A | `(text: str) -> list[Drug]` | G1 |
| `graph.load_profile` | A | `() -> Profile` | G1 |
| `router.route` | B | `(question: str, flags: list[Flag]) -> Answer` | G2 |
| `kb.get` | B | `(key: str) -> Fact | None` | G3 |
| `ledger.feed` | B | `(since: int) -> list[LedgerEntry]` | G2 |
| `merge.personalize` | C | `(answer: Answer, flags: list[Flag], profile: Profile) -> str` | G2 |
| `actions.*` | C | `pharmacist_draft`, `visit_summary`, `reminders` | G3 |
| `capture.from_image` | A | `(data: bytes, mime: str) -> list[Drug]` | G3 |
| `cloud.status` | B | `() -> dict` (keys `online: bool`, `demo: bool`) | G3 |

Keys: drug pairs are sorted ingredient names joined by `|` (`clopidogrel|omeprazole`). Gene–drug keys: `GENE:phenotype|drug`. Dose conditions are suffixes (`|dose>20mg`).
