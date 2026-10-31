# LaunchCase V1 — P0→P6 Executable Work Breakdown

## Execution convention

Do stages in dependency order. **Task IDs are traceable scope units**, not individual commits by requirement. Do not substitute future-phase fake empty functions for work completed in the current stage. Each P-stage is done only with (a) implementation, (b) a reproducible fixture, (c) tests executed, (d) artifacts/README, (e) real status report, (f) a local Git commit. If an optional integration is unavailable, implement a contract fake and record a blocker; do not fabricate live evidence.

All examples of paths below are target suggestions; P0 should inspect local repo and lock final paths in `docs/ADR/` before production changes. Strong preference for `src/launchcase/{domain,application,infrastructure,workflow,agents,skills,integrations,api,cli}`, `frontend/`, `migrations/`, `tests/`, `fixtures/`, `project/`, `work/` to stay familiar to TradeCase.

Dependencies: P0 -> P1 -> P2 -> P3 -> P4 -> P5 -> P6. P5 commercial development can follow P3 without images, but integration testing still runs after P4. Do not let unavailable paid API block core tasks.

## P0 — Repository governance, architecture, executable baseline

- **LC-P0-01 Repo reconnaissance:** read TradeCase main + visual branch and CreativeEngine docs, capture inspected commit SHAs, actual API version, licenses, what is reusable vs to be written. Deliver `docs/BASELINE_AUDIT.md`, reuse matrix, explicit no-copy risks. Do not mutate upstream repos.
- **LC-P0-02 Continuity:** establish LaunchCase-owned `AGENTS.md`, `project/state.yaml`, `work/active/LC-001-v1/task.yaml` and ADRs following schema 3 / protocol 3.0 only after checking actual compatible conventions. New project_id unique (`LAUNCHCASE_V1`). Never overwrite a pre-existing AGENTS file without inspecting and merging.
- **LC-P0-03 Package foundation:** Python package `src/launchcase`, locked `uv`/`pyproject.toml`, Pydantic v2 strict base models, SQLAlchemy base, Alembic baseline, FastAPI health, CLI `launchcase doctor`, structured error/result, env config with default offline/paid false, Ruff/pytest; Next.js minimal shell if build tools present.
- **LC-P0-04 Architectural contracts:** draft ERD for ProductCase/Task/Evidence/Gate/VisualTask, versioned OpenAPI baseline, application services interfaces, Runtime/Creative adapter `Protocol`, graph node and authority map.
- **LC-P0-05 CI and security:** environment example (no secrets), format+type/test job, file ignore rules for images/quotes/DB/keys, tenant_id query test foundation, fake model and mock image provider fixtures.

**P0 acceptance:** `uv sync --extra dev`, `uv run pytest`, `uv run ruff check .`, `uv run launchcase doctor`, `uv run python -c "import launchcase.api"` plus an isolated FastAPI `/health` smoke check, `alembic upgrade head` on disposable SQLite, `frontend npm run typecheck && npm run build` if shell bootstrapped. Current installed versions and commands verified in actual output; no unbounded dependencies. `docs/PHASE_REPORTS/P0.md` has exit codes and SHA.

## P1 — Authorized ingestion + durable evidence and ProductCase

- **LC-P1-01 Domain persistence:** ProductCase, ProductBriefVersion, SourceDocument, Evidence, MarketSnapshot, AuditEvent, Artifact manifest; migrate with IDs, tenant keys, version unique constraints and indexes. Source file bytes in content-addressed store with SHA256, not blob-duplicated in arbitrary log messages.
- **LC-P1-02 Importers:** strict CSV/JSON/TXT/MD import; review/competitor/spec/quote parsers with provenance, source locator (row/file), timestamp, rights and synthetic flags. Constrain MIME, file bytes, row counts, encoded text, and duplicate rows; record parsing warnings. No third-party login/scraping in P1.
- **LC-P1-03 Normalization:** marketplace+country+currency; product identity matching with ambiguities; date/time normalization; exact quotes/snapshots; contradictory evidence retained, not overwritten.
- **LC-P1-04 Services and APIs:** create/list/read ProductCase, import and read sources/evidence, manage Brief revisions, tenant access checks; CLI `case create`, `source import`, `case status` via application services.
- **LC-P1-05 Safety/recovery:** transactional version increments, immutable original retention, restart-safe import, idempotent source import fingerprint; file traversal/symlink/path and tenant abuse tests; audit event with no raw secret.

