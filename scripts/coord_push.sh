#!/usr/bin/env bash
# Publish one agent's coordination files to main from its coordination worktree.
# Usage (from the agent's code worktree): bash scripts/coord_push.sh <ID> "<ID>-NNN short summary" [--dry-run]
set -euo pipefail
AGENT="${1:?agent ID (A-D)}"; MSG="${2:-status}"; DRY="${3:-}"
CODE_DIR=$(git rev-parse --show-toplevel)
COORD_DIR="${COORD_DIR:-$(dirname "$CODE_DIR")/gv-$AGENT-coord}"
cd "$COORD_DIR"
git add -A -- "coord/agents/$AGENT/STATUS.md" "coord/agents/$AGENT/LOG.md" coord/inbox coord/proposals
bad=$(git diff --cached --name-status | awk -v a="$AGENT" '
  $2 ~ ("^coord/agents/" a "/(STATUS|LOG)\\.md$") { next }
  $1 == "A" && $2 ~ "^coord/(inbox|proposals)/" { next }
  { print }')
if [ -n "$bad" ]; then echo "refusing: not yours to change (AGENTS.md §3):"; echo "$bad"; git reset -q; exit 1; fi
if git diff --cached --quiet; then echo "nothing to publish"; exit 0; fi
if [ "$DRY" = "--dry-run" ]; then git diff --cached --stat; git reset -q; echo "dry run ok"; exit 0; fi
git commit -qm "[$AGENT] report: $MSG"
for i in 1 2 3 4 5; do
  if git fetch -q origin main && git rebase -q origin/main && git push -q origin HEAD:main; then echo "published to main"; exit 0; fi
  git rebase --abort 2>/dev/null || true
  sleep $(( (RANDOM % 5) + 2 ))
done
echo "push failed after 5 tries"; exit 1
