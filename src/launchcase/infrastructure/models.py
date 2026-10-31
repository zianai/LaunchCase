from sqlalchemy import JSON, Boolean, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from launchcase.domain.common import now, uid
from launchcase.infrastructure.db import Base


class Identity(Base):
    __tablename__ = "identities"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(String(100), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(30))
    synthetic: Mapped[bool] = mapped_column(Boolean, default=False)


class ProductCase(Base):
    __tablename__ = "product_cases"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(String(100), index=True)
    owner: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(200))
    stage: Mapped[str] = mapped_column(String(50), default="collecting_sources")
    status: Mapped[str] = mapped_column(String(30), default="needs_input")
    revision: Mapped[int] = mapped_column(Integer, default=1)
    brief_version: Mapped[int] = mapped_column(Integer, default=1)
    workflow_run_id: Mapped[str] = mapped_column(String(36), default=uid)
    is_synthetic: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[str] = mapped_column(String(40), default=now)
    updated_at: Mapped[str] = mapped_column(String(40), default=now)


class Scoped:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(String(100), index=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("product_cases.id"), index=True)
    created_at: Mapped[str] = mapped_column(String(40), default=now)


class BriefVersion(Scoped, Base):
    __tablename__ = "brief_versions"
    __table_args__ = (UniqueConstraint("tenant_id", "case_id", "version"),)
    version: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    data: Mapped[dict] = mapped_column(JSON)


class SourceDocument(Scoped, Base):
    __tablename__ = "source_documents"
    __table_args__ = (UniqueConstraint("tenant_id", "case_id", "sha256"),)
    filename: Mapped[str] = mapped_column(String(180))
    sha256: Mapped[str] = mapped_column(String(64))
    source_type: Mapped[str] = mapped_column(String(30))
    rights_status: Mapped[str] = mapped_column(String(30))
    is_synthetic: Mapped[bool] = mapped_column(Boolean)
    metadata_json: Mapped[dict] = mapped_column(JSON)


class Evidence(Scoped, Base):
    __tablename__ = "evidence"
    __table_args__ = (UniqueConstraint("tenant_id", "case_id", "fingerprint"),)
    source_id: Mapped[str] = mapped_column(ForeignKey("source_documents.id"), index=True)
    source_locator: Mapped[str] = mapped_column(String(250))
    quote: Mapped[str] = mapped_column(Text)
    fingerprint: Mapped[str] = mapped_column(String(64))
    data: Mapped[dict] = mapped_column(JSON)
    is_synthetic: Mapped[bool] = mapped_column(Boolean)


class Artifact(Scoped, Base):
    """Immutable versioned domain documents; typed payloads validated by their services."""
    __tablename__ = "artifacts"
    __table_args__ = (UniqueConstraint("tenant_id", "case_id", "kind", "version"),)
    kind: Mapped[str] = mapped_column(String(50))
    version: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    data: Mapped[dict] = mapped_column(JSON)
    dependency_hash: Mapped[str] = mapped_column(String(64))


class AuditEvent(Scoped, Base):
    __tablename__ = "audit_events"
    sequence: Mapped[int] = mapped_column(Integer)
    actor_id: Mapped[str] = mapped_column(String(100))
    action: Mapped[str] = mapped_column(String(80))
    data: Mapped[dict] = mapped_column(JSON)
    __table_args__ = (UniqueConstraint("tenant_id", "case_id", "sequence"),)


class Receipt(Base):
    __tablename__ = "receipts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(String(100))
    key: Mapped[str] = mapped_column(String(200))
    payload_hash: Mapped[str] = mapped_column(String(64))
    result: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(String(40), default=now)
    __table_args__ = (UniqueConstraint("tenant_id", "key"), Index("ix_receipt_tenant", "tenant_id"))


class Task(Scoped, Base):
    __tablename__ = "tasks"
    __table_args__ = (UniqueConstraint("tenant_id", "case_id", "kind", "input_hash"),)
    kind: Mapped[str] = mapped_column(String(40))
    input_hash: Mapped[str] = mapped_column(String(64))
    input_data: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(30), default="queued", index=True)
    lease_owner: Mapped[str | None] = mapped_column(String(100), nullable=True)
    lease_until: Mapped[float] = mapped_column(Float, default=0)
    fence: Mapped[int] = mapped_column(Integer, default=0)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)


class Attempt(Base):
    __tablename__ = "attempts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(String(100), index=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), index=True)
    fence: Mapped[int] = mapped_column(Integer)
    owner: Mapped[str] = mapped_column(String(100))
    started_at: Mapped[str] = mapped_column(String(40), default=now)
    status: Mapped[str] = mapped_column(String(30), default="running")
    __table_args__ = (UniqueConstraint("task_id", "fence"),)


class GateDecision(Scoped, Base):
    __tablename__ = "gate_decisions"
    gate: Mapped[str] = mapped_column(String(4))
    decision: Mapped[str] = mapped_column(String(30))
    subject_id: Mapped[str] = mapped_column(String(100))
    subject_type: Mapped[str] = mapped_column(String(40))
    subject_hash: Mapped[str] = mapped_column(String(64))
    dependencies: Mapped[dict] = mapped_column(JSON)
    actor_id: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(30))
    reason: Mapped[str] = mapped_column(Text)
    is_synthetic: Mapped[bool] = mapped_column(Boolean)


class VisualTask(Scoped, Base):
    __tablename__ = "visual_tasks"
    concept_id: Mapped[str] = mapped_column(String(36))
    request: Mapped[dict] = mapped_column(JSON)
    state: Mapped[str] = mapped_column(String(40), default="draft")
    dependency_hash: Mapped[str] = mapped_column(String(64))
    configuration_hash: Mapped[str] = mapped_column(String(64))
    plan: Mapped[dict] = mapped_column(JSON, default=dict)
    plan_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    plan_review: Mapped[dict] = mapped_column(JSON, default=dict)
    remote: Mapped[dict] = mapped_column(JSON, default=dict)
    submission_key: Mapped[str] = mapped_column(String(100), default=uid, unique=True)
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)


class VisualAsset(Scoped, Base):
    __tablename__ = "visual_assets"
    visual_task_id: Mapped[str] = mapped_column(ForeignKey("visual_tasks.id"), index=True)
    remote_id: Mapped[str] = mapped_column(String(160))
    sha256: Mapped[str] = mapped_column(String(64))
    identity: Mapped[str] = mapped_column(String(30), default="mock")
    qa: Mapped[dict] = mapped_column(JSON)
    review: Mapped[dict] = mapped_column(JSON, default=dict)
    __table_args__ = (UniqueConstraint("tenant_id", "visual_task_id", "remote_id"),)
