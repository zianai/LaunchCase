# P9 LaunchCase report

Tested code `5eb44ff384fe86027863847d0ddf30f41f62987d`. P9-LC-01/02/03, P9-CONTRACT-01, single-host P9-OPS and UI engineering are implemented. The workspace uses existing SKU/review endpoints and G4/G5 forms; additions provide tenant-safe image listing/preview and locatable provenance. Browser credentials never include the CE service token. The tab is now “图片与素材”; rights start unchecked and original review defaults to rejection.

Evidence-guided fixes include current rule revision binding, revoked visual content export denial, impossible citation rejection, independent review of generated assets, mixed-data pilot authorization, 5001-source refusal and synthetic-identity denial for real SKU plan/asset approval. The API cannot promote a generated asset to original/source ProductTruth. Null economics and unknown financial units remain blocked.

Frozen consumer `contracts/launchcase/1.0.0` runs standalone in this repository's CI, without CE source imports. Real integration uses an isolated CE subprocess/HTTP port and explicit test token. `evidence/rc-http` records 11 passes, including original strict composition, per-image review, tenant isolation and post-approval rights revocation. `evidence/rc-ui` records the full browser chain with 1440/390 screenshots and zero serious/critical accessibility violations. Existing G4/G5 and desktop/mobile regression evidence are `evidence/rc-ui-handoff` and `evidence/rc-ui-regression`.

`test_two_worker_processes_recover_one_expired_task` starts real worker processes after both pre-execution failure and abrupt process exit after persisted business output/checkpoint; one effective Research remains and human G1 is still required. This is a single-host SQLite test. The optional isolated PG/Redis probe failed readiness, retained at `evidence/infrastructure-first`; multi-host remains unverified.

All P9 LaunchCase planned IDs are mapped in acceptance-results.json. E1 SDK adapter tests use a deterministic injected Model; no paid real-model quality claim. UI conformance and human design approval remain pending despite engineering review.
