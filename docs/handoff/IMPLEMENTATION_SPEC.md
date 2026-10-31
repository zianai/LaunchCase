# LaunchCase V1 — Product & Engineering Implementation Specification

**Status:** Codex executable implementation specification; **not implemented code**.  
**Owner:** User-directed independent LaunchCase product.  
**Baseline:** Verified TradeCase/CreativeEngine GitHub source as of 2026-10-30; actual implementation must recheck repos, branch SHA and API.  
**Primary scenario:** Amazon US, differentiated non-high-risk consumer product development (Mode B).  
**Primary constraint:** Offline-first, source-first, human decision gates, no paid calls/outbound/publishing by default.  
**Primary output:** A persistent, auditable ProductCase and an **internal draft** LaunchPack, with blockers explicitly attached. Reaching a sample/launch-approved state requires genuine product and human verification.

## 0. North Star and absolute non-goals

LaunchCase is **an AI-native product development decision workbench**: convert licensed product research data and real VOC into traceable opportunity hypotheses, differentiated product concepts, versioned specifications, feasibility analyses and draft launch assets, while keeping business decisions explicit and reversible. No business value is proven by producing more charts, chat turns or generated pictures.

TradeCase remains B2B inquiry conversion; LaunchCase is an independent B2C development service. CreativeEngine is the shared image execution boundary. Do **not** create a universal Case type, a shared SQL DB, a standalone browser automation image worker, a proprietary Agent reasoning loop, a generalized ERP, a pure prompt app, auto-purchasing, an auto-listing publisher, or unlicensed scraping.

V1 implements one coherent Mode B path. Support Mode A (existing SKU optimization) and Mode C (zero-to-one innovation) as schema/UI enum and future extension points, **not** fake complete business graphs. Do not represent unimplemented modes as ready.

### 0.1 Core invariants

- **Source-first:** Evidence has source locator + immutable file hash + collection time + usage-rights status; inferred insight binds evidence IDs; missing/biased evidence is explicit.
- **Fact separation:** `OBSERVED`, `INFERRED`, `HYPOTHESIS`, `USER_ATTESTED`, and `VERIFIED` are not interchangeable. A model's confidence is not verification.
- **Versioned business truth:** `ProductSpecVersion` tracks proposal; `ProductTruthSnapshot` contains separately supported facts, their origin and allowed outward use. Generated visuals cannot be source evidence.
- **Deterministic guardrails:** Gate transitions, cost arithmetic, permission, source validity, file checks, QA state and retries are code, not prompt.
- **Single owner per responsibility:** CaseService status; LangGraph step ordering; TaskManager leases/attempts; Agent SDK bounded investigation; CreativeEngine image generation and image QA; Human owner approval.
- **Explicit uncertainty:** if costs are unknown, calculate conditional scenarios or null; if no sample, keep G4 blocked; if rules unavailable, show `needs_review`.
- **Side effects closed:** No external paid/image/model call, seller account login, supplier contact, purchase or publication without new explicit permission.
- **Test evidence:** distinguish implemented, tested_offline, tested_local_http, tested_live, blocked, user_accepted, production_ready.

## 1. Product roles and operator experience

Primary role: consumer-hardware or general consumer-goods Product Manager, category manager or small development team. Secondary: designer, sourcing engineer, compliance/reviewer and ecommerce operator. Authentication roles initially `admin`, `owner`, `contributor`, `reviewer`, `viewer` with server-scoped permissions; maintain `tenant_id` in data and queries even for local tenant.

Primary journey: user creates Product Brief → imports authorized reviews, competitor rows, spec and quote → reads AI research with evidence cards → accepts/rejects opportunity → compares 2–3 concept proposals → edits and approves one version → reviews cost/risk with missing-data prompts → initiates a concept VisualTask in CreativeEngine → reviews returned assets → exports PRD and **internal** draft LaunchPack. All meaningful actions and decisions survive restart. Source/visual status remains visible beside output; no implicit model-driven next action.

UI primary navigation: Product Case list / Inbox (review + blockers) / Product Case workspace / Assets / Sources & Knowledge / Settings. Within Case: Overview, Research, Opportunities, Concepts & Spec, Feasibility, Visuals, LaunchPack, Activity. Chat may be an optional task input but **not** the UI information architecture.

