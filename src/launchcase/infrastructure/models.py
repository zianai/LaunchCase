from sqlalchemy import JSON, Boolean, ForeignKey, Index, Integer, String, Text, UniqueConstraint
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
