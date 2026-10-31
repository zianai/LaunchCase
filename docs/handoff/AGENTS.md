# LaunchCase — Agent Engineering & Continuity Instructions

## Authority and continuity
- Current explicit human instruction and platform safety controls outrank local specs.
- Repo-owned `project/state.yaml`, active task YAML and approved ADRs are durable project context; conversation memory is not authority.
- On session start: read this file; inspect `project/state.yaml` and `active_task`, its context/decision refs, current Git status and tests. Do not overwrite existing changes, protected paths, or user data.
- Use an independent LaunchCase `project_id` and schema/protocol compatible with the actual installed project-continuity conventions. Do not copy TradeCase's task states blindly.
- Every significant code change must have reason, provenance, tests, commit and handoff record where needed. High-impact action needs explicit human authorization and exact subject/payload evidence.

## Core philosophy
1. ProductCase is an evidence-backed decision process, not an agent chat transcript.
2. Source-first; facts, inferences, hypotheses and decisions remain distinct.
3. One orchestrator per responsibility. CaseService owns lifecycle, LangGraph owns business graph, Task Manager owns leases/attempts, Agent SDK owns bounded research loop, Creative Engine owns image generation and image QA.
4. Skills define methods; data/knowledge is retrieved, versioned and cited; deterministic code validates schemas and computes economics.
5. Do not invent market demand, product specifications, legal compliance, seller performance, supplier quotations or manufacturing feasibility.
6. Human gates bind immutable versions; edits revoke affected approvals. Model output never grants its own authorization.
7. Offline-first. Mock evidence and images always labeled; no paid calls or external effects by default.
8. Preserve backwards-compatible, stable, versioned interfaces. Prefer adapters to hidden shared database coupling.

## Allowed work in this handoff
- Create a new standalone LaunchCase local project, code, migrations, tests, fixtures, documentation, CLI/Web/MCP read-or-task-start actions.
- Read TradeCase and CreativeEngine as references; call CreativeEngine's existing HTTP contract only against authorized local Mock/testing endpoints.
- Run local tests and synthetic fixtures, record evidence. Avoid external accounts and paid models without explicit separate authorization.

## Denied by default
- Change TradeCase or CreativeEngine's source, database or remote branches.
- Create GitHub remote repositories, push commits, publish packages, purchase products, contact suppliers, send mail, launch listings/ads, scrape behind login, use paid AI APIs, or access private seller accounts.
- Reuse any image/LLM result as new product evidence.
- Label an internal draft as published, compliant, certified, real-model-tested or customer-validated.

## Security and isolation
- Tenant scope is enforced in every DB access, asset and event query; not just API route guards.
- Uploads bounded by size/type; never execute uploaded files. Sanitize/log redact; prevent path traversal, SSRF, XML/SVG misinterpretation, prompt injection and credential leaks.
- Use versioned `Idempotency-Key` and receipt reconciliation for chargeable submissions, never blind retry after unknown outcomes.
- Store immutable originals and content hashes; copies and AI-derived assets never overwrite sources.

## Evidence-grade status language
Use `implemented`, `tested_offline`, `tested_local_http`, `tested_live`, `blocked`, `not_started`. A mocked test is not a live-model test. A passing schema test is not a business quality validation. User/customer approval is not inferred from an assistant-run fixture.

## Reporting contract per phase
`git base/head` | changed paths | concrete commands with exit codes | test counts | source and API boundaries | what is NOT tested | new risk | suggested next action. Do not delete failing logs or record passing status for skipped tests.

## Visual conformance
Meaningful UI design requires an approved baseline or an explicitly pending human baseline, actual browser render screenshot, and exact-version review. HTML/JSX existing is not visual proof. Design approval and runtime correctness are separate claims.
