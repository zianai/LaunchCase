# LaunchCase V1 — Contract Seeds, Test Scenarios and Exit Criteria

**This file defines intended LaunchCase contracts, not existing production endpoints.** The `contracts/*.schema.json` files are executable **specification seeds**, not yet canonical Pydantic models. P0 is responsible for freezing the authoritative Pydantic-generated schemas and their compatibility tests. CreativeEngine's own 1.0.0 API is separate and must be queried from `/v1/openapi.json`.

## 1. Entity and reference contracts

### ProductCase create

`POST /api/v1/product-cases` with `Idempotency-Key` and `examples/synthetic-brief.json` (align final version in P0); response has `id`, `tenant_id`, `status`, `stage`, `brief_version`, `schema_version`, `created_at`. Same key+same digest -> same object; same key+different digest -> 409.

### Source import

`POST /api/v1/product-cases/{id}/sources/import` accepts a bounded multipart/file stream or documented JSON wrapper, `source_type`, `rights_status`, `is_synthetic`, time/locale and duplicate policy. Response includes `source_id`, byte SHA256, rows imported/skipped, warnings and a stable locator for each evidence. Source original is immutable. Duplicate content does not silently multiply market evidence.

### Evidence, Insight and Opportunity

- Evidence `source_id` plus original row/excerpt and timestamp; no unsupported actual demand percentages.
- Insight stores `supporting_evidence_refs` and `contradicting_evidence_refs`; `status` is `observed|inferred|hypothesis`, `sample_limitations` required for derived claims.
- Opportunity stores alternatives, explicit assumptions, testable success/failure conditions, `data_sufficiency_status`; without evidence → `needs_more_data`.

### Gate decision

`POST /api/v1/product-cases/{id}/gates/G2/decision` example:

```json
{
  "schema_version": "1.0.0",
  "decision": "select",
  "subject_type": "concept",
  "subject_id": "concept-002",
  "expected_subject_hash": "<sha256: derived from frozen, current concept/spec/source versions>",
  "reason": "Approved for sample evaluation only; dimensions remain unverified"
}
```

Authenticated server role/actor is always taken from auth context, never trusted from `reviewer` field supplied by the model. If subject digest mismatches, return 409 `STALE_SUBJECT`; if unauthorized, 403; if required evidence missing, 422/409 `GATE_BLOCKED`. Gate decisions recorded append-only.

### VisualTask to CreativeEngine

LaunchCase owns a `VisualTask` with a frozen ProductCase/Concept/Spec/rights snapshot. The Engine owns a separate `project_id`, `brief_id`, `plan_id`, `batch_id`, `asset_id`, `export_id`. The client performs these mapped steps, **never** writes Engine SQLite:

```
GET  /v1/health
POST /v1/projects
POST /v1/assets/import
POST /v1/truth-snapshots  (only if eligible confirmed facts; contract-dependent)
POST /v1/briefs
POST /v1/briefs/{id}/plan
POST /v1/batches         (authorized plan, stable idempotency)
GET  /v1/batches/{id}
POST /v1/assets/{id}/review (human-only)
POST /v1/exports
```

`workflow=product-concept` for concept iterations; `workflow=ecommerce-listing` only after verified SKU and required assets. `source.system=launchcase` and `source.external_id=<visual_task_id>`. If Engine endpoint/fields don't match version 1.0.0 verified runtime, stop with actionable integration error. Do not spoof `ProductTruthSnapshot` facts from concept or mock imagery.

Remote request states: `draft→plan_ready→awaiting_plan_review→submitted→running→qa_pending→awaiting_asset_review→approved|rejected`, with orthogonal `needs_input|blocked|reconciling|cancelled|failed`. `reconciling` prevents another paid submit until receipt reconciliation.

### LaunchPack

`LaunchPack` defaults `audience=internal`, `status=draft`, `publishable=false`, `publication_action=unavailable`; contains section version hashes, explicit unresolved claims, links to approved internal visual assets and mandatory open reviews. It is **not** an Amazon listing post body for publication. External-ready flags only when human and actual product rule evidence support them; V1 has no external publish endpoint.

## 2. Required tests (run, do not just list)