**P1 acceptance:** two imports of the same file do not duplicate evidence; revoking rights or changing an input source does not make old approvals silently current; a user from tenant B cannot read tenant A sources, images, events. Synthetic PET-FURNITURE example imports with exact row pointers. Invalid/corrupt/huge uploads fail explicitly, without partial import. `docs/PHASE_REPORTS/P1.md` records migration upgrade/downgrade and test commands.

## P2 — Research Agent + evidence-first VOC / opportunity discovery

- **LC-P2-01 Skill package:** canonical `skills/market-research/`, `skills/voc-analysis/`, `skills/opportunity-discovery/`, each with SKILL.md, input-output schema, examples, version hash and source-limits; avoid more agent roles than needed.
- **LC-P2-02 AgentRunner:** reuse TradeCase *pattern* (not import database): OpenAI Agents SDK adapter behind stable Python Protocol + deterministic FakeRunner. Read-only tools restricted by tenant and source IDs; tool budget, deadline, max turns, structured output, stop reasons. Unit tests require no paid calls.
- **LC-P2-03 Data analyses:** review normalization, duplicate detection, issue/theme coding with raw quote backrefs, contradictory themes, price/feature tables only when denominator data exists. Keep complaints from different product variants distinguishable; unknown sample bias explicit.
- **LC-P2-04 Insight/Opportunity service:** versioned Insight/Opportunity entities, evidence sufficiency result with reasons, alternative explanations, confidence *class* and falsification plan. An opportunity has at least evidence refs and assumptions; one-sentence intuition alone not enough.
- **LC-P2-05 Workflow start:** LangGraph nodes `validate_brief` → `normalize_sources` → research fan-out (where truly independent) → merge/conflict → evidence gate → opportunity proposals → G1 interrupt. Checkpointer and business states persisted; bounded backfill and `needs_input` path.

**P2 acceptance:** expected synthetic themes with exact quoted row refs; contradictory data not silently majority-voted; ≤small sample cannot claim category-wide percentage; unsupported figure = null; prompt injection inside a review changes no instruction/permission; restarting after interrupted research preserves Task and Case. SDK FakeRunner actually executes through the adapter or fake with schema, not a fabricated finished report file. `docs/PHASE_REPORTS/P2.md`.

## P3 — Product opportunities, concepts, versioned spec and human gates

- **LC-P3-01 Product Agent:** canonical `skills/product-definition/` and `skills/concept-design/`; produce 2–3 genuinely different proposal directions tied to selected Opportunity, target segment, functional/CMF/usage constraints, risks and assumptions.
- **LC-P3-02 ProductSpec:** versioned `ProductSpecVersion`, `Concept` parent refs, per-claim states and evidence, diff and rollback; `ProductTruthSnapshot` only after independent supported source/attestation, not from concept or image.
- **LC-P3-03 Gate framework:** G1/G2 decisions, role authorization, exact subject hash, append-only decision record, invalidation upon evidence/spec/concept edit. Implement G3–G5 gate schema now but no fake pass logic. A review mutation cannot be performed by Agent token without user role.
- **LC-P3-04 Workflow continuation:** G1 selection → bounded concept creation → product definition → G2 interrupt; reject/revise generates new concept/spec version and returns to appropriate node. CaseService guards stages; LangGraph checkpoint is cursor only.
- **LC-P3-05 CLI/API:** `run concepts`, `gate decide` with expected hash, `spec history`, `concept compare`, `GET /.../events` durable progress replay.

