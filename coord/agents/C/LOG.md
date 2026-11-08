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

### C-004 · 2026-11-08 13:33 · commit `84f6e60` · PLAN v1.1

- **Change:** C's ledger tests now follow whoever writes the ledger: the app's mock before `core/ledger.py`, then B's router only. Added a test that the app writes nothing once the ledger is real.
- **Why:** Merging A+B+C locally showed that with B's real ledger and a mock router, two C tests failed, because nothing writes the ledger in that state. That would have turned main red if PR #2 merged before B's router.
- **Class:** Refines
- **Plan:** advances M10
- **Refinements:** none
- **Contract impact:** none
- **Affects:** I: PRs #2 and #3 can merge in either order → none. B: once `core/ledger.py` is on main, the ledger stays empty until `router.route` lands, as you said → none.
- **Demo impact:** none. Between those two merges the UI ledger shows "Nothing has left this device."
- **Tests:** `make test` → exit 0 (38 passed, 1 skipped). origin/main + A + B + C merged locally → `make test` exit 0 (260 passed, 2 skipped)
- **Next:** queue item 6 `actions.py`. After B's PR merges, show `ledger.outbound(seq)` (the 8 questions that left) in the ledger for S4.

### C-005 · 2026-11-08 13:39 · commit `72cde39` · PLAN v1.1

