# Acceptance traceability

All inputs below are synthetic fixtures. `tested_offline` means local code/SDK Fake/Mock, not
real market, engineering or legal validation. The isolated HTTP Engine uses its Mock provider.
Default pytest skips the HTTP and Docker tests; the delivery report records their separate runs.

| ID | Executed evidence / test | Scope |
|---|---|---|
| LC-T01 | `test_idempotency_and_payload_conflict`, `test_exact_row_provenance_duplicate_and_conflict_preserved` | Original bytes/hash; duplicate import and duplicate row |
| LC-T02 | `test_idempotency_and_payload_conflict`, `test_exact_row_provenance_duplicate_and_conflict_preserved` | Duplicate CSV and comment rows do not double count |
| LC-T03 | `test_real_sdk_fake_model_citations_injection_and_conflicts` | Injection remains inert source data; Fake SDK tools only |
| LC-T04 | Same test, exact row preservation | Variant contradictions retained, no majority-vote truth |
| LC-T05 | `test_small_sample_requests_input` | Three reviews → needs_input; no category percentage |
| LC-T06 | `test_size_unicode_and_traversal`, strict original-row validation | Missing date/identity flagged; no automatic verified status |
| LC-T07 | `test_spec_revision_stales_g2_preserves_history_and_rollback`, `test_stale_hash_and_agent_self_approval` | Current hash/role guards and immutable revision |
| LC-T08 | `test_lease_contention_fencing_and_recovery`, infrastructure test | SQLite and actual PostgreSQL lease race; duplicate ARQ wakeup |
| LC-T09 | `test_checkpoint_restart_duplicate_delivery` | Persisted LangGraph cursor and single semantic result |
| LC-T10 | `test_missing_not_zero_and_unknown_currency`, `test_currency_unit_fx_validity` | Null contribution, currency/unit rules |
| LC-T11 | `test_quote_change_stales_g3_and_pack`, `test_source_id_cannot_launder_invented_quote` | Expiry and original quote field binding |
| LC-T12 | `test_listing_blocked_and_version_mismatch` | Mock/concept cannot become Listing |
| LC-T13 | `test_plan_review_separate_asset_review_and_duplicate_submit` | Unreviewed asset not approved for export |
| LC-T14 | `test_unknown_receipt_no_resubmit_and_reconcile` | Simulated accepted-timeout, reconcile original receipt |
| LC-T15 | `test_engine_failure_does_not_block_product` | Fake Engine failure; product still readable |
| LC-T16 | `test_full_demo_strict_validator_and_false_label`, clean wheel journey | Local deterministic Model/Mock only, instrumented run counters |
| LC-T17 | `test_synthetic_sample_rejected`, `test_internal_pack_graph_stops_g4_and_never_publishable` | G4/G5 blocked; internal draft allowed |
| LC-T18 | `test_tenant_checks_service_api_source_events`, visual test, SSE reconnect test | Cross-tenant source, image, events denied |
| LC-T19 | `test_revocation_stales_downstream_and_sse_replay`, `test_stale_spec_or_config_blocks_plan` | Source/spec/config invalidates decisions; source-image upload unavailable |
| LC-T20 | `frontend/tests/workbench.spec.ts` | 1440px/390px full real Web/API/DB journey, axe and overflow |
| LC-T21 | `test_malformed_no_partial_import`, `test_size_unicode_and_traversal`, request body limit test | Path/symlink/type/size controls |
| LC-T22 | `test_full_demo_strict_validator_and_false_label` | False live/synthetic/approval labels rejected |
| LC-T23 | `test_hash_tamper_blocks_read`, `test_asset_hash_tamper_blocks_review`, strict row tamper test | Changed source/object/hash/row blocks validation |
| LC-T24 | `test_backup_restore_same_hashes_and_decisions` | SQLite restore regenerates byte-identical internal JSON |

Additional boundaries: exhausted final lease becomes terminal; CLI cannot submit before exact plan
review; body cap applies without Content-Length; event replay works beyond sequence6000; schema
version mismatch and unbounded decimal inputs rejected. All test names live in `tests/`.

Workflow-minimum sufficiency is five dated reviews across two identities. This is documented in
Skills and code, and is not a population-representative sampling threshold. Fixed fixture themes
and concept directions are deliberately marked as deterministic tests, not general AI capability.
