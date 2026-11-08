# FYI (I3): v3 bucket identity can reveal a genotype

- **From:** D · **To:** integrator · **Time:** 2026-11-08 14:15
- **Type:** heads-up (invariant)
- **Re:** I3, I5, P6.5, B-012, D-007

Thanks for D-016 (`anthropic`); the LLM attacker can now run when a key is present. One finding touches an invariant, so you should know. B's v3 puts phenotype variants of the same topic in different buckets (CYP2C19 + clopidogrel: poor metabolizer b03, intermediate b02; SLCO1B1 + simvastatin: b02 / b01). The outbound text is identical, but which bucket leaves reveals the variant, so guessing the topic also reveals the genotype. E1 measures 2.4% of synthetic patients on v3, and Alex's two gene topics are exactly these. I've sent B the details and two fix options. No D change is needed; the decision is B's, and yours if it needs a ruling.
