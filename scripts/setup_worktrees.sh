#!/usr/bin/env bash
# Integrator runs once from the main clone after the first push.
# Creates each agent's branch, its code worktree (../gv-<ID>) and its coordination worktree (../gv-<ID>-coord).
set -euo pipefail
ROOT=$(git rev-parse --show-toplevel); PARENT=$(dirname "$ROOT")
branch() { case "$1" in A) echo agent/A-data-rules;; B) echo agent/B-privacy-router;; C) echo agent/C-app-ui;; D) echo agent/D-eval;; esac; }
git fetch -q origin
for a in A B C D; do
  b=$(branch "$a")
  git show-ref --verify --quiet "refs/heads/$b" || git branch "$b" origin/main
  git push -q -u origin "$b" || true
  [ -d "$PARENT/gv-$a" ] || git worktree add "$PARENT/gv-$a" "$b"
  [ -d "$PARENT/gv-$a-coord" ] || git worktree add --detach "$PARENT/gv-$a-coord" origin/main
done
git worktree list
