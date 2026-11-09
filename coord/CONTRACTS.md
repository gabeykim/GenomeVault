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
| `normalize.suggest` | A | `(text: str) -> list[dict]`; `[]` unless `GV_FUZZY=1`. Dict keys: `token`, `term`, `span: [start, end]`, `mode: "assumed" \| "ask"`, `assumed: str \| None`, `choices: list[str]` (1–3), `not_covered: list[str]`. Never feeds a key directly (I4): the user's confirmed text goes back through `to_ingredients` | G5 (D-040, D-041) |
| `router.single_candidates` | B | `(question: str, flags: list[Flag]) -> list[str]`; `[]` unless `GV_TAIL=1`; local only, sends nothing | G5 (D-040, D-041) |
| `router.send_single` | B | `(key: str) -> Answer`; only after the user consents; `no_data` when `GV_TAIL` is off or offline; raises `ValueError` for a key in a fixed partition (I5) | G5 (D-040, D-041) |

Ledger conventions (D-041, no type change): a long-tail bucket send is a `bucket`/`cover` entry with `bucket_id` `tail-NNNN` ("Tail group of 8 sent"); a consented single send is a `bucket` entry with `bucket_id` `single` ("Single question sent, not hidden").

Keys: drug pairs are sorted ingredient names joined by `|` (`clopidogrel|omeprazole`). Gene–drug keys: `GENE:phenotype|drug`. Dose conditions are suffixes (`|dose>20mg`).
