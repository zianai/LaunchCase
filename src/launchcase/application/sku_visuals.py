"""Original SKU assets and version-bound eligibility; Engine still owns all image work."""

import base64
import io
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from PIL import Image
from sqlalchemy import select

from launchcase.application.products import ProductService
from launchcase.application.services import row_dict
from launchcase.domain.common import DomainError, digest, now
from launchcase.infrastructure.models import Artifact, SourceDocument, VisualAsset
from launchcase.validation import timestamp


def raster(raw):
    if not 0 < len(raw) <= 1024 * 1024 or not (
        raw.startswith(b"\x89PNG\r\n\x1a\n")
        or raw.startswith(b"\xff\xd8\xff")
        or (raw[:4] == b"RIFF" and raw[8:12] == b"WEBP")
    ):
        raise DomainError("UNSAFE_IMAGE", "Expected bounded JPEG/PNG/WebP original")
    try:
        with Image.open(io.BytesIO(raw)) as image:
            if (
                image.format not in {"PNG", "JPEG", "WEBP"}
                or image.width * image.height > 8_000_000
                or getattr(image, "n_frames", 1) != 1
            ):
                raise ValueError()
            image.verify()
        with Image.open(io.BytesIO(raw)) as image:
            image.load()
            alpha = image.convert("RGBA").getchannel("A").getextrema()
            return {
                "width": image.width,
                "height": image.height,
                "format": image.format,
                "transparent": alpha[0] < 255 and alpha[1] > 0,
            }
    except Exception as exc:
        raise DomainError("UNSAFE_IMAGE", "Image decode/size validation failed") from exc