### 1.1 Outcome metrics (defined, not invented)

Measure: evidence link coverage of nontrivial claims (numerator/denominator), unresolved critical assumptions count, duplicate review rate, gate bypass count (=0 desired), recoverable tasks %, known cost coverage, approval latency, time from brief to first reviewable opportunity and cost to usable approved asset. Real opportunity hit rate, product sales, CTR, conversion uplift and true engineering feasibility are `not_measured` until authorized field evaluation.

## 2. Mode B workflow and state machine

`new → collecting_sources → researching → opportunity_review → concepting → concept_review → feasibility_review → awaiting_sample_validation → launch_draft → ready_for_internal_handoff` with orthogonal statuses `needs_input`, `needs_review`, `paused`, `failed`, `cancelled` and transitions back to earlier **versioned** work. Avoid coupling a Case's current stage to image batch status.

### 2.1 Graph nodes

1. `validate_brief`: Pydantic; market/platform/category/objectives/budget/time; missing required inputs → `needs_input`.
2. `normalize_sources`: authorized sources, hash, time, origin, target SKU/product match; reject unsafe imports.
3. `plan_research`: bounded plan of evidence needs; no model-driven unbounded browsing.
4. `research_market` + `research_voc` + `research_competitors`: independent read-only tasks where sources permit; FakeAgent offline.
5. `merge_evidence`: versioned claims, de-duplication and contradiction marking; no synthetic evidence upgrades.
6. `evidence_sufficiency_gate`: deterministic coverage/material-missing review; not a magic confidence score. Low coverage → bounded request for evidence or human gate.
7. `propose_opportunities`: explicit problem, segment, alternatives, qualitative support, assumptions, falsification test.
8. `G1_opportunity_review`: human select/reject/research_more; binds exact evidence and opportunity version hash.
9. `develop_concepts`: limited concept directions, differentiators, design constraints and risk register; create concept proposals.
10. `define_product_spec`: canonical proposed spec version, unsupported fields marked `proposed`/null.
11. `G2_concept_review`: human pick/refine/reject, exact version binding.
12. `calculate_feasibility`: deterministic costs/sensitivity; append sourcing/manufacturing/compliance placeholders with source status.
13. `G3_feasibility_review`: human may authorize **sample investigation**, not claim manufacturing feasible without evidence; missing critical inputs block release.
14. `request_visual_tasks`: optional asynchronous child tasks; **does not block research/PRD**. Concept imagery internal only, user budget/rights required.
15. `G4_sample_validation`: demands external sample/test confirmations attached; V1 synthetic flows stop at `awaiting_sample_validation` or proceed only to an *internal draft*.
16. `build_launch_draft`: internal concept-based copy/visual briefs, data/claim gaps, SKU and platform checklists. No unverified actual item listing.
17. `G5_launch_review`: only after verified SKU truth + current scoped platform rules + exact asset reviews; even if approved, V1 produces a handoff, **no publication**.
18. `persist_report`: immutable source-backed Case history, audit/event records, export manifests.

### 2.2 Gates exactly

| Gate | Required inputs | Allowed decisions | Hard block |
|---|---|---|---|
| G1 Opportunity | Evidence sufficiency, dated samples, contradiction/rights status | `accept`, `research_more`, `reject` | No traceable evidence / authority failure |
| G2 Concept | Concept version, target needs, constraints, differentiators | `select`, `revise`, `reject` | Model invents user approval / missing concept revision |
| G3 Feasibility | Cost scenarios, design risks, engineering unknowns, compliance risk | `sample_validation`, `revise`, `hold` | Unknown unit economics cannot claim viable; unsafe use not certified |
| G4 Sample | Real sample/test records + responsible human attestation | `verify_sample`, `rework`, `hold` | Synthetic/demo approvals must not count as real sample evidence |
| G5 Launch | Verified ProductTruth, rights cleared images, current platform rule scope, exact human approval | `internal_handoff`, `needs_changes` | No listing publish route; unverified claim never outward-ready |

