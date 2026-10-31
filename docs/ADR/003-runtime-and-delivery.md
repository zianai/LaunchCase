# ADR 003 — V1 runtime and delivery boundary

2026-10-31. Implementation authorization is the user's explicit P0→P6 request; workspace is
`/Users/a/workspaces/AForeign Trade/LaunchCase`. No upstream writes, remote push or deployment.

- Default executable runtime: SQLite business store, SQLite LangGraph checkpoints, deterministic
  OpenAI Agents SDK Model, persistent CreativeEngine protocol Mock, loopback FastAPI/Next.js.
  PostgreSQL business storage + Redis/ARQ is separately integration tested. Graph checkpoints
  remain local SQLite, including the PostgreSQL configuration: V1 is a single-host workbench,
  not a horizontally deployed service.
- Research and product Skills are packaged immutable resources with input/output schemas,
  examples and hashes. Fake Model follows pet-furniture fixture themes; it is a functional
  pipeline, not a generally capable researcher or validated product designer. Paid runners
  are deliberately not configured. No live SDK/model quality claim.
- Domain documents (Insight, Opportunity, Concept, Spec, CostInput, Feasibility, Truth, Rule,
  Sample, LaunchPack) share an immutable, tenant-scoped Artifact envelope with unique per-kind
  versions and separate business services. A document is not a separate mutable case or queue.
- Agent outputs are structured Pydantic models. Business input contracts are canonical generated
  schemas. Immutable document read envelopes use JSON; they are not all independent strict
  Pydantic response classes. Stored lineage is validated by services and export validation.
- G4 records responsible source-backed human attestations for non-synthetic cases/actors;
  it is not certification. G5 external-readiness remains blocked in this internal-only release.
  No real-SKU reference-image upload, truth-to-Engine listing path, publisher, supplier contact,
  mode A/C graph or optional MCP server is implemented. These are explicit extension boundaries.
- Web review uses local human-role identities, exact subject hashes and separate plan/asset
  decisions. Fixture approvals are labelled synthetic; unattended real approvals do not exist.
- Same-origin Web proxy holds an HttpOnly SameSite=Strict cookie. No API token is bundled into
  client JS. Local CLI provisioning is a filesystem-admin operation. It is not public signup.
- Visual baseline remains pending human choice. Independent screenshot review and accessibility
  checks establish evidence about the current implementation, not human design acceptance.
