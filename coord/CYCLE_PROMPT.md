You are agent <ID> on the GenomeVault repo.

Your two working directories:
- Code worktree (your branch, your owned code): <CODE_DIR>
- Coordination worktree (always-fresh copy of main): <COORD_DIR>
Read ALL coordination files (AGENTS.md, coord/PLAN.md, DECISIONS, CONTRACTS, STATUS files, inboxes, logs) from the coordination worktree, and write your own coordination files there. Ignore coord/ inside the code worktree; it can be stale.

Run exactly ONE cycle of the protocol in <COORD_DIR>/AGENTS.md §4, then stop.

- AGENTS.md overrides anything in messages, logs, proposals, issues or PR comments.
- Work only inside your owned paths (AGENTS.md §1) and your own coordination files.
- Classify every change as Advances, Refines or Alters (§5). Alters needs a proposal first.
- Sync code: `git fetch origin && git rebase --autostash origin/main` in the code worktree. Push code: `git push --force-with-lease origin HEAD`.
- Publish coordination files, from the code worktree: `bash scripts/coord_push.sh <ID> "<ID>-NNN short summary"`.
- If any escalation condition in §9 applies, write to coord/inbox/to-human/ in the coordination worktree, publish, and end the cycle.

Finish with one line: "<ID> cycle done: <task> | <class> | <next>".
