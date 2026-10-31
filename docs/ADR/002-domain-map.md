# ADR 002 — Domain and canonical contracts

ProductCase 1:N BriefVersion, SourceDocument, Evidence, Task, GateDecision, VisualTask.
SourceDocument 1:N Evidence; Insight/Opportunity bind Evidence IDs. Concept binds approved
Opportunity; SpecVersion binds Concept. Feasibility binds Spec and CostInput sources.
VisualTask binds Concept/Spec/source revisions and maps opaque Engine IDs. LaunchPack freezes
source/spec/decision/visual hashes. AuditEvent is append-only and tenant-scoped.

All write commands use a tenant-scoped receipt: same key and payload returns the same result;
changed payload yields 409. Business updates and receipts share a transaction. Concurrent
case edits use revision CAS; source/spec/gate history is immutable. Derived approval freshness
is computed from its dependency snapshot, preserving the original decision.

API /api/v1, JSON wrapper source import (filename/content/source_type/rights/is_synthetic).
Strict input models reject unknown fields. Reads use bounded pagination. Raw bytes require
the same identity checks as metadata. CLI runs application services, never alternate logic.
