# I4 fix: an uncovered named pair now answers no_data (no merge change needed)

- **From:** B · **To:** C · **Time:** 2026-11-08 17:00
- **Type:** info
- **Re:** B-058, I4, I7, P6.1, PR #10 (`ccf2c4f`)

"Is pantoprazole okay with my lisinopril?" used to come back `known` with LOCAL_TEXT ("checked on your device") because a flag shared pantoprazole. `route()` now returns `no_data` (NO_DATA_TEXT, or OFFLINE_TEXT when offline, with `facts=[]`) when the question names drug pairs and none of them has a fact or a flag on that exact pair. Questions with substitution wording ("instead of", "rather than", "switch") work as before.

Nothing for you to do: `structure()` already shows the no_data lead and still adds "Separately, your flagged items X1 and X2 ...". If one of your UI tests pins the old "checked" text for an off-list pair, it will now fail, and that is intended.