- **Change:** Added `core/actions.py` with three functions. `pharmacist_draft(flags, profile) -> str` is a message to copy that lists meds, allergies and each flag as a question, high severity first, and says "I haven't changed anything I take." `visit_summary(flags, profile, questions=None, today=None) -> dict` returns sections for meds, conditions and allergies, pharmacogenomics, labs, things to discuss, and questions asked; `summary_text` renders it, and `/summary` is a printable HTML page. `reminders(flags, profile, today=None) -> list[dict]` returns reminders to call the pharmacist (high flags, next day), ask about labs (drug–lab flags, 3 days), update old labs (stale labs) and bring the summary (7 days); `reminders_ics` turns them into a calendar file. App endpoints: `GET /api/actions/pharmacist`, `/api/actions/summary`, `/api/actions/reminders`, `/api/actions/reminders.ics`, `/summary`. The UI gets a "05 Actions" section of expandable rows. Added `tests/C/test_actions.py` (11 tests).
- **Why:** BRIEF C queue item 6.
- **Class:** Refines
- **Plan:** advances F7, M9, M10, S6; refines CONTRACTS `actions.*`
- **Refinements:** (1) The signatures above are for CONTRACTS, which lists only the names. (2) Nothing is sent for the user (I2). They copy, print or import each item themselves. (3) The calendar file has no drug, gene, condition, lab value or flag ID, only "GenomeVault: <generic title>". Calendars sync to iCloud or Google, so the detail stays in the app. (4) Reminders only prompt the user to talk to someone, never to take, stop or change a medicine (I7). Due offsets are UI choices, not clinical intervals. (5) The app keeps the last 10 asked questions in memory only, for the summary.
- **Contract impact:** none (C-owned functions; please fold the signatures into CONTRACTS)
- **Affects:** D: the S6 script can show the three actions, and `/summary` makes a good printed handout → none. I: fold the signatures above into CONTRACTS → optional.
- **Demo impact:** S6 (actions: pharmacist draft, printable summary, reminders to the phone via the calendar file until `phone/` exists)
- **Tests:** `make test` → exit 0 (48 passed, 1 skipped). origin/main + A + B (with B's real validator and cloud) + C merged locally → `make test` exit 0 (306 passed, 2 skipped), and the merged answer passes B's `check_output`. Checked by hand in the browser (draft, summary, printable page, reminders, calendar file).
- **Next:** queue item 7, demo mode toggle and offline badge. Queue 5 `phone/` waits on the capture proposal ruling.

### C-006 · 2026-11-08 13:45 · commit `a168a4e` · PLAN v1.1

- **Change:** `merge.personalize` now shows a fact once when the general answer text already states it. The lead gets that fact's tier label: "(AI-summarized, verify.)" for cloud, "(Curated (source).)" for curated. Other facts keep their own paragraph. Added 3 regression tests.
- **Why:** The integration run (origin/main + A + B + C, with real modules wired by hand: generalize → bucket → check_outbound → cloud demo replay → ledger → check_output → merge) showed the same sentence printed twice when `Answer.text` equals the fact's text.
- **Class:** Refines
- **Plan:** advances M9, I6
- **Refinements:** none
- **Contract impact:** none
- **Affects:** none
- **Demo impact:** S4 answer reads cleaner
- **Tests:** `make test` → exit 0 (51 passed, 1 skipped). Integrated A+B+C → exit 0 (309 passed, 2 skipped). The pipeline run's merged answer now shows the fact once.
- **Next:** queue item 7 (demo toggle + offline badge)

### C-007 · 2026-11-08 13:48 · commit `bb0c4fb` · PLAN v1.1

- **Change:** Added `tests/C/conftest.py`. Every C test runs in demo mode with no API key and an empty cloud cache, and gets a fresh ledger and KB.
- **Why:** With origin/main + A + B (real router and KB) + C + D merged locally, two C tests failed. With no key and no demo mode, B's router correctly writes nothing, because nothing left the device. And without isolation, C tests would make live cloud calls on any machine that has a key set.
- **Class:** Refines
- **Plan:** advances M10; I2/I8 hygiene in tests
- **Refinements:** none
- **Contract impact:** none
- **Affects:** none
- **Demo impact:** none
- **Tests:** C alone → exit 0 (51 passed, 1 skipped). A+B+C+D merged → `make test` exit 0, 358 passed (A 4, B 272, C 48, D 30), `check_network.sh` ok, `make eval` exit 0 (simulated backend). With a fake key set, C tests still pass offline. In the merged app, Q18 sends buckets b01 (1248 B) and b05 (959 B) with 0 personal fields, and the UI ledger shows both.
- **Next:** queue item 7 (demo toggle + offline badge); suggestion chips use D's exact demo texts (Q18 already does)

### C-008 · 2026-11-08 13:55 · commit `e569a88` · PLAN v1.1

- **Change:** (1) Ask offers D's demo questions Q18, Q19, Q07 and Q15 as chips, using the exact texts from `eval/queries.json`. They stay after asking and get a ↻ mark, so re-asking shows the KB hit. (2) Each bucket or cover row in the ledger opens to the 8 exact texts that left (`ledger.outbound(seq)`), and the user's own question is marked "yours" by matching `generalize.generalize(flag)`. Only the device can do that. (3) "N facts learned on this device", from `kb.stats()['fresh']`. New endpoint `GET /api/ledger/{seq}/outbound` → `{seq, texts, mine, available}`; `/api/ledger` adds `learned`; `/api/status` adds `extras`. Added `tests/C/test_demo_beats.py` (7 tests).
- **Why:** User-requested polish of S4/S6 ahead of G2/G3, and D's request to use exact eval texts.
- **Class:** Refines
- **Plan:** advances M10, F5, F6, S4, S6
- **Refinements:** B's non-contract extras (`ledger.outbound`, `kb.stats`, `generalize.generalize`) load optionally. A missing attribute hides the feature, and a broken module still raises.
- **Contract impact:** none
- **Affects:** D: chips match Q18/Q19/Q07/Q15 exactly (a test compares them with `eval/queries.json` when present) → none. B: please keep the extras' names → none.
- **Demo impact:** S4 (open the ledger row: 8 questions, "yours" marked), S6 (re-ask Q18 → kb_hit 0 B, "Answered on device", learned counter)
- **Tests:** C alone → `make test` exit 0 (55 passed, 3 skipped). origin/main + A + B + C + D merged → exit 0, 409 passed, 0 skipped, including the full S4 → S6 test (bucket of 8, nothing personal in the texts, ≥8 facts learned, repeat ask is kb_hit 0 B). Checked by hand in the merged app with a placeholder cache.
- **Next:** queue item 7 (offline badge + "Wi-Fi off" toggle using B's `cloud.status`/`set_offline`, DEMO fallback), then 5 (`phone/`)

### C-009 · 2026-11-08 14:01 · commit `4e2ff03` · PLAN v1.1

- **Change:** Simplified the UI. The left side is now four tabs (Medications, Ask, Actions, My data) with one panel showing at a time, a slide-in, arrow-key navigation, and deep links `#ask`, `#actions` and `#data`. Removed the header meta lines, the duplicate personal-fields counter in the header, the per-row pixel glyphs, the engine column, key codes, Q-number and beat labels on the chips, the ledger event count and per-row sub-lines (now a hover title), and the mocks footer (shown only with `?debug`). The wordmark is smaller. `/api/flags` (page load) no longer adds a mock `local_only` ledger row.
- **Why:** Human owner said the page felt cluttered, with too much information on screen.
- **Class:** Refines
- **Plan:** advances M10, S1, S3, S4, S6; refines M10 (layout)
- **Refinements:** tabs replace the stacked sections; demo deep links are `#ask`, `#actions`, `#data` (Medications is the default).
- **Contract impact:** none
- **Affects:** D: the demo script and screenshots now switch tabs instead of scrolling; `/#ask` opens Ask directly → update S4/S6 steps if they mention scrolling.
- **Demo impact:** S1 (hero shorter), S3 (Medications tab, default), S4 (Ask tab + ledger), S6 (Actions tab)
- **Tests:** C alone → exit 0 (55 passed, 3 skipped); A+B+C+D merged → exit 0 (409 passed). Checked by hand at 1440×900 and 375×812: tabs, deep links, ask, ledger, no horizontal scroll.
- **Next:** queue item 7 (offline badge + Wi-Fi-off toggle), cover traffic at startup (G3), then 5 (`phone/`)

### C-010 · 2026-11-08 14:05 · commit `eb74f22` · PLAN v1.1

- **Change:** Added three status colors, used only on small indicators and always next to their word. Red: high severity, poor or decreased gene function, the allergy, labs named in a flag's evidence, and any personal field sent. Amber: medium severity and `no_data` answers. Green: normal gene results, `local_only`/`kb_hit` ledger rows, the "On device" marker, and 0 personal fields.
- **Why:** Human owner asked for color on the indicators (poor = red, good = green).
- **Class:** Refines
- **Plan:** advances M10, S3, S4
- **Refinements:** Color never stands alone (each colored item also says "High", "poor metabolizer", and so on). Labs are never green, because there are no reference ranges in the data; only flags make a lab red. Colors meet AA contrast on bone, with lighter variants on ink.
- **Contract impact:** none
- **Affects:** D: screenshots now show color → retake for slides
- **Demo impact:** S3 (severity readable at a glance), S4 (green 0 personal fields)
- **Tests:** C alone → exit 0 (55 passed, 3 skipped); A+B+C+D merged → exit 0 (409 passed). Checked in the browser, no console errors.
- **Next:** dedupe flags by key so all four X5 flags show (A's 20261108-1359 request) before G1, then queue 7

### C-011 · 2026-11-08 14:14 · commit `2a00181` · PLAN v1.1

- **Change:** `app._flags_for` now dedupes by `flag.key`, not `flag.id`, and sorts by `(id, key)`. Typing "ibuprofen" shows all four X5 flags: `aspirin|ibuprofen`, `clopidogrel|ibuprofen`, `ibuprofen|egfr<60`, `ibuprofen|lisinopril`. Before, it showed only the eGFR flag and hid both bleeding-risk pairs. Changes that follow from shared ids: reminders and merge's "Separately" line name an id once; labs match the profile case-insensitively (key token `egfr` matches `eGFR`), with the key's own lab listed first; drug-class questions read "aspirin 81 mg and ibuprofen"; flag titles show "eGFR < 60". Added `tests/C/test_shared_ids.py` (5 tests) using A's exact X5 flags.
- **Why:** Bug reported by A (20261108-1359) and D (20261108-1405).
- **Class:** Advances
- **Plan:** advances F3 view, M9, M10, S6
- **Refinements:** a finding id can span several keys; the UI shows one row per key, all labeled with the same id.
- **Contract impact:** none
- **Affects:** A: none. D: the S6 ibuprofen check now shows four X5 rows → the script can name the bleeding-risk pairs.
- **Demo impact:** S6 (offline ibuprofen shows the full X5)
- **Tests:** C alone → `make test` exit 0 (60 passed, 3 skipped). origin/main + A + B + C + D merged → exit 0, 550 passed. With A's real `rules.check`, `POST /api/check ibuprofen` → 4 X5 flags, and current meds still give X1–X4. Checked by hand in the merged UI.
- **Next:** queue 7 (offline badge + Wi-Fi-off toggle), cover traffic at startup (G3), then 5 (`phone/`)

### C-012 · 2026-11-08 14:22 · commit `9a4439a` · PLAN v1.2

- **Change:** D-021 in the UI. (1) Genes this kind of test can't call (`not_assessed`, `indeterminate`, `unknown`, `no_call`) show as a gray "not assessed" with a hover reason, never red. The visit summary says "CYP2D6: not assessed by this test" instead of "(notable)". (2) Expected-combination notes: `app.py` passes A's `rules.expected_notes_all(profile)` (on `/api/flags`) and `rules.expected_notes(drug, profile)` (on `/api/check`) through as `notes: [{id, key, text, source}]`, one per key, with text through `merge.guard`. The UI shows a neutral "For information · Aspirin × Clopidogrel" line with an "i" mark under the flags, and the visit summary lists it under "For information (not a warning)". It is never a Flag. Added `tests/C/test_d021.py` (8 tests).
- **Why:** PLAN v1.2 P5 and the integrator's ruling to C (20261108-1404).
- **Class:** Advances
- **Plan:** advances P5, D-021, F3 view, F7, M10, S3
- **Refinements:** notes are neutral by design: no severity and no color, labeled "For information". The source shows on hover.
- **Contract impact:** none
- **Affects:** A: please keep `expected_notes` / `expected_notes_all` and the `{id, key, text, source}` shape → none. I: `mocks/alex_profile.json` still has CYP2D6 `*1/*1` `normal_metabolizer`. Until A's `graph.py` lands, the app loads that mock, so the demo shows CYP2D6 as normal → please update the mock to `not_assessed` (A's `data/alex_profile.json` already is).
- **Demo impact:** S3 (DAPT shown as information, not a warning), My data (CYP2D6 neutral once the profile says `not_assessed`)
- **Tests:** C alone → exit 0 (68 passed, 3 skipped). origin/main + A (`3ce9f6d`) + B + C + D merged → exit 0, 600 passed. In the merged app: EX-001 note shows, `aspirin|clopidogrel` is not flagged, X5 still gives four flags. Checked in the browser, including a not_assessed CYP2D6 render.
- **Next:** D-020: call `capture.from_image` (`POST /api/capture`, phone page) and `cloud.status` (offline badge + Wi-Fi-off toggle) from `app.py`; drop the local stand-ins now covered by interfaces stubs (D-014)

### C-013 · 2026-11-08 14:28 · commit `0b8e157` · PLAN v1.2

- **Change:** An online/offline switch in the header (BRIEF C queue 7). It shows `cloud.status()` (the D-020 contract, interfaces stub until B merges) and toggles B's `cloud.set_offline(True / None)` via `POST /api/offline {"offline": bool}`, which returns 409 when B's cloud isn't present. `/api/status` and `/api/ledger` now carry `cloud: {online, demo, forced_offline, toggle}`. When offline, the switch reads "Offline", the DNA strand pauses, and the Ask tab says only local checks and stored answers work. Also merged main into the branch (D-014/D-020 stubs, PLAN v1.2), made the CYP2D6 summary test accept "not assessed" (A's 1417 note), and tests now reset the switch. Added `tests/C/test_offline.py` (6 tests).
- **Why:** BRIEF C queue 7. D-020 asked C to call `cloud.status` from `app.py`.
- **Class:** Advances
- **Plan:** advances F8, M10, S6, D-020
- **Refinements:** "off" passes `None`, not `False`, so control returns to `GV_OFFLINE` and the network. The switch is visible at every width and disabled, with a reason, when B's cloud isn't present.
- **Contract impact:** none
- **Affects:** B: app calls `cloud.status` and `cloud.set_offline`; please keep the names → none. D: S6 can flip the header switch instead of turning off real Wi-Fi → update the script if you like.
- **Demo impact:** S6 (offline beat is one click and visible on screen)
- **Tests:** C alone → `make test` exit 0 (74 passed, 4 skipped). origin/main + A + B + C + D merged → exit 0, 647 passed, including the S6 test (switch on → ask sends 0 bytes, local check still flags, switch off). Checked by hand in the browser at desktop and phone widths, no console errors.
- **Next:** start B's cover traffic at app startup (G3), then queue 5 `phone/` + `POST /api/capture` (D-020)

### C-014 · 2026-11-08 14:32 · commit `3feb861` · PLAN v1.2

- **Change:** `app.py` starts B's cover traffic (`router.start_cover()`) when the app starts and stops it on shutdown, using a FastAPI lifespan. It only stops cover it started itself. `GV_COVER=0` disables it. `/api/status` and `/api/ledger` add `cover: bool`. The ledger header reads "Live · cover on", with a hover explanation. Added `tests/C/test_cover.py` (6 tests, including a real-thread test on the integrated build).
- **Why:** PLAN P6.6. G3 needs cover traffic in the app (B's 20261108-1450 request).
- **Class:** Advances
- **Plan:** advances P6.6, F4, M10, S4
- **Refinements:** the app runs cover for its whole lifetime. B's thread owns the timing and the offline skip. `GV_COVER=0` is the dev off-switch.
- **Contract impact:** none
- **Affects:** B: app calls `start_cover`, `stop_cover` and `cover_running`; please keep the names → none. D: cover rows show up during the demo (one every ~30–90 s by default). Set `GV_COVER_INTERVAL_S` to make them livelier, or `GV_COVER=0` for a quiet rehearsal → optional script note.
- **Demo impact:** S4 (the ledger shows steady cover traffic next to real decoy groups; "cover on" in the header)
- **Tests:** C alone → `make test` exit 0 (79 passed, 5 skipped). origin/main + A (`f9db84a`) + B (`85ab929`) + C + D (`928224d`) merged → exit 0, 723 passed, **no mocks left in the app**. With `GV_COVER_INTERVAL_S=8` in the merged preview, 3 cover rows (b17, b04, b10, ~3 KB, 0 personal fields) arrived in 20 s.
- **Next:** queue 5: `phone/` page + `POST /api/capture` (A's real `capture.from_image` is now on PR #1), then drop the stand-ins (D-014)

### C-015 · 2026-11-08 14:41 · commit `bd85112` · PLAN v1.2

- **Change:** Added the phone page (BRIEF C queue 5) at `/phone` (`phone/index.html`, `phone.css`, `phone.js`). It has: take a photo of a label, two synthetic sample labels (`phone/samples/*.png`, built with A's `capture.demo_png`), or type a name. Then it shows flags in red/amber, info notes, and reminders with "Add to my calendar". `POST /api/capture` takes the raw image bytes plus Content-Type (no multipart dependency), calls `capture.from_image` (D-020), and returns `{read, drugs, flags, notes}`. The photo is never stored or sent. `GET /api/captures?since` feeds a live "From your phone" list on the laptop's Medications tab. `/api/check` accepts `via: "phone"`. Pairing: any request that isn't from this machine needs the code from Actions → Use your phone (`POST /api/phone/pair` sets an HttpOnly, SameSite=Strict cookie; lockout after 10 misses; `GET /api/phone` shows the code to the laptop only). `phone/serve_https.sh` serves on the LAN over HTTPS with a 7-day self-signed cert from the system `openssl`, kept in `~/.genomevault/cert`, never in the repo. Added `tests/C/test_phone.py` (17 tests).
- **Why:** BRIEF C queue 5, S2 and S6 ("actions to phone"). D-020 asked C to call `capture.from_image` from `app.py`.
- **Class:** Advances
- **Plan:** advances F2, M10, S2, S6, D-020
- **Refinements:** (1) Pairing gate: the app is reachable on the LAN only through `serve_https.sh`, and only paired devices get data. (2) No voice input, because browser speech recognition sends audio to a cloud service (contrary to P1). (3) Raw-body upload avoids adding `python-multipart`. (4) An unreadable photo says so honestly and points to typed input.
- **Contract impact:** none
- **Affects:** A: app passes raw bytes + Content-Type to `capture.from_image` → none. D: S2 can be phone page → tap the Plavix sample (or a real photo with tesseract) → it shows on the laptop → script note. I: `phone/serve_https.sh` binds 0.0.0.0, pairing-gated → FYI.
- **Demo impact:** S2 (capture on phone, appears on the laptop), S6 (reminders on the phone)
- **Tests:** C alone → `make test` exit 0 (94 passed, 7 skipped). origin/main + A + B + C + D merged → exit 0, 743 passed; both samples read with A's reader (clopidogrel → X1, X2; ibuprofen → X5 ×4). Real `serve_https.sh` run on the LAN IP: `/phone` 200, unpaired `/api/profile` 401, pair 200, capture reads ibuprofen with 4 flags, a paired phone gets 403 for `/api/phone`, and the laptop sees the capture. Checked by hand at phone and desktop sizes, no console errors.
- **Next:** drop the stand-ins (D-014); rehearsal with D's script after the merge
