# G4/G5 verification — 2026-10-31

Base: `8009baaca05411d2277671dcc53dc655eec163f1`. Local changes only. No external account actions, paid calls or real business approvals.

| Check | Actual result |
|---|---|
| `LAUNCHCASE_TEST_ENGINE_HTTP=1 uv run pytest -q` | exit 0; 64 passed, 1 skipped (optional PostgreSQL test; not rerun in this change) |
| `uv run pytest tests/test_handoff.py tests/test_feasibility.py -q` | exit 0; 23 passed |
| `LAUNCHCASE_SCREENSHOT_DIR=docs/evidence/g4-g5/regression npm run test:e2e --prefix frontend` | exit 0; 3 passed, desktop/mobile original journey and proxy boundaries |
| `uv run python ops/seed_handoff_test.py` then `npx playwright test --config playwright.handoff.config.ts` in frontend | exit 0; 1 passed, real API isolated DB, G4/G5 full form flow, deferred decisions, receipt, ZIP, 1440/390px |
| `npm run build --prefix frontend` | exit 0; production build and TS pass |
| `npm run typecheck --prefix frontend` | exit 0 |
| `uv run ruff check .` and `git diff --check` | exit 0 |
| `uv run python ops/verify_migrations.py` | exit 0; five migrations upgrade/downgrade/reupgrade, no metadata drift |
| axe in live browser | no violations reported |
| skill deterministic static UI audit, final | exit 0; fail 0 / warn 5; inherited palette/spacing and small mobile targets remain nonblocking warnings |

First implementation test run found source URL access using an incorrect model attribute; corrected to metadata_json and reran. First browser run used an exact label matcher including select options; corrected to role/name and reran. Initial UI audit failed summary target size; increased summary targets to 44px and reran. The failing audit is preserved in `design/rounds/g4-g5/audit-first/`; final is `audit-final/`.

New backend cases exercise G4/G5 positive path in disposable fictional real-mode contract fixtures, idempotency, public-web sample rejection, invented values, future dates, wrong Spec, missing sample identity, rule source URL, tenant isolation, missing preparation, stale packs, source rights revocation, clock-driven rule expiry, new sample and preparation invalidation. Graph handoff completion rechecks exact approval. No test constitutes actual human sample testing, market demand validation, compliance approval or image rights verification.

Screenshots and runtime HTML in this directory are from the clearly titled TEST ONLY isolated case; it is separate from the user-facing synthetic demo database. The public FTC/CPSC excerpt files are genuine attributed references; their applicability to the product remains unreviewed outside software fixtures.

Effect-test rerun: user authorized fabricated samples/approvals for testing. Re-seeded a separate disposable DB, ran the full browser test (1 passed), and opened Case b2bcec1e / Pack f4cb6abc at port 3312 with TEST ONLY labels. No real sample or business validation. Port 3310 demo remains separate.
