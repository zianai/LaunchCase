# Local operations and recovery

V1 is a loopback, single-host workbench. Do not expose the local provisioning mechanism publicly.
No production deployment, load/SLA, external SSO or horizontal checkpoint backend was validated.
Keep data directories private (OS permissions), outside Git and backed up under your own access
control. The application does not automatically encrypt SQLite, objects or backups.

## Configuration

| Variable | Default / meaning |
|---|---|
| `LAUNCHCASE_DATA_DIR` | `.launchcase` resolved from process cwd |
| `LAUNCHCASE_DATABASE_URL` | SQLite in that directory; optional PostgreSQL psycopg URL |
| `LAUNCHCASE_CREATIVE_ENGINE_MODE` | `mock`; `disabled` blocks visuals; `http` requires isolated Engine |
| `LAUNCHCASE_CREATIVE_ENGINE_URL` | `http://127.0.0.1:4311`; numeric loopback only |
| `LAUNCHCASE_CREATIVE_ENGINE_TOKEN` | server-only token for the isolated Engine |
| `LAUNCHCASE_TOKEN` | CLI identity, not an AI-provider key |
| `LAUNCHCASE_API_URL` | Next server upstream, default `http://127.0.0.1:8810` |

No paid-provider configuration is consumed. A real local HTTP Engine is still explicitly requested
with Mock, zero budget, paid authorization false and vision disabled. Never point this test at an
existing production Engine database. Adapter rejects redirects/non-loopback and schema mismatch.

## Processes and task recovery

Start API and Web as in README. No file import executes code or fetches source URLs. ARQ messages
are wakeups; database Task/Attempt rows own leases. A process crash can be recovered with
`uv run launchcase worker-once`; it processes up to 20 queued/expired tasks. A new fence invalidates
an old worker. Maximum 3 claims; expired final claims become failed/ATTEMPTS_EXHAUSTED. Review
failure and inputs before creating changed work; V1 has no arbitrary reset-to-queued endpoint.
Do not hand-edit gate/task rows to force progress.

Research tasks use 60-second leases and bounded Fake SDK runs. Real model work may exceed that;
a heartbeat/production worker policy must be designed before enabling live runners. Checkpoints
are SQLite local cursors even with PostgreSQL business storage. Use one application host.
ARQ adapter: `launchcase.workflow.worker.WorkerSettings` and `wakeup`; production Redis secrets,
service supervision and queue scheduling are deployment work, not this release's validated scope.

Visual unknown receipt: keep `reconciling`, call `sync`; adapter looks up the original plan's batch.
Never create a new paid/chargeable submission after an ambiguous timeout. `cancel` is explicit;
LaunchCase has no second image worker. Mock images and machine QA do not verify product truth.

## Backups and restore

Stop this LaunchCase API and all workers first. Copying business DB and checkpoints across stores
is consistent only while writers are stopped. Keep original files until restoration is verified.

```text
launchcase backup --out NEW_BACKUP_DIRECTORY
launchcase restore --source BACKUP_DIRECTORY --out NEW_DATA_DIRECTORY
```

SQLite backup uses SQLite backup API for business DB/checkpoint/Mock receipt stores and validates
content-addressed objects; manifest stores each file SHA256. Restore validates all paths/hashes
before writing to a new directory. Configure data/database paths to the restored directory and run
`launchcase init-db`, then read existing Case/Pack and compare export digests. Identity hashes are
restored, so securely retained operator tokens still work. Export files are regenerated from state.

PostgreSQL: stop writers, take `pg_dump` to protected storage plus checkpoints/Mock/object directory
and SHA manifest, restore into a new database, run migrations, validate before switching processes.
The built-in backup command rejects PostgreSQL. PostgreSQL backup/restore is documented but was
not executed here; the executed restore test covers SQLite and immutable objects.

Migrations: `launchcase init-db` or `alembic upgrade head`. Before upgrade preserve a stopped-writer
backup. For rollback prefer restoring the previous DB/object snapshot with the matching Git commit.
Only disposable databases were downgraded during verification; downgrading real data can discard
new tables. `ops/verify_migrations.py` tests all five revisions and metadata drift in isolation.

## Retention and deletion

Default: retain originals/immutable history; there is no timed automatic deletion. Owner-only
`launchcase retention` reports tenant row counts. Exact `--confirm-tenant ID` purges that tenant
from the current store, refuses active/unknown work, and deletes unshared content objects. It also
removes matching local graph threads and local Mock receipts. A local deletion journal allows
cleanup retry after a crash: a filesystem administrator can provision a new owner for that same
tenant and repeat the exact purge. Stop writers before any purge; keep no recoverable backups
if the intended policy is complete erasure. This is an explicit destructive operator command.

Separate lifecycle scope: already exported files, old backups, browser downloads and HTTP
CreativeEngine-owned data. The purge reports these exclusions and never deletes data from an
upstream Engine service. There is no automatic guarantee of forensic disk erasure.

## Reproducible checks

`ops/verify_infrastructure.py` creates only uniquely named `launchcase-p6-*` PostgreSQL17.6 and
Redis7.4.6 containers with random loopback ports, tests migrations/concurrent receipts/lease
contention/expired worker and duplicate ARQ wakeups, then removes only its containers.
No existing container, database or volume is reused.

HTTP test requires separately running authorized isolated Mock Engine on port4311 with the token
specified in `tests/test_visuals.py`; run `LAUNCHCASE_TEST_ENGINE_HTTP=1 uv run pytest -q`.
No HTTP test token is a real account credential. Engine's existing port4310 is never mutated.

For browser verification, start API with `LAUNCHCASE_DATA_DIR=.launchcase/browser`, migrate, create
one synthetic tenant owner and place only its token in `.launchcase/browser-token` with mode600.
Start the production Next build at3310; `npm run test:e2e --prefix frontend` creates fresh synthetic
Cases and retains screenshots. Failed traces may contain fixture credentials; traces stay ignored
in `.launchcase/` or `frontend/test-results/`, never commit them. Use a separate browser test tenant.

Reproduce the isolated HTTP Mock endpoint used here (requires the already-installed, inspected
CreativeEngine sibling; do not install/change its code or reuse its existing data directory):

```bash
cd '/Users/a/workspaces/AForeign Trade/creative-engine'
env -i PATH="$PATH" \
  CREATIVE_DATA_DIR='/Users/a/workspaces/AForeign Trade/LaunchCase/.launchcase/engine-http' \
  CREATIVE_API_TOKEN='launchcase-isolated-test-token' PORT=4311 \
  node --import tsx apps/server/index.ts
```

This token is solely an isolated localhost test credential, not a provider key. The clean environment
excludes paid-provider credentials. Stop only this process when done; do not stop the existing4310 service.
