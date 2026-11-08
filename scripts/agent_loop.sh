#!/usr/bin/env bash
# Runs one agent continuously, one protocol cycle at a time. Start it from the agent's code worktree:
#   cd ../gv-A && AGENT=A VENV=../genomevault/.venv ./scripts/agent_loop.sh
# Defaults to Claude Code headless mode; override AGENT_CMD / AGENT_FLAGS for another agent CLI.
set -u
export DISABLE_AUTOUPDATER=1
: "${AGENT:?set AGENT to A, B, C or D}"
CODE_DIR=$(git rev-parse --show-toplevel)
COORD_DIR="${COORD_DIR:-$(dirname "$CODE_DIR")/gv-$AGENT-coord}"
AGENT_CMD="${AGENT_CMD:-claude -p}"
AGENT_FLAGS="${AGENT_FLAGS:---permission-mode acceptEdits --add-dir $COORD_DIR}"
PAUSE="${PAUSE:-60}"; MAX_FAILS="${MAX_FAILS:-3}"; fails=0
if [ -n "${VENV:-}" ]; then . "$VENV/bin/activate"; fi
[ -d "$COORD_DIR" ] || { echo "missing $COORD_DIR; run scripts/setup_worktrees.sh"; exit 1; }
while true; do
  if ! claude --version >/dev/null 2>&1; then
    echo "[$AGENT] claude unavailable, waiting 60s (not counted as a failure)"
    sleep 60; continue
  fi
  git -C "$COORD_DIR" fetch -q origin main && git -C "$COORD_DIR" rebase -q --autostash origin/main || echo "[$AGENT] coord sync failed"
  if [ -f "$COORD_DIR/coord/FREEZE" ]; then echo "[$AGENT] FREEZE found, stopping."; break; fi
  if [ -f "$COORD_DIR/coord/agents/$AGENT/STOP" ]; then echo "[$AGENT] paused (STOP)"; sleep "$PAUSE"; continue; fi
  prompt=$(sed -e "s|<ID>|$AGENT|g" -e "s|<CODE_DIR>|$CODE_DIR|g" -e "s|<COORD_DIR>|$COORD_DIR|g" "$COORD_DIR/coord/CYCLE_PROMPT.md")
  echo "[$AGENT] cycle start $(date +%H:%M)"
  if $AGENT_CMD "$prompt" $AGENT_FLAGS < /dev/null; then
    fails=0
  else
    fails=$((fails+1)); echo "[$AGENT] cycle failed ($fails/$MAX_FAILS)"
    if [ "$fails" -ge "$MAX_FAILS" ]; then
      f="$COORD_DIR/coord/inbox/to-human/$(date +%Y%m%d-%H%M)-from-$AGENT-loop-stopped.md"
      printf "# Agent %s stopped\n\n%s consecutive failed cycles. Needs a human.\n" "$AGENT" "$MAX_FAILS" > "$f"
      bash "$CODE_DIR/scripts/coord_push.sh" "$AGENT" "loop stopped, needs human" || true
      break
    fi
  fi
  sleep "$PAUSE"
done