| ID | Test case | Expected observable outcome | Main stage |
|---|---|---|---|
| LC-T01 | Valid synthetic review and competitor imports | Stable row locators, original SHA, tenant link; Case created | P1 |
| LC-T02 | Same CSV imported twice / duplicate comments | No double count; duplicate flagged, deduplicated analytics | P1/P2 |
| LC-T03 | Review row contains prompt injection | Stored as source data; Agent tool permissions unchanged; no outbound action | P2 |
| LC-T04 | Contradictory statements from different variants | Conflict preserved and explanation shows variant matching uncertainty | P2 |
| LC-T05 | 3 synthetic reviews only / biased sample | Opportunity tagged needs_more_data; no market percentage claims | P2 |
| LC-T06 | Missing source URL or unsupported quote locator | Evidence cannot become verified; linked assertion blocked | P1/P2 |
| LC-T07 | Concept selection and subsequent Spec revision | Old G2 subject hash stale; unauthorized self-approval rejected | P3 |
| LC-T08 | Same Task delivered twice / two Workers contend | One effective lease and one durable result; no duplicate semantic action | P3/P6 |
| LC-T09 | Crash/restart after research and before approval | Stable task identity, checkpoint and current stage preserved | P3/P6 |
| LC-T10 | One cost component absent / currency mismatch | Unit contribution null or clearly labeled conditional scenario; no silent zero | P5 |
| LC-T11 | Supplier quote expired or assumption revised | Gate G3 stale or needs_review; historic decision retained | P5 |
| LC-T12 | Fake concept photo mistakenly requested as actual Listing | Engine strict fidelity blocks, `internal_only` remains; no factual upgrade | P4/P5 |
| LC-T13 | Visual plan is approved but asset has not been reviewed | Asset cannot be exported as approved; internal proposal status pending | P4 |
| LC-T14 | Remote batch submission times out with ambiguous receipt | Task enters reconciling; no new chargeable request without verified outcome | P4 |
| LC-T15 | CreativeEngine service unavailable | VisualTask blocked, product research/spec still accessible | P4 |
| LC-T16 | Paid model disabled, Oracle credentials absent | FakeAgent/Mock image local workflow succeeds, external paid calls = 0 | All |
| LC-T17 | No real sample test / unknown certification | G4/G5 cannot pass; internal LaunchPack allowed with blockers | P5/P6 |
| LC-T18 | Tenant B reads tenant A private source/quote | Denied at service, API, image mapping and event scope | P1/P6 |
| LC-T19 | Revoked image rights / changed ProductTruth | Previously approved material no longer current external-ready; diff visible | P4/P5 |
| LC-T20 | UI real browser desktop + 390px with API and DB | Import → evidence drilldown → concept review → mock visual → export works | P6 |
| LC-T21 | Source file path traversal, symlink, malformed file | Safe reject, no arbitrary read, no partial ghost data | P1 |
| LC-T22 | Mock result or synthetic source mislabeled real | Strict validator catches any false real/live/approved assertion | P6 |
| LC-T23 | Retained source asset hash differs from stored object | Audit/QA blocks export and alerts; cannot mark valid by UI | P4/P6 |
| LC-T24 | Actual persisted Case restored after backup/restart | Same immutable decisions/artifact refs still resolve; no re-sending | P6 |

All tests produce named fixture IDs/versions and expected statuses; do not require a fixed magic number of total tests. On a failure keep actual logs, fix and rerun, without rewriting history into a claim of first-time success.

## 3. Reproducible offline acceptance journey

Synthetic input: `examples/synthetic-brief.json`, `examples/synthetic-voc.csv`, `examples/synthetic-competitors.csv`, `examples/synthetic-quote.json`. Every source is labeled fake and generated solely for functional testing.

1. `ProductCase` created in differentiation Mode B with Amazon US target.
2. Import 24 synthetic review rows (including duplicates and variant conflicts), competitor rows and incomplete supplier cost.
3. Research creates traceable issue clusters with exact source row refs and sample-size caveat; no general-market demand claim.
4. Generate at least two differentiated but explicitly conceptual product directions, e.g., tool-free assembly vs compact modular storage, with risks and validation plan.
5. Human-role test actor selects one concept through approved G1/G2 test APIs (fixture approvals clearly `synthetic`, never count as real commercial approval).
6. Create versioned ProductSpec with unknown strength, size and material performance assertions; G3 feasibility reports missing inputs and scenario-only economics.
7. Create an authorized **internal concept** VisualTask using CreativeEngine Mock; retain Engine task ID and make QA + reviewer status distinguishable. If actual local Engine absent, run Fake Adapter and label no HTTP integration.
8. Generate an internal LaunchPack with chosen concept, source-backed VOC appendix, risk register, missing-price warning, concept asset watermark and `awaiting_sample_validation` / G4 blocked state. No real Listing-ready assertion.
9. Show restart-safe state and identical hashes; strict validation checks every reference.

## 4. Phase report format to produce after every P-stage

```markdown
# Pn execution report
- Repository/worktree and base/head: ...
- Scope implemented: ...
- Paths/files changed: ...
- Contracts/migrations: ...
- Commands and actual exit codes: ...
- Tests passed/failed/skipped: ...
- Actual integration scope: offline / local-http / live: ...
- Safety/external effects: paid calls=?, site writes=?, supplier messages=?, listings=?
- Known blockers and workarounds: ...
- QA evidence/run refs: ...
- Next dependency: ...
- Commit SHA: ...
```

Report absence of a call as `0 observed in the isolated workload` only if instrumented; otherwise `not observed / unknown`, not a universal cost statement.
