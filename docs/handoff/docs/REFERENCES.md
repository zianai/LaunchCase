# Reference paths and verification list

## Verified public repos at handoff time

TradeCase: https://github.com/zianai/TradeCase
- `main` docs: https://github.com/zianai/TradeCase/blob/main/README.md
- Architecture: https://github.com/zianai/TradeCase/blob/main/docs/architecture/adr-001-platform-boundaries.md
- Continuity: https://github.com/zianai/TradeCase/blob/main/AGENTS.md
- Visual branch: https://github.com/zianai/TradeCase/tree/codex/tradecase-visual-tasks
- Visual domain ADR: https://github.com/zianai/TradeCase/blob/codex/tradecase-visual-tasks/docs/architecture/adr-005-visual-domain.md
- Visual integration manual: https://github.com/zianai/TradeCase/blob/codex/tradecase-visual-tasks/docs/VISUAL_TASKS.md
- Visual validation report: https://github.com/zianai/TradeCase/blob/codex/tradecase-visual-tasks/docs/VISUAL_UPGRADE_REPORT.md

CreativeEngine: https://github.com/zianai/CreativeEngine
- API: https://github.com/zianai/CreativeEngine/blob/main/docs/api.md
- Architecture: https://github.com/zianai/CreativeEngine/blob/main/docs/architecture.md
- TradeCase adapter boundaries: https://github.com/zianai/CreativeEngine/blob/main/docs/tradecase-integration.md
- Skill authoring: https://github.com/zianai/CreativeEngine/blob/main/docs/skill-development.md
- Visual Task 1.0.0 fixture contract: https://github.com/zianai/CreativeEngine/blob/main/contracts/visual-task/1.0.0/contract.json
- HTTP OpenAPI (only when authorized local server running): http://127.0.0.1:4310/v1/openapi.json

## How to verify as Codex
1. Fetch current repo HEAD, branch, dirty state, dependency manifests.
2. Confirm `TradeCase` visual branch integration vs `CreativeEngine` 1.0.0 protocol and any drift. Existing 1.0.0 fixture is for **TradeCase consumer**; create LaunchCase-specific consumer tests.
3. Prefer `GET /v1/openapi.json` to guessed request fields. `source.system` should be `launchcase`, `external_id` a LaunchCase VisualTask ID.
4. Confirm that the stage can call `skills/product-concept` and (only after actual product confirmation) `skills/ecommerce-listing`. Do not route unverified concept to strict listing.
5. Never assume endpoint exists just because a planned name is listed here; implement and test LaunchCase-only endpoints separately.
