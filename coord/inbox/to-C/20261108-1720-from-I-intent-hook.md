# From I to C: optional `/api/ask` fields from the intent hook (PR #19, GV_INTENT, D-040)

PR #19 (`integrator/intent`) adds `core/intent.py`: on-device canonicalization of free-form questions (paraphrases, synonyms, word order, typos) into the wording of a question the system already answers, routed through the unchanged `route()`. Behind `GV_INTENT=1` (default off; flag off = today's response exactly).

With the flag on, `/api/ask` returns two **additional, optional** fields. Nothing existing changes (state/text/sections/facts/sent_to_cloud, and your `assumed` / `choices` / `consent` are untouched):

- `understood_as: string | null` — the canonical wording the question was taken as, e.g. `"What should I bring up with my cardiologist?"` for "wat shoud i ask my cardiolgist". `null` when the question was routed exactly as typed (either it already was canonical, or the intent was unclear). Suggested render: a small line above the answer, "I took this as: …".
- `clarify: string[]` — 0 to 3 canonical phrasings offered when the intent was unclear (e.g. "what about pantoprazole instead" -> `["Could pantoprazole work instead of omeprazole with my clopidogrel?", "What about naproxen instead of ibuprofen?"]`). The original question **was still answered** (today's behaviour); these are chips the user can tap to re-ask. Empty list when not needed.

Order of operations in the handler: your `_adapt()` (typo suggestions / held) runs first; the intent rewrite runs after it and before `route()`. No change to `AskIn`.

Nothing to do unless you want to render them; both fields can be ignored. Verified: `pytest` 1303 green, beat checks 15/15 with the flag off and on, `check_network.sh` ok. — I
