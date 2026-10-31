---
name: market-research
version: 1.0.0
---

# market-research

Restrict scope to Amazon US and the target segment. Read authorized imports only. Separate listed prices from realized sales. Market tables contain observed fields only; missing demand, denominators and revenue stay null. Preserve date, product identity and uncertain variant matching. State source limits.

Inputs: frozen tenant-scoped Evidence with locator, rights, synthetic status and original hash.
Outputs: structured observations/hypotheses with evidence IDs, counter-evidence and sample limitations.
Never call paid services, mutate facts or choose human decisions. Stop on citation failure, source corruption or exhausted budget.
