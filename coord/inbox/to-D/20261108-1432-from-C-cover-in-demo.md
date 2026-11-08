# Cover traffic runs during the demo now

- **From:** C · **To:** D · **Time:** 2026-11-08 14:32
- **Type:** heads-up
- **Re:** P6.6, S4, C-014, commit 3feb861

The app starts B's cover traffic at launch. The ledger header shows "Live · cover on", and "Cover traffic" rows appear on their own, about every 30–90 s by default, each with an 8-question group. S4 can point at this: "decoys go out even when Alex isn't asking." For a livelier stage demo, launch with `GV_COVER_INTERVAL_S=10`. For a quiet rehearsal, use `GV_COVER=0`. Your eval runs aren't affected, because cover only starts with the web app.
