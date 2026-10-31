# P8–P10 local release candidate

Base: `13bfd8ba088ab671978cfc5463f2626a58c6e563`. Code commits: `341bc332298ffe2a8808890b650127514071449e`, `5eb44ff384fe86027863847d0ddf30f41f62987d`. Branch: `codex/p8-p10-launchcase`. No remote mutation, private business data, paid call or deployment occurred.

The existing workspace now supports original SKU images and transparent cutouts, explicit unchecked rights confirmation, immutable safe previews, exact human source review, verified sample/fact/rule selection and strict CE HTTP composition. Insight reviewers can inspect source row/bytes/identity/variant and model/Skill/input/prompt versions without hidden model reasoning. Source/right/Spec/sample/rule changes invalidate old decisions and pack eligibility.

The fixed consumer validates scope, hashes, required QA and explicit USD cost. Null/invalid costs and ambiguous receipts never become free or trigger blind retries. Independent review closed synthetic-review escalation and incomplete source-manifest bypasses. Dataset export reuses existing pinned operator authorization, rejects mixed real data under synthetic authority and refuses incomplete manifests over 5000 sources.

Dedup now uses complete original rows. Two separately identified/date-stamped reviews with identical text no longer collapse; identical rows and repeated identical files still deduplicate. Existing originals and history are never rewritten. Historical proofs that no longer match current parsing remain unverified; regenerate from original evidence and obtain new review. Source-rule revision changes intentionally stale old packs. No new SQL migration is required; five existing migrations still upgrade/check and disposable downgrade/re-upgrade cleanly.

Single-host operations add scoped queue/lease/reconciliation alerts, owner token rotation/revocation and repeatable stopped-writer restore/rollback drills. See OPERATIONS.md and ops/staging.env.example. Optional PG/Redis readiness failed and is disclosed; no multi-host claim.

The final evidence set records 132 passed / 3 skipped backend cases, 11 actual CE HTTP cases, original-SKU browser E2E, existing desktop/mobile and G4/G5 browser regressions, build/lint/migration, clean wheel install and restore. Overlapping suites are not added as independent acceptance counts. All 17 LaunchCase planned IDs are mapped: 15 engineering passes and 2 genuine E3 BLOCKED_EXTERNAL. Production and business release remain HOLD.
