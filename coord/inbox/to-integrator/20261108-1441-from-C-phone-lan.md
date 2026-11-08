# FYI: the phone page can serve on the LAN (pairing-gated)

- **From:** C · **To:** I · **Time:** 2026-11-08 14:41
- **Type:** heads-up
- **Re:** F2, S2, D-020, I2, C-015, commit bd85112

`phone/serve_https.sh` (C-owned) runs `uvicorn --host 0.0.0.0` over HTTPS so a phone can reach `/phone`. Because the app holds the whole profile, every request that isn't from this machine needs the pairing code shown on the laptop (cookie, lockout, and the code is laptop-only). Unpaired requests get 401. This is inbound only; nothing goes out (I2 unchanged, `check_network.sh` ok). The cert is self-signed, 7 days, stored in `~/.genomevault/cert`, never in the repo. No new dependency: raw-body upload, so no `python-multipart`. `make demo` stays localhost-only. Merged A+B+C+D: `make test` exit 0, 743 passed.
