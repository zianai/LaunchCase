import io
import json
import zipfile
from datetime import datetime, timezone

from sqlalchemy import select

from launchcase.agents.runtime import skill_snapshot
from launchcase.application.products import ProductService
from launchcase.application.services import row_dict
from launchcase.application.visuals import VisualService
from launchcase.domain.common import DomainError, canonical, digest
from launchcase.domain.economics import instant
from launchcase.infrastructure.models import Artifact, Evidence, SourceDocument, VisualAsset, VisualTask


class LaunchPackService:
    def __init__(self, service):
        self.service = service

    def snapshot(self, s, actor, case):
        product = ProductService(self.service)
        g1 = product.current(s, actor, case.id, "G1", {"accept"})
        g2 = product.current(s, actor, case.id, "G2", {"select"})
        if not g1 or not g2:
            raise DomainError("GATE_BLOCKED", "Current G1/G2 reviews required for an internal draft", 409)
        sources = list(
            s.scalars(
                select(SourceDocument)
                .where(SourceDocument.tenant_id == actor.tenant_id, SourceDocument.case_id == case.id)
                .order_by(SourceDocument.id)
            )
        )
        for source in sources:
            self.service.objects.get(source.sha256)
        selected_spec = product.latest_spec(s, actor, case.id, g2.subject_id)
        feasibility = product.artifacts(s, actor, case.id, "Feasibility")
        if not feasibility:
            raise DomainError("FEASIBILITY_REQUIRED", "Calculate known and missing costs first", 409)
        product.subject(s, actor, case.id, "G3", feasibility[0].id)
        approved = []
        visual_service = VisualService(self.service)
        for asset in s.scalars(
            select(VisualAsset)
            .where(VisualAsset.tenant_id == actor.tenant_id, VisualAsset.case_id == case.id)
            .order_by(VisualAsset.id)
        ):
            if asset.review.get("decision") != "approved":
                continue
            task = self.service.get_row(s, VisualTask, actor, asset.visual_task_id)
            try:
                visual_service.current(s, actor, task)
            except DomainError:
                continue
            if task.state == "cancelled" or asset.qa.get("status") == "block":
                continue
            self.service.objects.get(asset.sha256)
            approved.append(
                {
                    "asset_id": asset.id,
                    "sha256": asset.sha256,
                    "identity": asset.identity,
                    "review_hash": asset.review["hash"],
                    "plan_hash": task.plan_hash,
                    "allowed_use": "internal_only",
                }
            )
        decisions = ProductService(self.service).decisions(actor, case.id)
        return {
            "brief_version": case.brief_version,
            "sources": [
                {"id": x.id, "sha256": x.sha256, "rights": x.rights_status, "is_synthetic": x.is_synthetic}
                for x in sources
            ],
            "g1_id": g1.id,
            "g2_id": g2.id,
            "spec_id": selected_spec.id,
            "spec_hash": selected_spec.sha256,
            "feasibility_id": feasibility[0].id,
            "feasibility_hash": feasibility[0].sha256,
            "decisions": [
                {"id": d["id"], "hash": d["subject_hash"], "status": d["status"]} for d in decisions
            ],
            "assets": approved,
        }

    def build(self, actor, case_id, key):
        def run(s):
            case = self.service.case_row(s, actor, case_id, True)
            snapshot = self.snapshot(s, actor, case)
            product = ProductService(self.service)
            selected = self.service.get_row(
                s, Artifact, actor, product.current(s, actor, case_id, "G2", {"select"}).subject_id
            )
            opportunity = self.service.get_row(s, Artifact, actor, selected.data["opportunity_id"])
            spec = self.service.get_row(s, Artifact, actor, snapshot["spec_id"])
            feasibility = self.service.get_row(s, Artifact, actor, snapshot["feasibility_id"])
            evidence = [
                row_dict(x)
                for x in s.scalars(
                    select(Evidence)
                    .where(Evidence.tenant_id == actor.tenant_id, Evidence.case_id == case_id)
                    .order_by(Evidence.source_locator)
                )
            ]
            data = {
                "schema_version": "1.0.0",
                "title": case.title,
                "audience": "internal",
                "status": "draft",
                "skill_hashes": skill_snapshot(["launch-preparation"])[0],
                "publishable": False,
                "publication_action": "unavailable",
                "is_synthetic": case.is_synthetic,
                "watermark": "INTERNAL DRAFT / CONCEPT / NOT LISTING READY",
                "manifest": snapshot,
                "opportunity_memo": opportunity.data,
                "concept_comparison": [row_dict(x) for x in product.artifacts(s, actor, case_id, "Concept")],
                "prd": spec.data,
                "cost_model": feasibility.data["economics"],
                "risk_register": feasibility.data["risks"],
                "voc_appendix": [
                    {
                        "evidence_id": e["id"],
                        "source_id": e["source_id"],
                        "locator": e["source_locator"],
                        "quote": e["quote"],
                        "is_synthetic": e["is_synthetic"],
                    }
                    for e in evidence
                    if e["data"]["source_type"] == "review"
                ],
                "listing_draft": {
                    "headline": "Product concept under investigation",
                    "copy": "Internal development proposal. Product facts, dimensions, performance and claims require confirmation.",
                    "unsupported_claims_withheld": [
                        c["name"] for c in spec.data["claims"] if c["status"] in {"proposed", "unknown"}
                    ],
                },
                "blockers": [
                    "G4: real sample/test confirmation required",
                    "G5: verified product facts, current scoped rules and external image rights required",
                    *(
                        ["Unit economics incomplete; missing costs are not zero"]
                        if feasibility.data["economics"]["unit_contribution"] is None
                        else []
                    ),
                    "Mock/concept visuals are internal communication materials only",
                ],
                "ready_for_sample_validation": True,
                "real_market_validation": "not_measured",
            }
            pack = self.service.artifact(s, actor, case, "LaunchPack", data, digest(snapshot))
            self.service.bump(case, "ready_for_internal_handoff", "needs_review")
            self.service.event(
                s,
                actor,
                case_id,
                "launchpack.internal_draft_created",
                {"pack_id": pack.id, "publishable": False},
            )
            return row_dict(pack)

        return self.service.command(actor, key, {"action": "launchpack.build", "case": case_id}, run)

    def read(self, actor, pack_id):
        with self.service.sessions() as s:
            pack = self.service.get_row(s, Artifact, actor, pack_id)
            if pack.kind != "LaunchPack":
                raise DomainError("NOT_FOUND", "LaunchPack not found", 404)
            case = self.service.case_row(s, actor, pack.case_id)
            try:
                current = digest(self.snapshot(s, actor, case)) == pack.dependency_hash
            except DomainError:
                current = False
            return {**row_dict(pack), "current": current}

    def export(self, actor, pack_id, format="json"):
        pack = self.read(actor, pack_id)
        if not pack["current"]:
            raise DomainError(
                "STALE_PACK", "Source/Spec/quote/asset/approval changed; rebuild internal draft", 409
            )
        data = pack["data"]
        encoded = canonical(data)
        if format == "json":
            return encoded
        markdown = f"# {data['title']}\n\n**{data['watermark']}**\n\nSynthetic: {data['is_synthetic']} · Publishable: false\n\n"
        for title, value in [
            ("Opportunity", data["opportunity_memo"]),
            ("Proposed PRD", data["prd"]),
            ("Cost model", data["cost_model"]),
            ("Risk register", data["risk_register"]),
            ("Blockers", data["blockers"]),
            ("Listing draft", data["listing_draft"]),
            ("Evidence appendix", data["voc_appendix"]),
        ]:
            markdown += f"## {title}\n\n```json\n{json.dumps(value, ensure_ascii=False, indent=2)}\n```\n\n"
        if format == "md":
            return markdown.encode()
        if format != "zip":
            raise DomainError("EXPORT_FORMAT", "Choose json, md or zip")
        files = {"launchpack.json": encoded, "launchpack.md": markdown.encode()}
        for asset in data["manifest"]["assets"]:
            files[f"assets/{asset['asset_id']}.png"] = self.service.objects.get(asset["sha256"])
        files["manifest.json"] = canonical(
            {
                "status": "internal_draft",
                "publishable": False,
                "pack_sha256": pack["sha256"],
                "files": {name: digest(value) for name, value in files.items()},
            }
        )
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, content in sorted(files.items()):
                entry = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
                archive.writestr(entry, content)
        return out.getvalue()

    def outward_prerequisites(self, s, actor, case, pack):
        if case.is_synthetic or actor.synthetic:
            raise DomainError("GATE_BLOCKED", "Synthetic work cannot pass real launch review", 409)
        rules = ProductService(self.service).artifacts(s, actor, case.id, "RuleSnapshot")
        current = [
            x
            for x in rules
            if not x.data["is_synthetic"]
            and instant(x.data["effective_at"])
            <= datetime.now(timezone.utc)
            < instant(x.data["review_due_at"])
        ]
        if not current:
            raise DomainError(
                "GATE_BLOCKED", "Current scoped official rules require human applicability review", 409
            )
        # V1 only produces concept/mock visual material. External-ready mode is intentionally unavailable.
        raise DomainError(
            "GATE_BLOCKED",
            "V1 internal concept pack cannot become an external listing pack; publication unavailable",
            409,
        )
