# ADR 001 — Independent LaunchCase and responsibility boundaries

Accepted for local implementation, 2026-10-30. Direct user instruction authorizes P0–P6;
the handoff's historical statement that only a plan was authorized is superseded.
Workspace corrected by direct user instruction to `/Users/a/workspaces/AForeign Trade/LaunchCase`.
No remote repository, push, deployment or paid service is authorized.

Use Python/FastAPI/Pydantic v2, SQLAlchemy/Alembic, LangGraph SQLite checkpoints,
OpenAI Agents SDK with a deterministic local Model, DB leases with fencing, and Next.js.
Canonical strict API contracts live in Python and generated OpenAPI/JSON Schema. Skills
live in `skills/`, packaged as wheel resources. No source code copied from upstream.

CaseService owns business state. LangGraph owns sequencing/interrupts; persisted checkpoints
are cursors, never approval authority. TaskManager owns durable work and retries. Redis/ARQ
may wake it; no queue message owns business state. Engine owns image workers and QA.
Concepts/specs are proposals; only independently supported source attestations can yield truth.
Human-role test fixtures are synthetic, never commercial approvals. G4/G5 fail closed.

Local API identities are hashed bearer tokens with tenant and role; browser uses a same-origin
server proxy and an HttpOnly session. No caller-controlled tenant/reviewer headers are trusted.
SQLite is the executable default. PostgreSQL uses the same models, with separate deployment
checks before any production claim. Frontend implementation follows after P5; P0 has no shell.

Actual continuity checker requires T-NNN-slug task IDs. The handoff-suggested LC-001-v1 failed validation; use T-001-launchcase-v1 and keep LC-Pn IDs for specification traceability.
