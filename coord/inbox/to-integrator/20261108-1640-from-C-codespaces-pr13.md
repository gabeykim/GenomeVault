# PR #13: one-click Codespaces demo link (prepared for you; your call)

- **From:** C · **To:** integrator (Gabe) · **Time:** 2026-11-08 16:40
- **Type:** request (re proposal 20261108-1640-C-codespaces-demo.md)
- **Re:** C-028, S2, I2, I8

Cristian asked for a GitHub link that runs the demo like it runs locally. `.devcontainer/` and `README.md` are yours, so I prepared them on `integrator/codespaces-demo` as PR #13, tagged [I] and labeled "prepared by C". Merge it only if you accept the proposal. The link is `https://codespaces.new/gabeykim/GenomeVault?quickstart=1`. It starts the same app as `make demo` (DEMO=1, no key) and opens it in a browser tab.

C's app part (`82a7205`, the phone address inside a codespace) is on PR #11. PR #13 works without it, but the phone link needs it.

After merging, please open the link once to confirm it boots. I couldn't create a codespace from here. Setting About → Website to the link needs admin.
