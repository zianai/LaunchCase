# P0 read-only baseline audit

Inspected 2026-10-30. Current independent workspace: `/Users/a/workspaces/AForeign Trade/LaunchCase`.
Original handoff bytes are preserved under docs/handoff; it is a build plan, not code.

| Reference | Actual inspected commit / state | Reuse |
|---|---|---|
| TradeCase GitHub main | 11147c12d21305862ad67a2bd439e7c486e06d5a; remote ls-remote verified | Responsibility boundaries, API/RBAC/lease patterns |
| TradeCase visual branch/local HEAD | 4b70f652f72ba82c0e03d5d05fd4cd1e43c687dd; dirty working tree | HTTP consumer pattern, separate plan/asset reviews |
| CreativeEngine GitHub main / clean sibling | cd90f64c7ab577ea029d35119f0ad6eba18e57ad | HTTP protocol 1.0.0 |
| CreativeEngine working source | f0ca0a437f9353c523d7c5bc1409fcf69a9d1c96; dirty | Read-only API docs/skills/runtime inspection |

Remote refs checked with git ls-remote. TradeCase remote-main ref and local visual ref inspected;
local branch named main is older unrelated upstream ancestry, not GitHub main. No fetch/reset.
Full pre-existing status and diff digests are in docs/evidence/P0-*-before.json.
Read AGENTS, state, platform/visual ADRs, VISUAL_TASKS and VISUAL_UPGRADE_REPORT,
runtime.py, pyproject, frontend package.json, Engine API/integration/architecture docs,
product-concept/ecommerce-listing Skills and visual-task/1.0.0/contract.json.

TradeCase: MIT, Python 3.11+, FastAPI 0.162.0, Pydantic 2.14.1, SQLAlchemy 2.1.6,
Alembic 1.20.1, LangGraph 1.2.18, Agents SDK 0.24.0, ARQ 0.28.0, Next 16.4.3.
These are declared versions, not claims of running upstream tests. Existing test totals
in upstream reports are historical and are not LaunchCase validation.
CreativeEngine package 0.1.0, API 1.0.0, Node >=24, Fastify 5.12.7, SQLite, React/Vite.
No root LICENSE was found in the inspected CreativeEngine tree: do not copy/distribute source.
The HTTP boundary needs no source copying or shared DB.

Actual localhost:4310 /v1/health responds schema_version=1.0.0, worker=false.
/v1/openapi.json captured in docs/evidence. No writes to that existing service.
P4 will run an isolated Engine instance with its data directory inside LaunchCase and Mock
provider, or report fake-only testing if unavailable. Never inherit provider secrets.

Reuse matrix: own ProductCase/Evidence/Spec/economics/schema/migrations/Skills/UI are newly
implemented; reuse SDK libraries by locked dependencies; reuse Engine only via HTTP.
No source, database, object or business-memory coupling. TradeCase source changes and
CreativeEngine first-round live receipts are out of scope.