**P3 acceptance:** one synthetic Case creates at least two differentiated concepts with source-backed problem statements, human-style review API can choose one, stale hash 409, edited spec invalidates earlier gate decisions, no Agent self-approval. `ProductSpecVersion` can hold unknown dimensions/materials as null or proposal and cannot automatically yield verified facts. `docs/PHASE_REPORTS/P3.md`.

**P3 milestone:** real useful offline **Research → Opportunity → Concept + Review** MVP (without creative images or financial integration).

## P4 — CreativeEngine HTTP integration and domain-specific VisualTask

- **LC-P4-01 Integration audit:** compare live local CreativeEngine `/v1/openapi.json` to docs and 1.0.0 contract; implement `CreativeEngineClient` `MockClient` with version checking, strict auth, no path/DB imports, timeouts and bounded polling. `LAUNCHCASE_CREATIVE_ENGINE_MODE=disabled|mock|http`, default `mock`/disabled safe.
- **LC-P4-02 Visual domain:** `VisualIntent` (concept exploration vs listing), ProductCase/Concept/Spec version refs, source permissions, CreativePlan/VisualTask/VisualRun and asset mapping. Source ID `source.system=launchcase`. No generation on raw market `Evidence` unless authorized image rights and purpose.
- **LC-P4-03 Creative task flow:** create project → asset mapping → truth snapshot (only real supported facts) → structured brief (`product-concept`) → plan dry run → budget/rights approval → remote batch with Idempotency-Key → status sync → separate machine QA/human asset review → approved internal export. For unverified Concept, keep `internal_only`; strict Listing blocked until genuine SKU verified. Allow ProductCase progression without images.
- **LC-P4-04 Failure/recovery:** stale plan/providercfg, Engine down, blocked constraints, network timeout before/after remote receipt, repeated submission, remote reconciliation and cancellation; no second image Worker. Do not retry chargeable/unknown remote call blindly.
- **LC-P4-05 Contract tests:** new LaunchCase consumer tests against MockClient and actual local HTTP CreativeEngine when available, plus 1.0.0 mismatch test. Evidence source rules prohibit generated art and derived background as verified product truth.

**P4 acceptance:** one approved concept plan completes against local Mock HTTP or fake adapter (report which), outputs an immutable concept image asset with visible Mock/Concept status; plan approval != asset review; template/schema mismatch blocks; stage change or spec hash invalidates review. Strict SKU listing with no actual verified photo is blocked. `docs/PHASE_REPORTS/P4.md`.

## P5 — Deterministic unit economics, feasibility and governance

- **LC-P5-01 Costs:** `CostInput`/`CostScenario`, Decimal money and currency conversion records, unit normalization, supplier quote source/revision/validity; formula and scenario assumptions explicit; no missing=0.
- **LC-P5-02 Risk:** engineering/supply-chain/compliance/returns/marketing assumptions with evidence and accountable owner, not binary legal conclusions. Rules have market/scope/date/hash; missing current official applicability -> `needs_review`.
- **LC-P5-03 Human G3–G5:** feasibility decision before sample authorization; G4 actual samples/test/attestation only; G5 outward-ready preconditions and explicit **no publishing**; when missing sample, internal draft can still be produced without fraudulent gate pass.
- **LC-P5-04 LaunchPack internal draft:** versioned PRD/Opportunity Memo/concept comparison/cost model/risk register/approved internal visuals/Listing **draft** with unsupported claims withheld + todo for external verification. External-facing pack only with individual confirmed product facts, current rules and explicit approval.
- **LC-P5-05 Security and drift:** stale supplier quote, changed ProductSpec, expired rules, revoked rights, removed approval, changing image file digest all trigger gate re-evaluation. High impact failures fail closed; all edits audited.

