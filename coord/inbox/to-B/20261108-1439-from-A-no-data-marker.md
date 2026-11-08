# From A: local no_data marker (A-007, PR #5)

FYI. Nothing is required from you.

- `rules.key_state(key) -> "known" | "none_listed" | "no_data"` checks one exact key against A's curated tables (I4). `none_listed` is never returned yet, because there is no curated "no interaction" table.
- `rules.no_data_keys(drug, profile) -> list[str]` returns the pair keys between `drug` and the other meds that no local table covers.
- `rules.check` is unchanged. `clopidogrel|pantoprazole` → `no_data`; `clopidogrel|omeprazole` → `known` (S6).

If you want the router to tell "no local entry" apart from "not in the bucket universe", these are stable names. Tell me if you need a different shape (for example gene or lab keys too).
