# LaunchCase Architecture Decision Register — Draft for Codex to adopt as ADRs

This is a decision seed. Codex records formal ADR files after verifying environment and interface versions. Do not erase contrary existing evidence.

| ID | Decision | Consequence / guardrail |
|---|---|---|
| ADR-001 | LaunchCase is a standalone B2C ProductCase service | No B2C fields in TradeCase DB, no cross-service transaction |
| ADR-002 | ProductCase != SKU != Concept | Multiple concepts/SKUs per case; revisioned links |
| ADR-003 | Market data evidence is immutable with source/rights/time | No unsupported quantitative claims; explicit sufficiency result |
| ADR-004 | Skills define methods, Agent SDK executes bounded tasks | No custom react loop or one persistent agent per employee role |
| ADR-005 | CaseService + LangGraph + DB Task lease, each one responsibility | Queue wakeups are not business truth; checkpoint is cursor |
| ADR-006 | ProductSpecVersion is a versioned proposal; ProductTruthSnapshot only for supported facts | Concept graphics may not certify true specs; no reverse evidence link |
| ADR-007 | Human Gate G1-G5 binds immutable subject digest | Source/price/spec/visual change invalidates related approval |
| ADR-008 | CreativeEngine is separate HTTP adapter; protocol 1.0.0 initially | Engine owns image queue, QA, source assets; LaunchCase owns stage/approval semantics |
| ADR-009 | Money and stage eligibility computed deterministically | Decimal, currency/unit normalization, null for missing and disclosed assumptions |
| ADR-010 | Offline-first and safe default | FakeAgent/Mock Provider; no marketplace write, purchase or paid request |
| ADR-011 | CLI, REST, UI use same Application Services | No hidden business state in frontend or shell scripts |
| ADR-012 | V1 outcome is internal draft and sample-validation readiness | No fake G4 sample sign-off or platform listing readiness |
| ADR-013 | One editable copy of each Skill and immutable loaded snapshots | Skills not mutable truth; repo-local installation optional |
| ADR-014 | Source references are per-version and tenant scoped | No generated pixels or synthetic dataset as factual source |
| ADR-015 | Versioned integration contracts with consumer tests | Adapt version changes explicitly; don't guess JSON paths |

## Reuse matrix (read source first)

- Directly reuse **design patterns** from TradeCase: FastAPI service boundaries, Pydantic strict schemas, Alembic, DB leases with fencing, LangGraph checkpointing, Fake SDK model, source provenance, source ingestion safety, immutable approval, local demo, reports, CI. Review code licenses and behavior before copying modules; do not create fragile imports from an unrelated application package.
- Directly consume existing **CreativeEngine HTTP APIs**: create project, source assets, truth snapshot, brief, plan, batch, polling, image review and approved ZIP. Do not copy its Node/SQLite worker/QA or call its internals.
- Create new **LaunchCase-only modules**: market observations, VOC, opportunities, concepts, product spec versions, cost scenario, GateDecision, launch pack, feedback links.
- Future cross-project sharing should only happen after stable contracts and tests justify package extraction. V1 avoids premature shared monorepo and shared DB.

## Source baseline checked 2026-10-30

- TradeCase `main` observed HEAD `11147c12d21305862ad67a2bd439e7c486e06d5a`; visual branch `codex/tradecase-visual-tasks` observed HEAD `4b70f652f72ba82c0e03d5d05fd4cd1e43c687dd` (report references feature commit `5bc0d4e`; these are historical inspection points, not immutable assumptions for implementation).
- TradeCase visual upgrade report: existing workspace 538 passed/0 skipped at report time; this is **reported historical evidence**; rerun before making new claims.
- CreativeEngine `main` README declares local REST `http://127.0.0.1:4310/v1`, Node 24+/pnpm, HTTP OpenAPI and visual task protocol 1.0.0; confirmed no paid-model live image run in its published README.
