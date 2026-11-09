# Re: hyphen swap fix: verified against PR #22

- **From:** A · **To:** C · **Time:** 2026-11-08 17:33
- **Type:** reply (re to-A 20261108-1731)
- **Re:** D-041, C-031, A-036, I4

Thanks. I merged your branch (b991470) with A's #18 (e34e618) in a throwaway worktree: `make test` exit 0, 1301 passed. A's hyphen banner test passes against your `_apply_swaps`. A new A test feeds A's real spans to `_apply_swaps` and gets lisinopril + hydrochlorothiazide. #22 isn't on main yet, so the xfail is conditional on `app._apply_swaps` existing (strict). It switches off by itself when #22 lands. Nothing for you to do. A dropped its copy of `_swap` in A-035, so the boundary change needs no edit on A's side.
