# S6: there's now a one-click "Wi-Fi off" switch in the header

- **From:** C · **To:** D · **Time:** 2026-11-08 14:28
- **Type:** heads-up
- **Re:** F8, S6, C-013, commit 0b8e157

The header now has an **Online / Offline** switch next to "Sent to cloud". Clicking it calls B's `cloud.set_offline(True)`: the pill turns black and reads "Offline", the DNA strand stops, and the Ask tab says only local checks and stored answers work. Clicking it again goes back online. For S6 the script can say "click Online to go offline" instead of turning off the laptop's Wi-Fi, which is safer on stage. Then type **ibuprofen**: all four X5 flags show and the ledger stays at 0 B. It also works through `POST /api/offline {"offline": true|false}` if your rehearsal check wants it.
