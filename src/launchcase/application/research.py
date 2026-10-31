from sqlalchemy import select

from launchcase.agents.runtime import FakeSDKRunner
from launchcase.application.services import row_dict
from launchcase.domain.common import DomainError, digest
from launchcase.infrastructure.models import Artifact, Evidence, SourceDocument
from launchcase.infrastructure.tasks import TaskManager


class ResearchService:
    def __init__(self, service, runner=None):
        self.service = service
        self.runner = runner or FakeSDKRunner()

    def snapshot(self, actor, case_id):
        with self.service.sessions() as s:
            case = self.service.case_row(s, actor, case_id)
            sources = list(s.scalars(select(SourceDocument).where(SourceDocument.tenant_id == actor.tenant_id, SourceDocument.case_id == case_id).order_by(SourceDocument.id)))
            for src in sources:
                self.service.objects.get(src.sha256)
            return {"case_id": case.id, "brief_version": case.brief_version,
                    "sources": [{"id": x.id, "sha256": x.sha256, "rights": x.rights_status} for x in sources]}

    def execute(self, actor, task_id, fence):
        manager = TaskManager(self.service)
        task = manager.get(actor, task_id)
        snapshot = self.snapshot(actor, task["case_id"])
        if digest(snapshot) != task["input_hash"]:
            raise DomainError("STALE_INPUT", "Research input changed", 409)
        with self.service.sessions() as s:
            existing = s.scalar(select(Artifact).where(Artifact.tenant_id == actor.tenant_id,
                Artifact.case_id == task["case_id"], Artifact.kind == "Research", Artifact.dependency_hash == task["input_hash"]))
            if existing:
                return existing.data
            evidence = [row_dict(e) for e in s.scalars(select(Evidence).join(SourceDocument, Evidence.source_id == SourceDocument.id)
                .where(Evidence.tenant_id == actor.tenant_id, Evidence.case_id == task["case_id"],
                       SourceDocument.tenant_id == actor.tenant_id, SourceDocument.rights_status.in_(["authorized", "synthetic_fixture"])).order_by(Evidence.source_locator))]
        result = self.runner.run(evidence)
        reviews = [e for e in evidence if e["data"]["source_type"] == "review"]
        products = {e["data"]["product_identity"] for e in reviews} - {"unresolved"}
        dated = all(e["data"]["observed_at"] for e in reviews)
        sufficient = len(reviews) >= 5 and len(products) >= 2 and dated
        conflicts = any(t["supporting_evidence_refs"] and t["contradicting_evidence_refs"] for t in result["output"]["themes"])
        sufficiency = {"status": ("conflicted" if conflicts else "sufficient_for_draft") if sufficient else "needs_more_data",
            "draft_minimum_met": sufficient, "review_count": len(reviews), "independent_products": len(products),
            "reasons": ["Threshold 5 dated reviews / 2 imported product IDs is a workflow minimum, not statistical proof.",
                        "Variant differences and selection bias require human interpretation."]}
        result["sufficiency"] = sufficiency
        with self.service.write() as s:
            manager.check_fence(s, actor, task_id, fence)
            case = self.service.case_row(s, actor, task["case_id"], True)
            if digest(self.snapshot(actor, case.id)) != task["input_hash"]:
                raise DomainError("STALE_INPUT", "Source changed during research", 409)
            self.service.artifact(s, actor, case, "Research", result, task["input_hash"])
            for theme in result["output"]["themes"]:
                insight = self.service.artifact(s, actor, case, "Insight", {**theme, "classification": "inferred",
                    "sample_limitations": result["output"]["sample_limitations"]}, task["input_hash"])
                if theme["supporting_evidence_refs"]:
                    self.service.artifact(s, actor, case, "Opportunity", {"title": f"Reduce {theme['name']} friction",
                        "problem": theme["interpretation"], "insight_id": insight.id, "classification": "hypothesis",
                        "evidence_refs": theme["supporting_evidence_refs"], "counter_evidence_refs": theme["contradicting_evidence_refs"],
                        "target_segment": "Imported sample's target users; unvalidated",
                        "alternatives": ["Improve instructions for existing products", "Investigate variant mismatch before redesign"],
                        "assumptions": ["The selected complaint matters to the intended segment"],
                        "falsification_plan": "Interview target users and compare physical prototypes; abandon if the reported friction does not recur.",
                        "data_sufficiency_status": sufficiency["status"], "sample_limitations": result["output"]["sample_limitations"]}, task["input_hash"])
            self.service.bump(case, "opportunity_review" if sufficient else "collecting_sources", "needs_review" if sufficient else "needs_input")
            self.service.event(s, actor, case.id, "research.completed", {"task_id": task_id, "sufficiency": sufficiency["status"]})
        return result
