import secrets
from contextlib import contextmanager
from dataclasses import dataclass

from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError

from launchcase.application.intake import parse_import
from launchcase.domain.common import DomainError, digest, now
from launchcase.infrastructure.db import database
from launchcase.infrastructure.models import (
    Artifact,
    AuditEvent,
    BriefVersion,
    Evidence,
    Identity,
    ProductCase,
    Receipt,
    SourceDocument,
)
from launchcase.infrastructure.store import ObjectStore


@dataclass(frozen=True)
class Actor:
    id: str
    tenant_id: str
    role: str
    synthetic: bool = False


def row_dict(row):
    return {c.name: getattr(row, c.name) for c in row.__table__.columns}


class CaseService:
    def __init__(self, settings):
        self.settings = settings
        self.engine, self.sessions = database(settings)
        self.objects = ObjectStore(settings.data_dir)

    @contextmanager
    def write(self):
        with self.sessions() as s:
            s.info["writing"] = True
            if self.engine.dialect.name == "sqlite":
                s.execute(text("BEGIN IMMEDIATE"))
            try:
                yield s
                s.commit()
            except BaseException:
                s.rollback()
                raise

    def provision(self, tenant: str, name: str, role: str, synthetic=False):
        if role not in {"owner", "reviewer", "analyst", "agent", "viewer"}:
            raise DomainError("ROLE_INVALID", "Unsupported identity role")
        token = secrets.token_urlsafe(32)
        with self.write() as s:
            item = Identity(
                tenant_id=tenant, name=name, role=role, synthetic=synthetic, token_hash=digest(token.encode())
            )
            s.add(item)
            s.flush()
            actor = Actor(item.id, tenant, role, synthetic)
        return token, actor

    def authenticate(self, token: str):
        with self.sessions() as s:
            item = s.scalar(select(Identity).where(Identity.token_hash == digest(token.encode())))
            if not item:
                raise DomainError("UNAUTHORIZED", "Valid bearer identity required", 401)
            return Actor(item.id, item.tenant_id, item.role, item.synthetic)

    def require(self, actor, human=False):
        allowed = {"owner", "reviewer"} if human else {"owner", "reviewer", "analyst", "agent"}
        if actor.role not in allowed:
            raise DomainError(
                "FORBIDDEN",
                "This action requires an authorized human role" if human else "Read-only identity",
                403,
            )

    def get_row(self, s, model, actor, item_id):
        query = select(model).where(model.id == item_id, model.tenant_id == actor.tenant_id)
        row = s.scalar(query.with_for_update() if s.info.get("writing") else query)
        if not row:
            raise DomainError("NOT_FOUND", "Resource not found", 404)
        return row

    def case_row(self, s, actor, case_id, lock=False):
        q = select(ProductCase).where(ProductCase.id == case_id, ProductCase.tenant_id == actor.tenant_id)
        row = s.scalar(q.with_for_update() if lock else q)
        if not row:
            raise DomainError("NOT_FOUND", "ProductCase not found", 404)
        return row

    def command(self, actor, key, payload, fn):
        self.require(actor)
        if not key or len(key) > 180:
            raise DomainError("IDEMPOTENCY_REQUIRED", "A 1..180 character Idempotency-Key is required")
        hashed = digest(payload)
        try:
            with self.write() as s:
                receipt = s.scalar(
                    select(Receipt).where(Receipt.tenant_id == actor.tenant_id, Receipt.key == key)
                )
                if receipt:
                    if receipt.payload_hash != hashed:
                        raise DomainError("IDEMPOTENCY_CONFLICT", "Key was used for a different request", 409)
                    return receipt.result
                result = fn(s)
                s.add(Receipt(tenant_id=actor.tenant_id, key=key, payload_hash=hashed, result=result))
                return result
        except IntegrityError:
            # A concurrent transaction may have committed the same logical command.
            with self.sessions() as s:
                receipt = s.scalar(
                    select(Receipt).where(Receipt.tenant_id == actor.tenant_id, Receipt.key == key)
                )
                if receipt and receipt.payload_hash == hashed:
                    return receipt.result
                if receipt:
                    raise DomainError(
                        "IDEMPOTENCY_CONFLICT", "Concurrent key payload conflict", 409
                    ) from None
            raise

    def event(self, s, actor, case_id, action, data=None):
        self.case_row(s, actor, case_id, lock=True)
        seq = (
            s.scalar(
                select(func.max(AuditEvent.sequence)).where(
                    AuditEvent.case_id == case_id, AuditEvent.tenant_id == actor.tenant_id
                )
            )
            or 0
        )
        s.add(
            AuditEvent(
                tenant_id=actor.tenant_id,
                case_id=case_id,
                sequence=seq + 1,
                actor_id=actor.id,
                action=action,
                data=data or {},
            )
        )
        s.flush()

    def bump(self, case, stage="collecting_sources", status="needs_review"):
        case.revision += 1
        case.updated_at = now()
        case.stage, case.status = stage, status

    def artifact(self, s, actor, case, kind, data, dependency_hash):
        version = (
            s.scalar(
                select(func.max(Artifact.version)).where(
                    Artifact.case_id == case.id, Artifact.tenant_id == actor.tenant_id, Artifact.kind == kind
                )
            )
            or 0
        ) + 1
        item = Artifact(
            tenant_id=actor.tenant_id,
            case_id=case.id,
            kind=kind,
            version=version,
            data=data,
            sha256=digest(data),
            dependency_hash=dependency_hash,
        )
        s.add(item)
        s.flush()
        return item

    def create_case(self, actor, brief, key):
        data = brief.model_dump(mode="json")

        def run(s):
            case = ProductCase(
                tenant_id=actor.tenant_id,
                owner=actor.id,
                title=brief.title,
                is_synthetic=brief.data_policy.is_synthetic or actor.synthetic,
            )
            s.add(case)
            s.flush()
            s.add(
                BriefVersion(
                    tenant_id=actor.tenant_id, case_id=case.id, version=1, sha256=digest(data), data=data
                )
            )
            self.event(s, actor, case.id, "case.created", {"revision": 1})
            return row_dict(case)

        return self.command(actor, key, {"action": "case.create", "brief": data}, run)

    def list_cases(self, actor, limit=50, offset=0):
        with self.sessions() as s:
            return [
                row_dict(x)
                for x in s.scalars(
                    select(ProductCase)
                    .where(ProductCase.tenant_id == actor.tenant_id)
                    .order_by(ProductCase.created_at.desc())
                    .offset(offset)
                    .limit(min(limit, 100))
                )
            ]

    def get_case(self, actor, case_id):
        with self.sessions() as s:
            case = self.case_row(s, actor, case_id)
            brief = s.scalar(
                select(BriefVersion).where(
                    BriefVersion.case_id == case_id,
                    BriefVersion.tenant_id == actor.tenant_id,
                    BriefVersion.version == case.brief_version,
                )
            )
            return {**row_dict(case), "brief": brief.data, "schema_version": "1.0.0"}

    def revise_brief(self, actor, case_id, request, key):
        def run(s):
            case = self.case_row(s, actor, case_id, True)
            if case.revision != request.expected_revision:
                raise DomainError("STALE_SUBJECT", "Case revision changed", 409)
            case.brief_version += 1
            self.bump(case)
            data = request.brief.model_dump(mode="json")
            case.title = request.brief.title
            case.is_synthetic = case.is_synthetic or request.brief.data_policy.is_synthetic
            s.add(
                BriefVersion(
                    tenant_id=actor.tenant_id,
                    case_id=case_id,
                    version=case.brief_version,
                    sha256=digest(data),
                    data=data,
                )
            )
            self.event(s, actor, case_id, "brief.revised", {"revision": case.revision})
            return row_dict(case)

        return self.command(
            actor, key, {"action": "brief.revise", "case": case_id, **request.model_dump(mode="json")}, run
        )

    def import_source(self, actor, case_id, request, key):
        raw, rows = parse_import(request)
        sha = digest(raw)

        def run(s):
            case = self.case_row(s, actor, case_id, True)
            old = s.scalar(
                select(SourceDocument).where(
                    SourceDocument.tenant_id == actor.tenant_id,
                    SourceDocument.case_id == case_id,
                    SourceDocument.sha256 == sha,
                )
            )
            if old:
                return {
                    "source_id": old.id,
                    "sha256": sha,
                    "rows_imported": 0,
                    "rows_skipped": len(rows),
                    "warnings": ["duplicate_content"],
                }
            self.objects.put(raw)
            synthetic = any(r["is_synthetic"] for r in rows)
            src = SourceDocument(
                tenant_id=actor.tenant_id,
                case_id=case_id,
                filename=request.filename,
                sha256=sha,
                source_type=request.source_type,
                rights_status=request.rights_status,
                is_synthetic=synthetic,
                metadata_json={
                    "source_url": request.source_url,
                    "collected_at": request.collected_at or now(),
                    "rows": len(rows),
                },
            )
            s.add(src)
            s.flush()
            count, locators = 0, []
            for row in rows:
                exists = s.scalar(
                    select(Evidence.id).where(
                        Evidence.tenant_id == actor.tenant_id,
                        Evidence.case_id == case_id,
                        Evidence.fingerprint == row["fingerprint"],
                    )
                )
                if exists:
                    continue
                locator = f"{request.filename}#row={row['row']}"
                s.add(
                    Evidence(
                        tenant_id=actor.tenant_id,
                        case_id=case_id,
                        source_id=src.id,
                        source_locator=locator,
                        quote=row["quote"],
                        fingerprint=row["fingerprint"],
                        data=row["data"],
                        is_synthetic=row["is_synthetic"],
                    )
                )
                s.flush()
                count += 1
                locators.append(locator)
            self.bump(case)
            case.is_synthetic = case.is_synthetic or synthetic
            if request.source_type == "competitor":
                self.artifact(
                    s,
                    actor,
                    case,
                    "MarketSnapshot",
                    {
                        "marketplace": "amazon_us",
                        "country": "US",
                        "currency": "USD",
                        "source_id": src.id,
                        "rows": [r["data"]["raw"] for r in rows],
                        "is_synthetic": synthetic,
                    },
                    sha,
                )
            self.event(
                s, actor, case_id, "source.imported", {"source_id": src.id, "sha256": sha, "rows": count}
            )
            return {
                "source_id": src.id,
                "sha256": sha,
                "rows_imported": count,
                "rows_skipped": len(rows) - count,
                "warnings": [
                    "sample_not_representative",
                    *(["duplicates_removed"] if count < len(rows) else []),
                ],
                "locators": locators,
            }

        return self.command(
            actor, key, {"action": "source.import", "case": case_id, **request.model_dump()}, run
        )

    def list_scoped(self, actor, case_id, model, limit=100, offset=0, kind=None):
        with self.sessions() as s:
            self.case_row(s, actor, case_id)
            q = select(model).where(model.tenant_id == actor.tenant_id, model.case_id == case_id)
            if kind:
                q = q.where(model.kind == kind)
            return [
                row_dict(x)
                for x in s.scalars(
                    q.order_by(model.created_at, model.id).offset(offset).limit(min(limit, 5000))
                )
            ]

    def read_source(self, actor, source_id, content=False):
        with self.sessions() as s:
            src = self.get_row(s, SourceDocument, actor, source_id)
            data = self.objects.get(src.sha256)
            return data if content else row_dict(src)

    def replay_events(self, actor, case_id, after=0, limit=1000):
        with self.sessions() as s:
            self.case_row(s, actor, case_id)
            query = (
                select(AuditEvent)
                .where(
                    AuditEvent.tenant_id == actor.tenant_id,
                    AuditEvent.case_id == case_id,
                    AuditEvent.sequence > max(after, 0),
                )
                .order_by(AuditEvent.sequence)
                .limit(min(max(limit, 1), 5000))
            )
            return [row_dict(event) for event in s.scalars(query)]

    def change_rights(self, actor, source_id, request, key):
        self.require(actor, human=True)

        def run(s):
            src = self.get_row(s, SourceDocument, actor, source_id)
            case = self.case_row(s, actor, src.case_id, True)
            if case.revision != request.expected_revision:
                raise DomainError("STALE_SUBJECT", "Case revision changed", 409)
            if src.is_synthetic and request.rights_status == "authorized":
                raise DomainError("SYNTHETIC_SOURCE", "Synthetic content cannot be relabeled as genuine")
            src.rights_status = request.rights_status
            self.bump(case)
            self.event(
                s,
                actor,
                case.id,
                "source.rights_changed",
                {"source_id": source_id, "rights": request.rights_status},
            )
            return row_dict(src)

        return self.command(
            actor, key, {"action": "source.rights", "source": source_id, **request.model_dump()}, run
        )
