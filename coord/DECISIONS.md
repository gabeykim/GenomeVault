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
- **D-014** · G1 · v1.2 · Accept C's stub-gap note (c8a7839): add `core/interfaces.py` stubs for `normalize.to_ingredients` and `ledger.feed` (both already in CONTRACTS). · Aligns M12 interfaces with CONTRACTS; C drops local stand-ins. · A, B, C · pass by backup integrator Gabe
- **D-015** · G1 · v1.2 · Noted C's status/risks heads-up; B and D loops confirmed running (board); the capture/status proposal is ruled in D-020. · FYI, no PLAN change (F4, G2). · C · pass by backup integrator Gabe
- **D-016** · G1 · v1.2 · Accept D's request: add `anthropic` to `requirements.txt` (lazy import in `eval/llm_client.py`, used only when `EVAL_LLM=1`; no key in repo). · Enables E1 LLM attacker and E3 quality judge; deterministic evals unaffected; I2 keeps eval network inside `llm_client.py`. · D · pass by backup integrator Gabe
- **D-017** · G1 · v1.2 · Noted C-004: A+B+C integrate green, PR merge order is free. · FYI; informs G1/G2 merge sequencing. · all · pass by backup integrator Gabe
- **D-018** · G1 · v1.2 · Noted C-007: all four branches integrate green; G1 blocker = A's real `rules.check` (X1–X4), G2 blocker = `mocks/cloud_cache` recording (D-019). · FYI; drives the G1 gate check and D-019. · all · pass by backup integrator Gabe
- **D-019** · G1 · v1.2 · Accept B's cloud_cache need (B-005): `mocks/cloud_cache/*.json` must be recorded before G2, but recording needs ANTHROPIC_API_KEY, which is not in this environment. B generates the JSON and sends it, or Gabe supplies a key; integrator commits it before G2. · Demo mode replays the cache (I8, M8, S6); no secret is committed. · B · pass by backup integrator Gabe
- **D-020** · G1 · v1.2 · Accept C's additive contract proposal (20261108-1323): add `capture.from_image(data,mime)->list[Drug]` (owner A) and `cloud.status()->dict{online,demo}` (owner B) to CONTRACTS + interfaces stubs + a test. Implementation routed to owners: A (queue 6), B (queue 9); C calls both from `app.py`. · Additive only, no migration; unblocks S2 photo and S6 offline badge (F2, F8, I2). · A, B, C, D · pass by backup integrator Gabe
- **D-021** · G1 · v1.2 · PGx corrections (P5): CYP2D6 → not_assessed (SNP-uncallable), no rule may use it; `aspirin|clopidogrel` is expected DAPT after a stent — informational UI note, not a Flag (A adds `data/rules/expected_combinations.json`); NSAID+antiplatelet X5 still fires for ibuprofen; A matches genotypes by rsID (VCF ID), GRCh38 positions fixed (rs4244285 chr10:94781859, rs4986893 chr10:94780653, rs12248560 chr10:94761900; 94775489 is rs17884712 *9, not *3); unverifiable positions marked in `data/README.md`. · Prevents a false DAPT flag and mis-mapped genotypes while preserving I4/I7. · A, C, D · pass by backup integrator Gabe
