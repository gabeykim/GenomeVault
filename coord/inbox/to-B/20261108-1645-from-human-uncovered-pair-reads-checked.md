# Priority: an uncovered drug pair answers "known" / "checked" (I4) — must land before 18:15

- **From:** human (Dhiaa, B owner) · **To:** B · **Time:** 2026-11-08 16:45
- **Type:** request (priority)
- **Re:** I4, router.route answer state, merge LOCAL_TEXT, G4

Exact check (main 6f9403e, DEMO=1, FastAPI TestClient):

    POST /api/ask {"question": "Is pantoprazole okay with my lisinopril?"}
    -> state "known", sent_to_cloud false, facts []
    -> text: "In general: This was checked on your device against your own records. Nothing was sent.
             Separately, your flagged items X1 and X2 are still worth raising. ..."

`pantoprazole|lisinopril` is not in the partition and has no curated or stored fact, so the asked pair has
nothing behind it. "Checked on your device" reads as "nothing found", which is the reassurance I4/I7 forbid,
and a judge can type exactly this kind of pair. Expected: state `no_data` for the asked pair with NO_DATA_TEXT
(or OFFLINE_TEXT when offline), while the current flags X1/X2 can still be listed separately. The other
pantoprazole question (`clopidogrel|pantoprazole`) is fine: it answers from its own exact key.

Please add a test for a question whose named pair is outside the universe and not covered by any flag on that
pair, and tell C if the merge text needs to change. Must land before G4 (18:15).
