# API and CLI contract

Canonical OpenAPI: `docs/openapi.json`; running endpoint `GET /api/v1/openapi.json`.
Strict request schema version is `1.0.0`, unknown fields/versions rejected. Dates have explicit
source/UTC handling, null costs remain null. All data endpoints require `Authorization: Bearer …`;
only health, capability description and OpenAPI are public. Identity determines tenant/role.
No tenant, actor or approval identity comes from a caller-supplied header.

Mutation headers: `Idempotency-Key: <unique-logical-request>`. Reuse exactly for the same
payload. Changed payload → 409. Spec/Brief/gate updates additionally compare the displayed
revision/hash. Errors use `{ "error": { "code": "…", "message": "…" } }`; validation details
include field paths/types, never input text. Backend request limit 2 MiB; imported UTF-8 file
limit 1 MiB / 5,000 rows; Web proxy envelope limit 1,500,000 bytes.

| Purpose | Route under `/api/v1` |
|---|---|
| Cases/Brief | `POST/GET /product-cases`, `GET /product-cases/{id}`, `PATCH …/brief` |
| Sources | `POST /product-cases/{id}/sources/import`, `GET /sources/{id}[/content]`, `PATCH …/rights` |
| Evidence/derived records | `GET /product-cases/{id}/{sources,evidence,insights,research,opportunities,concepts,spec-versions,feasibility,truth,rules,activity}` |
| Tasks | `POST /product-cases/{id}/runs/{research,opportunities,concepts,feasibility,launch_draft}`, `GET /tasks/{id}` |
| Gates | `GET /product-cases/{id}/gates`, `GET …/gates/{gate}/subject/{subject_id}`, `POST …/gates/{gate}/decision` |
| Spec | `POST /product-cases/{id}/concepts/{concept_id}/spec-versions`, `GET …/spec-diff?left=…&right=…` |
| Economics/facts | `POST /product-cases/{id}/feasibility`, `POST …/sample-attestations`, `POST …/rule-attestations` |
| Visual | `POST/GET /product-cases/{id}/visual-tasks`, `GET /visual-tasks/{id}`, `POST …/{approve-plan,submit,sync,cancel}` |
| Asset | `GET /visual-assets/{id}[/content]`, `POST …/review` |
| Pack | `POST/GET /product-cases/{id}/launch-packs`, `GET /launch-packs/{id}`, `GET …/export?format=json\|md\|zip` |
| Event replay | `GET /product-cases/{id}/events?after=0`, or `Last-Event-ID` |

List routes support limit/offset where declared in OpenAPI. SSE is bounded persisted replay
(1,000 sequential events per response), not an infinite in-memory connection. Reconnect with the
last sequence; disconnect does not lose progress. Tenant lookup precedes event/asset/object access.

Roles: owner/reviewer can review; analyst/agent can perform bounded drafting but cannot grant
human approvals; viewer reads only. CLI identity provisioning requires local filesystem access.
Human-role automated fixtures remain `is_synthetic=true`. Revocation/spec edits invalidate
current decisions without deleting history. Asset approval is distinct from plan approval.

CLI emits JSON, including when `--json` is specified. `LAUNCHCASE_TOKEN` supplies an existing
identity. Put global flags before subcommands. Never paste the token into scripts committed to Git.

```text
launchcase doctor | init-db | worker-once
launchcase auth create --tenant ID --name NAME --role owner [--synthetic]
launchcase case create --brief FILE | case list | case status CASE_ID
launchcase source import --case ID --file FILE --type review --rights authorized
launchcase run research|opportunities|concepts|feasibility|launch_draft --case ID
launchcase gate decide --case ID --gate G1 --file exact-gate-request.json
launchcase spec history --case ID
launchcase concept compare --case ID
launchcase visual plan --case ID --file visual-request.json
launchcase visual status|submit|sync|cancel VISUAL_TASK_ID
launchcase visual approve-plan VISUAL_TASK_ID --file exact-review-request.json
launchcase visual review-asset ASSET_ID --file exact-review-request.json
launchcase export PACK_ID --format zip --out NEW_FILE
launchcase --idempotency-key LOGICAL_KEY <mutation-command>
```

No MCP server is exposed in V1 (optional in handoff). No CLI shortcut bypasses the same
application-service checks. Strict validators inspect the persisted synthetic demo and manifests;
they do not certify real market evidence or legal applicability.

G4/G5 additions and exact request fields: see [G4_G5_HANDOFF.md](G4_G5_HANDOFF.md).
