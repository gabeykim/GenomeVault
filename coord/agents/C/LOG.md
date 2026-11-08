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
