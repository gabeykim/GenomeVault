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