**P5 acceptance:** unit economics tests with mixed currency/unit, missing price and source-expired cases; no made-up fees, margins or certification. Editing any referenced spec/quote/visual invalidates its approvals; synthetic case reaches internal handoff but cannot reach real-ready-for-listing. `docs/PHASE_REPORTS/P5.md`.

## P6 — Integrated Web, CLI, exports and reliability/ops

- **LC-P6-01 Next.js workbench:** Case list, create brief, source import, evidence trace, VOC, opportunity comparison, concept and Spec diff, feasibility, review Inbox, VisualTask gallery and internal LaunchPack, settings/capability pages. Real API calls, no permanent canned fake dashboard.
- **LC-P6-02 CLI/MCP:** CLI calls same application services as REST. Optional stdio MCP exposes read/query/create-draft/task-status actions, **not bypass gate**. CLI docs and `--json`, `doctor` check. Structured errors and versions.
- **LC-P6-03 Export:** deterministic JSON + Markdown, immutable manifest with source/Spec/decision versions and SHA; internal draft watermarks/labels, mock and concept status visible, never includes internal secrets. ZIP bundles only approved-for-internal assets; no real listing publish.
- **LC-P6-04 Reliability:** PostgreSQL+Redis/ARQ local infra smoke if authorized Docker available; database migrations, backup/restore source+object hashes, Worker interruption, duplicate queue wakeups, lease expiration, checkpoint replay, idempotency, SSE reconnection. SQLite-only tests always runnable if Docker absent.
- **LC-P6-05 Visual accessibility:** desktop + 390px, keyboard review controls, source citations, errors, clear unknown states; actual browser screenshot for UI review and transparent claim of design acceptance.
- **LC-P6-06 End-to-end demo:** `fixtures/scenarios/pet-furniture-us/` in synthetic, no paid calls; report Case ID, source/evidence, opportunities, at least 2 concepts, versioned Spec, cost missing/conditional result, blocked/pending G4/G5, mock visual, internal launch pack. Automatable script `scripts/demo_offline.py`, `launchcase demo ...`, strict validator and clean wheel install.
- **LC-P6-07 Documentation:** README quickstart, runbook, API/OpenAPI, retention and deletion, licenses, deployment/recovery, `docs/DELIVERY_REPORT.md`, `docs/CAPABILITY_STATUS.md`, ADRs and reproducible test evidence without secrets.

**P6 acceptance:** full real local browser/API/database workflow + CLI + mock Engine Contract, all 12+ boundary tests, build, migrations, offline clean install and recovery. Never claim model output quality or user conversion tested merely because the full synthetic demo is green.

## Concrete mandatory terminal verification (Codex should adapt after P0)

```bash
uv sync --extra dev
uv run ruff check .
uv run pytest -q
uv run python -m compileall -q src
uv run launchcase doctor
uv run launchcase demo --fixture fixtures/scenarios/pet-furniture-us --out .launchcase/demo-001
uv run launchcase validate --case .launchcase/demo-001 --strict
cd frontend && npm ci && npm run typecheck && npm run build
```

If Docker is present and authorized:

```bash
# Use isolated project names, no disruption to TradeCase/CreativeEngine
python ops/verify_infrastructure.py
```

Always show actual exit codes and which commands were **not** run. P0 can adjust commands/flags if it records final CLI contract first. Use separate temporary dirs for fixture and always use non-existent output targets.

## Suggested commit series (no push)

- `feat(launchcase): P0 product domain and baseline`
- `feat(launchcase): P1 evidence persistence and import`
- `feat(launchcase): P2 VOC research and opportunity graph`
- `feat(launchcase): P3 concepts specs and human gates`
- `feat(launchcase): P4 creative engine adapter and visual tasks`
- `feat(launchcase): P5 economics and launch checks`
- `feat(launchcase): P6 case workbench and offline e2e`

No arbitrary one-commit-big-bang. Release tag and remote push are separate user choices.