class SkuVisualService:
    def __init__(self, service):
        self.service = service

    def upload(self, actor, case_id, request, key):
        self.service.require(actor, human=True)
        try:
            raw = base64.b64decode(request.data_base64, validate=True)
        except ValueError as exc:
            raise DomainError("UNSAFE_IMAGE", "Invalid base64") from exc
        meta = raster(raw)
        expected_format = {".png": "PNG", ".jpg": "JPEG", ".jpeg": "JPEG", ".webp": "WEBP"}
        if expected_format.get(Path(request.filename).suffix.lower()) != meta["format"]:
            raise DomainError("UNSAFE_IMAGE", "Filename and decoded image format must match")
        if digest(raw) != request.original_sha256:
            raise DomainError("SOURCE_HASH", "Original image hash mismatch")
        if request.kind == "cutout" and not meta["transparent"]:
            raise DomainError("CUTOUT_REQUIRED", "Cutout must contain actual transparent pixels")

        def run(s):
            case = self.service.case_row(s, actor, case_id, True)
            rights = self.service.get_row(s, SourceDocument, actor, request.rights.source_id)
            content = self.service.objects.get(rights.sha256).decode()
            if (
                rights.case_id != case_id
                or rights.source_type != "rights"
                or rights.rights_status not in {"authorized", "synthetic_fixture"}
                or request.rights.exact_excerpt not in content
                or timestamp(request.rights.expires_at_utc) <= datetime.now(timezone.utc)
            ):
                raise DomainError(
                    "RIGHTS_REQUIRED", "Current original rights proof and exact excerpt required", 409
                )
            if not request.is_synthetic and (
                rights.is_synthetic
                or actor.synthetic
                or case.is_synthetic
                or rights.rights_status != "authorized"
            ):
                raise DomainError(
                    "SYNTHETIC_SOURCE", "Synthetic material cannot establish a genuine SKU", 409
                )
            if s.scalar(select(VisualAsset).where(VisualAsset.sha256 == request.original_sha256)):
                raise DomainError(
                    "DERIVED_ASSET", "Generated/derived assets cannot be original product photos", 409
                )
            existing = s.scalar(
                select(SourceDocument).where(
                    SourceDocument.tenant_id == actor.tenant_id,
                    SourceDocument.case_id == case_id,
                    SourceDocument.sha256 == request.original_sha256,
                )
            )
            if existing:
                raise DomainError(
                    "SOURCE_EXISTS", "Original bytes are already registered; use their existing identity", 409
                )
            sha = self.service.objects.put(raw)
            source = SourceDocument(
                tenant_id=actor.tenant_id,
                case_id=case_id,
                filename=request.filename,
                sha256=sha,
                source_type="image",
                rights_status="synthetic_fixture" if request.is_synthetic else "authorized",
                is_synthetic=request.is_synthetic,
                metadata_json={
                    "sku": request.sku,
                    "kind": request.kind,
                    "identity": "synthetic_fixture" if request.is_synthetic else "original",
                    "rights": request.rights.model_dump(),
                    "rights_sha256": rights.sha256,
                    "raster": meta,
                    "review": {},
                    "uploader": actor.id,
                },
            )
            s.add(source)
            s.flush()
            self.service.event(
                s, actor, case_id, "sku.original_imported", {"source_id": source.id, "sha256": sha}
            )
            return self.describe(source)

        return self.service.command(
            actor, key, {"action": "sku.upload", "case_id": case_id, **request.model_dump()}, run
        )

    def describe(self, source):
        data = row_dict(source)
        data["subject_hash"] = digest(
            {
                "sha256": source.sha256,
                "sku": source.metadata_json["sku"],
                "kind": source.metadata_json["kind"],
                "rights": source.metadata_json["rights"],
                "rights_sha256": source.metadata_json["rights_sha256"],
            }
        )
        return data

    def list(self, actor, case_id):
        with self.service.sessions() as s:
            self.service.case_row(s, actor, case_id)
            sources = s.scalars(
                select(SourceDocument)
                .where(
                    SourceDocument.tenant_id == actor.tenant_id,
                    SourceDocument.case_id == case_id,
                    SourceDocument.source_type == "image",
                )
                .order_by(SourceDocument.created_at, SourceDocument.id)
            )
            result = []
            for source in sources:
                data = self.describe(source)
                try:
                    self.valid_source(s, actor, source, review_required=False)
                    data["review_allowed"] = True
                    self.valid_source(s, actor, source)
                    data["eligibility"] = {"current": True, "reason": None}
                except DomainError as exc:
                    data.setdefault("review_allowed", False)
                    data["eligibility"] = {"current": False, "reason": exc.code}
                result.append(data)
            return result

    def preview(self, actor, source_id):
        with self.service.sessions() as s:
            source = self.service.get_row(s, SourceDocument, actor, source_id)
            if source.source_type != "image":
                raise DomainError("NOT_FOUND", "Image source not found", 404)
            raw = self.service.objects.get(source.sha256)
        raster(raw)
        # Strip metadata and cap preview dimensions; original bytes remain immutable.
        with Image.open(io.BytesIO(raw)) as image:
            image = image.convert("RGBA")
            image.thumbnail((1024, 1024))
            out = io.BytesIO()
            image.save(out, format="PNG")
            return out.getvalue()

    def review(self, actor, source_id, request, key):
        self.service.require(actor, human=True)

        def run(s):
            src = self.service.get_row(s, SourceDocument, actor, source_id)
            self.valid_source(s, actor, src, review_required=False)
            if self.describe(src)["subject_hash"] != request.expected_subject_hash:
                raise DomainError("STALE_SUBJECT", "Image/rights review hash changed", 409)
            src.metadata_json = {
                **src.metadata_json,
                "review": {
                    "actor_id": actor.id,
                    "decision": request.decision,
                    "subject_hash": request.expected_subject_hash,
                    "reason": request.reason,
                    "at": now(),
                    "is_synthetic": actor.synthetic,
                },
            }
            self.service.event(
                s,
                actor,
                src.case_id,
                "sku.original_reviewed",
                {"source_id": src.id, "decision": request.decision},
            )
            return self.describe(src)

        return self.service.command(
            actor, key, {"action": "sku.review", "source_id": source_id, **request.model_dump()}, run
        )

    def valid_source(self, s, actor, src, review_required=True):
        if (
            src.source_type != "image"
            or src.is_synthetic
            or src.rights_status != "authorized"
            or src.metadata_json.get("identity") != "original"
        ):
            raise DomainError(
                "SKU_SOURCE_BLOCKED",
                "Genuine authorized original required; concept/Mock remains blocked",
                409,
            )
        meta = src.metadata_json
        proof = self.service.get_row(s, SourceDocument, actor, meta["rights"]["source_id"])
        content = self.service.objects.get(proof.sha256).decode()
        if (
            proof.case_id != src.case_id
            or proof.rights_status != "authorized"
            or proof.is_synthetic
            or proof.source_type != "rights"
            or proof.sha256 != meta["rights_sha256"]
            or meta["rights"]["exact_excerpt"] not in content
            or timestamp(meta["rights"]["expires_at_utc"]) <= datetime.now(timezone.utc)
            or meta["rights"]["external_allowed"] is not True
        ):
            raise DomainError(
                "RIGHTS_REQUIRED", "Source rights revoked, expired, changed or not externally cleared", 409
            )
        self.service.objects.get(src.sha256)
        review = meta.get("review", {})
        if review_required and (
            review.get("decision") != "approved"
            or review.get("is_synthetic") is not False
            or review.get("subject_hash") != self.describe(src)["subject_hash"]
        ):
            raise DomainError(
                "SOURCE_REVIEW_REQUIRED", "Exact original and rights require human verification", 409
            )

    def snapshot(self, s, actor, case_id, request):
        self.service.case_row(s, actor, case_id)
        product = ProductService(self.service)
        g4 = product.current(s, actor, case_id, "G4", {"verify_sample"})
        g2 = product.current(s, actor, case_id, "G2", {"select"})
        if not g4 or not g2 or g2.subject_id != request["concept_id"]:
            raise DomainError(
                "LISTING_BLOCKED", "Current verified SKU sample and selected Spec required", 409
            )
        sample = self.service.get_row(s, Artifact, actor, g4.subject_id)
        truth = self.service.get_row(s, Artifact, actor, sample.data["truth_id"])
        if request.get("truth_snapshot_id") != truth.id or truth.sha256 != sample.data["truth_hash"]:
            raise DomainError("TRUTH_MISMATCH", "Exact current ProductTruthSnapshot required", 409)
        facts = truth.data["facts"]
        if not facts or any(
            f["external_allowed"] is not True or f["status"] != "USER_ATTESTED" for f in facts
        ):
            raise DomainError(
                "FACT_NOT_CLEARED", "Every Listing fact must be human-attested and externally cleared", 409
            )
        rule_ids = [request.get("platform_rule_id")]
        from launchcase.application.launchpacks import LaunchPackService

        rules = LaunchPackService(self.service).rule_bindings(
            s, actor, case_id, SimpleNamespace(data={"rule_ids": rule_ids})
        )
        if not rules or not all(x["valid"] for x in rules):
            raise DomainError("PLATFORM_RULE_REQUIRED", "Current scoped platform profile required", 409)
        images = []
        for source_id in request["source_asset_ids"]:
            src = self.service.get_row(s, SourceDocument, actor, source_id)
            if src.case_id != case_id or src.metadata_json.get("sku") != sample.data["sample_identifier"]:
                raise DomainError("SKU_MISMATCH", "Original image belongs to another Case/SKU", 409)
            self.valid_source(s, actor, src)
            images.append(self.describe(src))
        if not any(
            x["metadata_json"]["kind"] == "cutout" and x["metadata_json"]["raster"]["transparent"]
            for x in images
        ):
            raise DomainError(
                "CUTOUT_REQUIRED", "Strict Listing composition requires a verified transparent original", 409
            )
        logo = request.get("logo_asset_id")
        if logo and not any(x["id"] == logo and x["metadata_json"]["kind"] == "logo" for x in images):
            raise DomainError("LOGO_RIGHTS", "Logo must be an explicitly registered and reviewed source", 409)
        if ("authorized_logo" in request.get("allowed_changes", [])) != bool(logo):
            raise DomainError("LOGO_RIGHTS", "Logo permission and reference must match", 409)
        docs = []
        for fact in facts:
            src = self.service.get_row(s, SourceDocument, actor, fact["source_id"])
            if (
                src.case_id != case_id
                or src.sha256 != fact["source_sha256"]
                or src.rights_status != "authorized"
                or src.is_synthetic
            ):
                raise DomainError("FACT_SOURCE_CHANGED", "Original fact evidence changed", 409)
            self.service.objects.get(src.sha256)
            docs.append(row_dict(src))
        return {
            "truth": row_dict(truth),
            "images": images,
            "documents": docs,
            "g4_hash": g4.subject_hash,
            "rules": rules,
            "sku": sample.data["sample_identifier"],
            "external_publication_authorized": False,
        }

    def wire(self, snapshot):
        result = {**snapshot, "images": [], "documents": []}
        for kind in ["images", "documents"]:
            for src in snapshot[kind]:
                result[kind].append(
                    {**src, "data_base64": base64.b64encode(self.service.objects.get(src["sha256"])).decode()}
                )
        return result
