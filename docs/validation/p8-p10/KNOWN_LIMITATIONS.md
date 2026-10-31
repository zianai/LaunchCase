# Known limitations and external conditions

- `BLOCKED_EXTERNAL`: three genuine product cases, authorized source/SKU/sample data, two independent blinded reviewers, paired human timing, actual billing and human product-owner acceptance are absent. Synthetic fixtures cannot satisfy those business criteria.
- Paid model/image/Vision execution, private-data inspection, remote Git writes, external publication and production deployment have no new authorization. There is no publishing endpoint.
- Single-host SQLite is the selected boundary. Two real worker processes and checkpoint recovery are tested locally; multi-host shared checkpoints are not. The optional PostgreSQL/Redis probe failed readiness; it is not evidence of a deployed topology.
- Token owners remain trusted to attest genuine source rights and SKU provenance. The system checks immutable bytes, exact excerpts, tenant, versions and synthetic flags; it cannot independently prove a human's property rights, physical sample or claims.
- Current CE consumer allows only explicit zero-cost receipts. Paid use and actual provider billing need a separately authorized integration and cannot be inferred from a fixture.
- Provenance added here does not fabricate missing legacy model/Skill/input hashes. Such historical insights remain unverified and require a new reviewed run. VOC dates remain source facts; historical consumer reviews do not become current market-share measurements.
- Screenshots and automated accessibility checks are engineering evidence. Human design approval, business acceptance and target-user validation remain pending.
- Source-rule revisions intentionally invalidate old packs. Preserve the prior pack and decisions for history, rebuild, then request new human approvals; never silently migrate an old approval to new facts.
