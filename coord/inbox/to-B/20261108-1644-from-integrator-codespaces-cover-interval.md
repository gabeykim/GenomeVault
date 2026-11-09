# FYI: Codespaces demo sets GV_COVER_INTERVAL_S=20 (D-039)

- **From:** integrator (Gabe) · **To:** B · **Time:** 2026-11-08 16:44
- **Type:** information (no action unless you object)
- **Re:** proposals/20261108-1640-C-codespaces-demo.md, D-039, P6.6, D-006

The accepted Codespaces container (PR #13, `.devcontainer/devcontainer.json`) runs the app with `DEMO=1` and `GV_COVER_INTERVAL_S=20`, instead of your default of 60. That makes cover traffic show up sooner in a short web session. It changes no code. If 20 s breaks an assumption in `core/router.py` (for example rate, jitter, or the E1 bucket mix), message the integrator before G5 (18:30) and we'll drop the variable.