Each GateDecision stores gate, actor identity, role, reason, `subject_version_hash`, source/Spec/Cost/Visual hashes, timestamp, decision, status. Editing any dependency marks affected decisions `stale`. No overwrite/delete of history.

## 3. Domain and persistence model

Use Python Pydantic v2 **strict** input/output models; SQLAlchemy tables with Alembic; JSON Schema generated and versioned for API consumers. Minimal V1 entities and essential fields:

| Entity | Required key data / invariant |
|---|---|
| `ProductCase` | id, tenant_id, owner, title, mode (`differentiation` in V1), market, marketplace, category, stage, status, active_revision, created_at, updated_at |
| `ProductBrief` | case_id, version/hash, problem, segment, target product and constraints; target costs/markets can be null; user authorization refs |
| `SourceDocument` | immutable bytes/object ID, sha256, source_kind, locator, original/captured times, rights, is_synthetic, product identity mapping |
| `Evidence` | id, tenant_id, case_id, source_id, source_locator row/page/URL, quote/claim, evidence_type, observed_at, quality flags, `is_synthetic` |
| `MarketSnapshot` | market, marketplace, category, currency, timezone, captured_at, source/evidence refs, measured-vs-estimated field statuses |
| `Insight` | id, hypothesis/observation label, supporting and contradicting evidence IDs, sample limitations, confidence_class (not scientific probability) |
| `Opportunity` | version, target user/problem, proposition, supporting evidence, alternatives, assumptions, falsifiability, stage and reviewer decision |
| `Concept` | version, parent opportunity, concept direction, design intent, user value, feature hypotheses, risk, visual refs; cannot claim real SKU |
| `ProductSpecVersion` | immutable version, concept_id, ordered features/specs, verification status per claim, source refs, no inferred product truth |
| `ProductTruthSnapshot` | only facts with individual source/status/rights/confirmation date and exact outward permission; provided to Engine as immutable snapshot |
| `CostInput`/`CostScenario` | currency, unit, normalized decimal money, provenance (`quote`, `historical`, `assumption`, `missing`), effective_date, explicit scenario inputs and outputs |
| `Feasibility` | scenario references, unknowns, risks, cash/investment requirements, assumptions, conditional recommendation |
| `GateDecision` | exact subject/hash/actor/role and decision, append-only, revocation when stale |
| `VisualTask`/`VisualRun` | references ProductCase/Concept/Spec/Truth, Engine project/brief/plan/batch/asset IDs, rights, plan budget, idempotency and approval snapshots |
| `LaunchPack` | immutable `internal_draft` by default, listing-copy sections, exact source/asset/Spec refs, outwards-claim checks, blockers |
| `Task`/`Attempt`/`AgentRun` | per work unit lease, version, retry, provider info, input fingerprint, cost/stop reason; never a second Case identity |
| `AuditEvent` | append-only actor/time/action/tenant/resource, redacted sensitive fields |

Schema rule: all IDs opaque and tenant-scoped; all dates ISO 8601 UTC with source timezone if relevant; quantities include unit, currencies ISO 4217; never coerce missing number to zero; original imported raw data retained hash. Distinguish returned source text from metadata `verified` status. Any synthetic input is visibly labeled, cannot satisfy real external validation.

### 3.1 Truth and inference lineage

`SourceDocument` → `Evidence (observed)` → `Insight (inferred)` → `Opportunity (hypothesis)` → `Concept (proposal)` → `ProductSpecVersion (proposal)` → optional **independently confirmed** `ProductTruthSnapshot (facts)`.

Prohibit arrows `GeneratedImage → VerifiedProductTruth`, `MockVisionQA → Certification`, `SyntheticReview → RealMarketDemand`, `OpportunityScore → BusinessFact`.

### 3.2 Evidence sufficiency

Compute observable quality signals: target market match, time window known, number of independent products/sources, duplicate ratio, presence of counter-evidence, category/variant matches, sample coverage, permissions. Return `sufficient_for_draft|needs_more_data|conflicted|unusable`, with reasons and missing fields. Fixed thresholds must be documented, configurable and treated as **workflow minimums**, never statistical proof. No aggregate demand quantification without actual licensed denominators.

