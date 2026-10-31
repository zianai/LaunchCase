# LaunchCase V1 delivery — local implementation

Workspace: `/Users/a/workspaces/AForeign Trade/LaunchCase`, local branch `codex/launchcase-v1`.
P0→P6 implemented in dependency order. Scope is the functioning offline evidence-to-internal-draft
workbench; genuine market/product validation and external launch readiness are not delivered claims.
Full phase commits, paths, commands, failures and limitations: `docs/PHASE_REPORTS/P0.md` through
`P6.md`. P6's implementation SHA is recorded in its phase report after committing the tested code.

## Actual result

Synthetic demo Case `59d7447e-f199-4056-8838-78ef2aeb6b2c`, Pack
`b671dc3e-c7fb-4596-8621-2c7db7b0cc03`, retained under `.launchcase/demo-001`.
3 original sources, 28 deduplicated evidence rows, 4 opportunities, 2 differentiated fixture
concepts, versioned proposed Spec, incomplete/null costs, G1/G2/G3 synthetic decisions,
separately reviewed internal Mock asset, deterministic JSON/Markdown/ZIP exports. Graph stops
at G4; publishable=false. The strict validator resolves original rows, cross-document references,
source/artifact/asset hashes and rejects false live/real/sample labels.

Actual Next.js browser operations call the FastAPI/database: create/import/citation drilldown,
SDK Fake research, opportunity/concept/feasibility reviews, approved plan execution, independent
asset review and pack export. The UI has no canned finished-case data. CLI calls the same services.

## Executed verification

- Final backend suite with isolated HTTP Engine enabled: **52 passed, 1 skipped**. The skip is
  PostgreSQL/Redis; its separate Docker run is **1 passed**. These are 53 unique backend tests.
- Browser: **3 passed**, including full1440px and390px workflows, no page JS errors, no document
  overflow, overview axe WCAG2A/2AA/2.1AA zero violations and proxy boundary checks.
- Ruff check/format, compileall, doctor, frozen uv install, npm ci/typecheck/format/build: exit0.
- Five Alembic revisions upgraded, checked for metadata drift, downgraded on a disposable DB,
  then upgraded again: exit0. No real database was downgraded.
- Built wheel and installed in a fresh virtual environment outside the repository with cached
  dependencies and network disabled; packaged migrations/Skills/Mock raster, complete demo and
  strict validation: exit0. A preliminary run needed permitted package downloads to fill cache.
- SQLite business/checkpoint/Mock/object backup and restore regenerated identical export bytes.
  PostgreSQL migration/concurrent receipt/lease and actual Redis ARQ recovery passed in isolated
  uniquely named containers; no production PostgreSQL backup or load/SLA test is claimed.
- Actual isolated CreativeEngine1.0.0 HTTP used Mock provider only, zero budget/paid false/vision
  disabled. The existing Engine service at4310 was read-only; test writes used separate4311/data.
- Login audit fail0/warn4, final workbench audit fail0/warn6. Fresh-context paired design reviewer
  preferred the final candidate; token/spacing warnings and remaining density limits are retained.
  This is not human design approval. `design/render-manifest.json` binds exact rendered bytes.

Reproducible command/output index: `docs/evidence/P6/command-index.json`. Earlier failures were
kept: initial login proxy origin check, audit's unauthenticated probes, clean-install cache/path
issues, an incorrectly named CLI error expectation, and PostgreSQL bootstrap readiness race.
Each was investigated and a corrected run retained. ARQ emits an upstream close() deprecation
warning; it does not change the passed recovery result. CI workflow is configured, not remotely run.

## Boundaries and residual work

Fake SDK themes/concepts are functional pet-furniture fixtures, not live research quality.
No real customers, suppliers, samples, current regulatory applicability, seller data, conversion
or sales were tested. G4 rejects synthetic samples/actors. G5 external-readiness and publishing
remain unavailable. No paid model/image provider, supplier message, purchase, listing or ad action
was invoked by this implementation. Fake SDK/Mock workload counters show zero paid calls;
this statement is scoped to this isolated workload, not any other running local projects.

Real-SKU reference-image import/truth-to-Engine Listing flow, optional MCP, mode A/C, external SSO,
horizontal graph persistence and production hardening remain explicit extensions. Source asset
IDs are rejected rather than silently accepted. Document read envelopes use immutable JSON, not a
separate strict response model for every domain kind. See CAPABILITY_STATUS and ADR003.

TradeCase and both CreativeEngine checkouts have unchanged HEAD, full porcelain status and
tracked diff SHA compared with the P0 capture (P6-*-after.json). Their pre-existing dirty changes
were preserved. No upstream source/database edits, remote repository creation, push, release tag
or deployment was performed. The incorrect sibling LaunchCase directory was relocated; the
working repository lives only under AForeign Trade as requested.

## Start/recover

See README and OPERATIONS. Web3310/API8810 are loopback. The delivered running browser environment
uses `.launchcase/browser`; fixture token file `.launchcase/browser-token` is local/private/ignored.
To create a fresh environment use CLI init-db/auth provision and the normal quickstart.
Demo exports are internal/synthetic and retained locally, not published or sent anywhere.
