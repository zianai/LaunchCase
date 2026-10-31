# P8 LaunchCase report

Code subject `5eb44ff384fe86027863847d0ddf30f41f62987d`; baseline `13bfd8ba088ab671978cfc5463f2626a58c6e563`. P8-00 is captured in ../post-p7/BASELINE.md and P7_DELTA_REGISTER.json. Protected P7/handoff history has no diff. Original worktrees were not modified.

P8-LC-01/02 engineering is implemented: exact-row dedup, original evidence identity/variant/date retention, citation validation independent of model claims, source proofs, read-only versioned pilot export and accountable existing G1–G5. A specific P7 defect collapsed reviews with different IDs/dates but the same text; preserved failing/baseline observations justified the complete-row key. Three real cases, a real sample, paired human baseline and two independent reviewers were not available or authorized, so their business work remains BLOCKED_EXTERNAL.

Reused Agent SDK, LangGraph, TaskManager, Skills, sources and existing authorization. No second orchestrator, shared DB or new authorization issuer. Synthetic export is labeled; any non-synthetic source, mixed case or non-synthetic case requires the exact pinned data grant. Synthetic grant context is refused for real data; absent review metrics are null/not_evaluable. Export over 5000 sources fails explicitly.

Validation: `evidence/rc-backend/result.json` records exact command `.venv/bin/python -m pytest -q`, exit 0 and 132 passed / 3 skipped. P8-T016/017/018 map to exact nodes in acceptance-results.json; P8-T019 is blocked. Source and model dates are evidence, not market prevalence. No claim of genuine business usefulness, time savings, actual model billing or human approval is made.
