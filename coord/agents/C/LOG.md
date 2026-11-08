# Agent C — impact log (append only)

Entries use coord/templates/impact-report.md and are numbered C-001, C-002, ...

### C-001 · 2026-11-08 13:10 · commit `c8a7839` · PLAN v1.1

- **Change:** `app.py` (FastAPI) plus the two-pane UI in `ui/`. Left pane has the profile panel marked "Stays on this device", flags, a typed drug check, and chat. Right pane has the live outbound ledger with byte and personal-field totals. Also added `tests/C/test_app.py` (13 tests).
- **Why:** BRIEF C queue item 1, the base for S3/S4.
- **Class:** Refines
- **Plan:** advances F2 (typed input), F3 view, F5 view, M10; refines M10
- **Refinements:** (1) At startup the app uses each real module (`graph`, `rules`, `normalize`, `router`, `merge`, `ledger`) once it exists, and falls back to the mock otherwise. A broken real module raises instead of silently using the mock. `/api/status` and the UI footer show which modules are mocks. (2) Until `core/ledger.py` exists, app.py keeps a labeled mock ledger: `local_only` for local checks, and a `bucket` entry with a fixed 1440-byte placeholder when `Answer.sent_to_cloud`. The app writes nothing to the ledger once B's is real. (3) UI is self-contained, with no external assets (I8).
- **Contract impact:** none
- **Affects:** I: `core/interfaces.py` has no stubs for `ledger.feed` or `normalize.to_ingredients`, so app.py carries stand-ins → optional: add stubs. B: app reads `ledger.feed(since)` → none. A: typed input calls `normalize.to_ingredients(text)` → none.
- **Demo impact:** S3 (flags + "0 bytes sent"), S4 (ledger shows the bucket entry) now exist on mocks
- **Tests:** `make test` → 17 passed; `scripts/check_network.sh` → ok; `check_ownership.py` → ok
- **Next:** UI redesign (minimal visual style, motion), then queue item 2 `merge.py`

### C-002 · 2026-11-08 13:20 · commit `f886031` · PLAN v1.1

- **Change:** Redesigned `ui/` in a monochrome style: bone paper, black ink, a giant split GENOME▬VAULT wordmark, numbered sections on heavy rules, and index-style flag rows that fill with ink on hover and expand to show evidence. Added motion: an intro where the "sequencing lanes" slide open, a DNA barcode strand where 8 identical packets slide across whenever a bucket or cover entry appears in the ledger, wipe-in ledger rows, and rolling counters. Fixed the ledger column, which was not staying sticky.
- **Why:** Human owner asked for a sleeker, more minimal demo with stronger motion. This polishes S1/S3/S4.
- **Class:** Refines
- **Plan:** advances M10, S1, S3, S4; refines M10 (visual style)
- **Refinements:** (1) Fixed light theme in every system theme. (2) Severity is shown by a 3-block glyph plus the word, not color. (3) Each flag gets a 5×5 pixel glyph hashed from its exact key (decorative). (4) Motion is off under prefers-reduced-motion. A click skips the intro. (5) Still no external assets (I8).
- **Contract impact:** none
- **Affects:** D: slides and the S4 demo script can use the packet animation as the "decoy group leaves" visual → none required
- **Demo impact:** S1 (intro and wordmark), S3 (flag rows), S4 (packets cross the strand when a bucket leaves)
- **Tests:** `make test` → 17 passed; `check_network.sh` → ok; `check_ownership.py` → ok; checked by hand in the browser at 1440×900 and 375×812
- **Next:** queue item 2, `merge.py`

### C-003 · 2026-11-08 13:31 · commits `037d993`, `e57fccf` · PLAN v1.1

- **Change:** Added `core/merge.py`. `personalize(answer, flags, profile) -> str` turns the router's general Answer and the local flags into an answer about this user, on device. The text opens by state (`known` "In general: …", `none_listed` names the curated source and says it is not a guarantee, `no_data` says a missing entry is not "no interaction"). Next comes every fact with its tier label, then "For you:" with the user's own dose, genotype and lab trend for each flag whose drug or gene the answer mentions, and a closing pharmacist line. Calls B's `validator.check_output(text, facts)` on the general text only. A failed check withholds that text and keeps the local flags. The UI renders the merged paragraphs. Added `tests/C/test_merge.py` (20 tests).
- **Why:** BRIEF C queue item 2.
- **Class:** Advances
- **Plan:** advances M9, F4 (merge step), I4, I6, I7, S4; refines M9
- **Refinements:** (1) Deterministic, no model call, so I7 is enforced by code and works offline (I8). (2) I7 guard: any sentence matching "safe/safer/safest/safely", "no risk/danger", start/stop/quit/discontinue/resume + taking, "switch to/from", "you should/must take/stop/…" or "lower/raise your dose" is dropped. This applies to cloud text and fact text before anything is shown. (3) Output format: paragraphs separated by a blank line, always ending with the closing line `merge.CLOSING`. (4) Relevance is by whole-word match of a flag's drug or gene names in the answer text and fact keys. When nothing matches, the high flags are listed by ID.
- **Contract impact:** none
- **Affects:** B: `check_output` gets the generalized answer text and `Answer.facts`, never the personal paragraph → none. D: E3 quality scoring can rely on the format above → none.
- **Demo impact:** S4 (the answer now names the user's doses and genotype, computed locally)
- **Tests:** `make test` → exit 0, 37 passed; `check_network.sh` ok; `check_ownership.py` ok; checked by hand in the browser
- **Next:** queue item 6 `actions.py` (no dependencies). Queue 5 `phone/` waits on the capture proposal. Queues 3/4 switch automatically when A and B merge.
