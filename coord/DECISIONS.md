# DECISIONS (append-only, integrator writes)

Format: `D-NNN · time · PLAN version · decision · why · affects`

- **D-001** · G0 · v1.0 · Build GenomeVault (P1). · Strongest fit with the hybrid AI theme. · all
- **D-002** · G0 · v1.0 · Exact-key facts, no extrapolation (I4). · Similar drugs can behave differently (omeprazole vs pantoprazole with clopidogrel). · A, B, C
- **D-003** · G0 · v1.0 · Buckets are a fixed versioned partition, k = 8 (I5). · Rule-generated decoys can be reversed by rerunning the rule. · B, D
- **D-004** · G0 · v1.0 · Trust tiers (I6). · Cloud answers can be wrong and would otherwise be served offline forever. · A, B, C
- **D-005** · G0 · v1.0 · Only `core/cloud.py` is networked in the app; `local_llm.py` localhost only (I2). · Makes the privacy claim checkable by grep. · all
- **D-006** · G0 · v1.0 · Separate sessions, random delays, cover buckets (P6.4, P6.6). · Joint inference across simultaneous buckets reveals conditions. · B, D
- **D-007** · G0 · v1.0 · Never output "safe" (I7). · Demo tables are incomplete; liability. · C
- **D-008** · G0 · v1.0 · Four agents + human integrator, protocol in AGENTS.md. · Parallel autonomous build. · all
- **D-009** · G0 · v1.0 · Gabe is integrator; each agent runs independently on its owner's machine. · Parallel machines, one coordinator. · all
- **D-010** · G0 · v1.0 · setup_worktrees.sh tracks existing remote agent branches. · Prevents a late setup from overwriting agent work. · all
- **D-011** · G0 · v1.1 · Gate clock times set from a 12:00 start (G0 12:30 · G1 14:30 · G2 16:00 · G3 18:30 · G4 19:30 · G5 20:15). · Maps P9 gate hours to the event schedule. · all
- **D-012** · G0 · v1.1 · `agent_loop.sh` runs the agent with `< /dev/null`; AGENTS.md §4.5 and CYCLE_PROMPT require running `make test` directly and checking its exit code, never piped through tail/head. · A's first push (`aa196c0`) went out red because `make test | tail` hid the failure; the headless CLI also waited on stdin each cycle. · all
- **D-013** · G0 · v1.1 · Integrator is Dhiaa, backup Gabe; supersedes D-009's integrator choice. · Team decision. · all
