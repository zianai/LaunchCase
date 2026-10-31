# Evidence-grade capability status

| Capability | Status | Actual scope / limitation |
|---|---|---|
| Independent workspace, contracts, five migrations | implemented / tested_offline | Local Git; no remote/push/deploy; upstream audited read-only |
| ProductCase, originals, provenance, rights, dedup | tested_offline | CSV/JSON/TXT/MD, immutable hashes, exact row locators, tenant isolation |
| Agent SDK + Skills + VOC/opportunities | tested_offline | Actual SDK Runner with deterministic local Model; fixed fixture themes, not live model research |
| Concepts/Spec/G1/G2 | tested_offline | Two fixture directions, append-only revisions/diffs, exact review hashes, stale/agent rejection |
| LangGraph + TaskManager | tested_offline / tested_local_http | SQLite checkpoints; DB leases/fencing/attempts, real PostgreSQL+Redis/ARQ smoke |
| Visual plan/Mock assets/separate reviews | tested_offline / tested_local_http | Persistent fake and actual isolated CreativeEngine1.0.0 HTTP Mock; no paid image generation |
| Image reference upload / verified SKU Listing | blocked | `source_asset_ids` must be empty; listing intent rejected; no source-rights bypass |
| Unit economics and quote provenance | tested_offline | Decimal, FX/unit scenarios, null costs, matching quote field check, expiry; no current platform fee claims |
| Sample/Rule/Truth attestation | tested_offline / browser tested | Sample identity/method, exact values/excerpts, source rights, scoped official URL and expiry; no actual sample/compliance validation |
| G4/G5 internal business handoff | tested_offline / browser tested | Real-mode contracts tested only in isolated fictional databases; exact pack/rules/risk ownership, invalidation and receipt ZIP. Actual business approval remains absent; publication unavailable |
| Internal LaunchPack JSON/MD/ZIP | tested_offline | Exact manifest; approved internal assets; stale/tampered objects block export; no auth tokens/config serialized |
| Next.js / CLI / accessibility | tested_offline + local browser/API | Real API/DB journey at1440px and390px, keyboard/focus/axe checks; English fixture content in Chinese UI |
| Installation / backup/restore / deletion | tested_offline | Clean wheel resources and cached install, SQLite hash-preserving restore; external backups/exports excluded from purge |
| Optional MCP / mode A / mode C | not_started | Explicit future extensions, not selectable complete workflows |
| Real models, supplier/seller integration, publication | not_started / unavailable | No authorization, paid integrations, messages, buying, listings or ad calls |
| Design acceptance / target-user outcomes | pending / not_measured | Agent provisional design, independent screenshot review; no human visual approval, sales or conversion validation |

Current boundaries: single-host deployment, local bearer provisioning, local SQLite graph cursor,
not all document read envelopes are separate Pydantic response classes, no real-SKU truth-to-Engine
image path. Browser lists are bounded; large-scale search/virtualization/load tests are future work.
SDK fake and supplied fixtures validate orchestration and guardrails, not business output quality.