### 3.3 Cost engine

`unit_contribution = net_sales_revenue_ex_tax - landed_product_cost - referral_fee - fulfillment - variable_storage - advertising_allocated - returns_allowance - other_variable_costs`.

Model `landed_product_cost = ex_factory + freight + tariff/duty + per-unit import/handling`; keep `fixed_rnd/tooling/sample/overhead` separately for investment analysis. Use `Decimal`, explicit currency/FX timestamp/assumptions and unit conversion; avoid double counting, choose one tax and fulfillment model per scenario. Missing required fields yield `null` contribution or labeled bounded scenarios, never false precision. Profitability/ROI decision belongs to human owner.

### 3.4 Compliance

Store `RuleSnapshot` with authority URL or uploaded document, jurisdiction, market, product scope, revision, effective date, expiry/review date, rule excerpt and hash. `unknown|not_applicable|needs_review|potential_issue|verified_by_human` (avoid `legally_compliant` as autonomous model claim). Base V1 does not bundle unverified Amazon or regulatory rules. A general checklist without current authoritative sources must be `needs_review`, not pass.

## 4. Component boundaries

```
Next.js Case UI / CLI / optional MCP
    → FastAPI strict endpoints + RBAC
    → ProductCaseService / EvidenceService / ApprovalService / ArtifactService
    → PostgreSQL business truth (SQLite in local test)
    → DB TaskManager leases + fencing / Redis ARQ wakeups
    → LangGraph ProductCase orchestration (checkpoint = cursor)
       ├─ deterministic Pydantic/validators/economics/rules
       └─ bounded Agents SDK runtime: Research, Product, Creative
              └─ read-only source, knowledge, product-spec tools
    → HTTP CreativeEngine adapter / fake adapter
          ↳ separate CreativeEngine DB + images + Worker + QA
    → immutable artifact references / AuditEvent / human gate
```

`CaseService` alone sets business stage/status. `TaskManager` only schedules and verifies, cannot approve product or infer success from API status. LangGraph resumes using stable workflow_run_id, but business truth lives in DB. ARQ queue is wake-up, not truth. CreativeEngine's own scheduler handles image attempts; LaunchCase only owns submitted VisualTask references, human business approvals and progress synchronization. No double image scheduler.

### 4.1 Agent structure and tools

- **ResearchAgent**: read-only source retrieval/normalization, market and VOC coding, contradictions; output exact evidence refs and sample limitations. Can signal `needs_input`.
- **ProductAgent**: propose opportunity/concept/spec drafts constrained by approved evidence and goals; cannot mark facts verified or approve decisions.
- **CreativeAgent**: produce structured `VisualIntent`, allowed changes and review suggestions; cannot call paid generation without approved plan/budget. Image execution is delegated.
- **Tool whitelist**: `list_case_sources`, `get_source_excerpt`, `search_approved_knowledge`, `list_evidence`, `read_product_spec`, `read_feasibility`, `propose_visual_brief` (proposal only). No default mail/purchase/publish/write platform tools.
- **Runtime controls**: per task budgets for wall clock, model tokens, tool calls and cost; prompt input/output schemas; immutable snapshots; fake SDK Model for tests. Agent context includes tenant-scoped authorized data only.

Skills canonical directories under `skills/`, each with `SKILL.md`, input/output schema, references, examples, acceptance fixtures. Suggested V1: `market-research`, `voc-analysis`, `opportunity-discovery`, `product-definition`, `concept-design`, `commercial-feasibility`, `launch-preparation`; `visual-task-planning` thin integration. Avoid duplicate editable copies under Codex/Claude install folders. Freeze Skill version/hash per Run.

### 4.2 CreativeEngine integration (verified project API, not guesses)

Expected local service: `http://127.0.0.1:4310`, API at `/v1`, `GET /v1/health` and `/v1/openapi.json` (verify actual runtime). Sequence:

