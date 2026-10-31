# LaunchCase → Codex handoff pack

This ZIP is a **build plan and fixture pack**, not implemented source code or a pull request.

1. Hand the whole ZIP folder to Codex in a new LaunchCase workspace.
2. Send Codex the text of `CODEX_KICKOFF_PROMPT.md`; it will read the implementation spec and P0–P6 phase plan.
3. It should audit existing TradeCase and CreativeEngine repositories read-only, then implement in the independent LaunchCase worktree, report exact commit IDs and test commands at each stage.

## Documents

- `CODEX_KICKOFF_PROMPT.md`: short message for starting Codex.
- `README_FOR_CODEX.md`: required operator behavior and scope.
- `IMPLEMENTATION_SPEC.md`: product/system/API/state/agent/image/evidence/commerce design.
- `PHASE_PLAN.md`: P0–P6 coding task breakdown, exits and tests.
- `CONTRACTS_AND_SCENARIOS.md`: detailed contract and failure testing matrix.
- `AGENTS.md`: initial project governance instructions.
- `docs/ARCHITECTURE_DECISIONS.md`: proposed ADRs; adopt after baseline verification.
- `docs/REFERENCES.md`: GitHub repos and stable document paths.
- `docs/PHASE_REPORT_TEMPLATE.md`: actual evidence reporting template.
- `contracts/*.schema.json`: JSON Schema seeds for Codex to validate/adapt into canonical Pydantic models.
- `examples/*`: clearly synthetic functional inputs; **not real market data**.

All example IDs are synthetic. Any `CreativeEngine` request must be translated using its actual 1.0.0 `/v1/openapi.json`, not blindly POSTed using LaunchCase-owned schema.