1. Verify API/contract version and `product-concept` Skill availability. Fail closed on mismatch.
2. Create/find Engine project (LaunchCase stores opaque mapping; don't reach into Engine DB).
3. Import source assets with origin, rights, verification and sensitive data flags. Store Engine asset IDs in LaunchCase mapping; original bytes remain in own immutable source store.
4. Create Engine `ProductTruthSnapshot` **only** with verified factual claims and actual source IDs. Pure speculative concept may have no verified facts; follow Engine contract rather than inventing verification.
5. Save `CreativeBrief` with `source.system="launchcase"`, `external_id=<visual_task_id>`, workflow `product-concept` for design exploration; `ecommerce-listing` only for eligible verified SKU. Reference assets and structured changes must match provider API schema.
6. Request deterministic plan (`POST /v1/briefs/:id/plan`); inspect strategy, blocked reasons, immutable Skill/QA hash, cost estimate; do not submit blocked plan.
7. Require independent human **plan/budget/rights** approval, bind request to exact plan and provider config.
8. Submit `POST /v1/batches` with stable idempotency key, `budget_usd`, `authorize_paid=false`, `vision_review=false` in V1 default. Paid paths remain disabled unless explicitly authorized later.
9. Save remote receipt and ID; poll `GET /v1/batches/:id` / events with backoff; reconcile uncertain submissions by idempotency/remote state before any retry; no blind duplicate charge.
10. Read outputs, QA issues and source references; Engine asset review must be by authorized human, and LaunchCase stage-specific business review is distinct. Export only approved assets; never turn concept pixels into product truth.
11. Engine down or no authorized photos -> blocked VisualTask but PRD/research continues. Existing TradeCase consumer fixture is not sufficient for LaunchCase: add a new consumer contract suite.

Strict existing SKU listing must use reuse/compose and verified product photos as Engine currently enforces. Structure changes require separate concept identity. With synthetic fixture and Mock Provider, the asset is a **mock internal concept**; do not call it market-ready product imagery. `visual_task` and `asset` revision never updates factual evidence.

### 4.3 Versioned tasks and remote effects

For any effect (especially image service) persist: command, target, environment, payload digest, role authorization, idempotency key, attempt, remote receipt, reconciliation status. `RUNNING/UNKNOWN_REMOTE` after timeout must not automatically retry paid request. For known local failure, bounded retry and jitter allowed. File writes atomic and checksum verified. Use outbox only if adding external side effects in later version; V1 keeps them disabled.

## 5. Service APIs (new LaunchCase API; must implement, not existing APIs)

All endpoints `/api/v1`; strict OpenAPI and consistent `{error:{code,message,details?}}`, pagination, tenant isolation, RBAC and Idempotency-Key on writes. Proposed minimal set:

- `POST /product-cases`, `GET /product-cases`, `GET /product-cases/{id}`, `PATCH /product-cases/{id}/brief` with version check.
- `POST /product-cases/{id}/sources/import`, `GET /product-cases/{id}/sources`, `GET /sources/{source_id}` (metadata and authorization-gated original bytes).
- `GET /product-cases/{id}/evidence`, `/insights`, `/opportunities`, `/concepts`, `/spec-versions`, `/feasibility`.
- `POST /product-cases/{id}/runs/{research|opportunities|concepts|feasibility}` returning durable Task/Run ID; `GET /tasks/{id}`.
- `POST /product-cases/{id}/gates/{g}/decision` requiring `expected_subject_hash`, role and explicit decision; `GET /product-cases/{id}/gates`.
- `POST /product-cases/{id}/visual-tasks` (create structured proposal); `POST /visual-tasks/{id}/approve-plan`, `GET /visual-tasks/{id}`; `POST /visual-assets/{id}/review`, `GET /visual-assets/{id}`.
- `POST /product-cases/{id}/launch-packs` (internal draft), `GET /launch-packs/{id}`, `GET /launch-packs/{id}/export`.
- `GET /product-cases/{id}/events` SSE with event sequence replay or cursor; `GET /health`, `/capabilities` status.

Actual field names must be frozen by P0 API contract and schema generation before frontend work; do not duplicate endpoints for CLI/MCP. CLI proposed interface: `launchcase case create --brief`, `source import`, `run research|opportunities|concepts|feasibility`, `gate decide --file`, `visual plan|submit|status`, `export --format json|md` and `doctor`.

## 6. Frontend design system and accessibility

Next.js + TS. Reuse **methodology**, not hidden TradeCase UI implementation. Define compact visual tokens (colors, typography, spacing, status badges) and a reusable screen map before building. User flows: list cases, open Case, import authorized sources, inspect one evidence claim in original context, choose opportunity, compare concepts/Spec diff, cost scenarios, gate Inbox, image gallery QA and internal export. Preserve source citations and `synthetic` badges; unknown does not look like pass. Distinct human review versus machine QA statuses.

Implement responsive 390px and desktop; keyboard accessible reviews, errors and focus, no destructive actions without confirmation. Browser test must use real local API/DB and screenshot the actual render; no image-only prototype qualifies. If no approved design baseline, label visual conformance pending human confirmation.

## 7. Test strategy and verification

- `unit`: schemas, aliases, duplicate grouping, evidence graph, cost Decimal/unit/currency math, permission checks, immutable hash binding, stage logic.
- `integration`: SQLite/API/Agent Fake SDK, DB lease/fencing, checkpoint rehydration, event replay, isolation and file authorization.
- `contract`: OpenAPI snapshot, fixture schema compatibility, LaunchCase-to-CreativeEngine real local HTTP Mock contract, unexpected/additive response handling, version mismatch fail-closed.
- `scenario`: full offline fixture Mode B, evidence gaps, contradictions, fake quote, false certification claim, altered spec after approval, remote timeout, repeated submit, mock concept ready vs listing blocked.
- `e2e`: Next.js actual browser + API + DB, desktop/mobile, at least one complete reviewed candidate; **no claim of real user acceptance**.
- `operations`: Alembic migrate up/down, clean install/wheel, PostgreSQL+Redis smoke if available, backup/restore object hashes and interrupted workflow recovery, clean CI.

All test fixtures are explicitly synthetic. Preserve test logs without secrets; record actual exit codes and skipped tests. Live model/source/platform verification is distinct and not included in V1 offline acceptance.

## 8. Data retention, security and licensing

Treat reviews/competitor data as user-controlled imports or appropriately licensed read-only sources. No default logged-in scraping, site rule bypass, social platform private data import or third-party scraping account automation. Provide retention/delete dry-run, tenant purge, backup/restore notes. Control uploads by mime signature and actual decoded size; do not execute attachments. Block SSRF or filesystem path injection if future source readers added. Extracted review text and webpage content are untrusted data, not tool permissions.

Secrets in env/secret manager only, no secret in frontend, tests, logs or exported launch pack. Provide visibility/permissions rules for source content and internal supplier quotes. Author and user-supplied images need explicit reuse rights. Hosted CreativeEngine local mode is a trusted-single-user service, not a built-in enterprise multi-tenant auth service; LaunchCase enforces its tenant and asset mapping, does not expose Engine directly to arbitrary end users.

## 9. Full V1 Definition of Done

1. A fresh clone/install launches offline CLI and Web; schema migration works; docs/README self-contained.
2. A fully labeled synthetic Case flows: import → normalized evidence → VOC → opportunity → human G1 → concepts/spec → human G2 → conditional feasibility/G3 → mocked concept visual → QA/human asset review → internal draft pack, and stops rather than fabricating G4/G5.
3. Every nontrivial insight lists source and source limitations. Bad/missing data forces explicit review.
4. Different versions of spec, gate, source and image can be compared; stale approvals invalidated.
5. Agent is bounded, model failure leaves recoverable tasks; duplicate queue delivery never duplicates approved business changes; Engine uncertain paid state never auto-retries.
6. Commercial calculations exact under documented assumptions, unknowns are null, externally acquired fees/rules cannot be fabricated.
7. No real listing, ads, email, purchase, paid model or supplier call in default mode.
8. CLI/API/UI read and write the same source of business truth; per-tenant isolation tests pass.
9. `docs/DELIVERY_REPORT.md` includes commands, exit code, tested vs not tested, known blockers and case/output references.
10. No changes to TradeCase or CreativeEngine repos required to complete LaunchCase V1; any needed protocol change is documented as a separate proposal, not silently implemented in dependencies.
