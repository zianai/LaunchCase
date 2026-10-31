from datetime import datetime, timezone

from sqlalchemy import select

from launchcase.agents.runtime import skill_snapshot
from launchcase.application.products import ProductService
from launchcase.application.services import row_dict
from launchcase.domain.common import DomainError
from launchcase.domain.contracts import CostRequest, MoneyInput
from launchcase.domain.economics import COMPONENTS, calculate, instant
from launchcase.infrastructure.models import Evidence, SourceDocument


class FeasibilityService:
    def __init__(self, service):
        self.service = service

    def source_validity(self, s, actor, case_id):
        valid, invalid = {}, []
        evidence = self.service.list_scoped(actor, case_id, Evidence, 5000)
        for src in s.scalars(select(SourceDocument).where(SourceDocument.tenant_id == actor.tenant_id, SourceDocument.case_id == case_id,
            SourceDocument.source_type.in_(["quote", "spec"]))):
            self.service.objects.get(src.sha256)
            if src.rights_status not in {"authorized", "synthetic_fixture"}:
                invalid.append(src.id)
                continue
            expiry = next((e['data']['raw'].get('expires_at') for e in evidence if e['source_id'] == src.id), None)
            if expiry and instant(expiry) <= datetime.now(timezone.utc):
                invalid.append(src.id)
            else:
                valid[src.id] = src.sha256
        return valid, invalid

    def default_costs(self, s, actor, case_id):
        rows = list(s.scalars(select(Evidence).join(SourceDocument, Evidence.source_id == SourceDocument.id).where(
            Evidence.tenant_id == actor.tenant_id, Evidence.case_id == case_id, SourceDocument.source_type == "quote")))
        quote = rows[-1] if rows else None
        data = quote.data["raw"] if quote else {}
        fields = {"ex_factory": "unit_ex_factory_cost", "freight": "freight_per_piece", "tariff_duty": "tariff_per_piece",
            "fulfillment": "fulfillment_per_piece", "advertising_allocated": "advertising_per_piece", "returns_allowance": "returns_allowance_per_piece"}
        components = {}
        for name in COMPONENTS:
            amount = data.get(fields.get(name, name))
            components[name] = MoneyInput(amount=str(amount) if amount is not None else None, currency=data.get("currency", "USD"),
                unit=data.get("unit", "piece"), provenance="quote" if amount is not None else "missing", source_id=quote.source_id if quote else None)
        return CostRequest(components=components, assumptions=["Imported quote fields are unverified source claims; fees and revenue are not inferred."])

    def evaluate(self, actor, case_id, request, key):
        def run(s):
            case = self.service.case_row(s, actor, case_id, True)
            product = ProductService(self.service)
            g2 = product.current(s, actor, case_id, "G2", {"select"})
            if not g2:
                raise DomainError("GATE_BLOCKED", "Current G2 selection is required", 409)
            cost = request or self.default_costs(s, actor, case_id)
            valid, invalid = self.source_validity(s, actor, case_id)
            economics = calculate(cost, valid)
            source = product.subject(s, actor, case_id, "G2", g2.subject_id)[1]
            cost_artifact = self.service.artifact(s, actor, case, "CostInput", cost.model_dump(), source)
            data = {"cost_input_id": cost_artifact.id, "g2_id": g2.id, "g2_hash": source,
                "skill_hashes": skill_snapshot(["commercial-feasibility"])[0],
                "economics": economics, "source_hashes": valid, "invalid_source_ids": invalid,
                "risks": [{"domain": domain, "owner": "product_owner", "status": "needs_review", "evidence_refs": [], "question": question} for domain, question in [
                    ("engineering", "Prototype strength, tolerances and assembly must be measured"),
                    ("supply_chain", "Confirm supplier quotation, MOQ, production process and lead time"),
                    ("compliance", "Obtain current official rules and assess product-specific applicability"),
                    ("returns", "Investigate returns causes using actual product data"),
                    ("marketing", "Validate target customer problem and truthful claims")]],
                "recommendation": "Investigate missing inputs and physical samples; no viability conclusion",
                "sample_status": "not_verified", "compliance_status": "needs_review"}
            result = self.service.artifact(s, actor, case, "Feasibility", data, source)
            self.service.bump(case, "feasibility_review", "needs_review")
            self.service.event(s, actor, case_id, "feasibility.calculated", {"artifact_id": result.id, "status": economics["status"]})
            return row_dict(result)
        return self.service.command(actor, key, {"action": "feasibility", "case": case_id, "cost": request.model_dump() if request else None}, run)

    def sample(self, actor, case_id, request, key):
        self.service.require(actor, human=True)
        def run(s):
            case = self.service.case_row(s, actor, case_id, True)
            product = ProductService(self.service)
            g3 = product.current(s, actor, case_id, "G3", {"sample_validation"})
            g2 = product.current(s, actor, case_id, "G2", {"select"})
            if not g3 or not g2 or case.is_synthetic or actor.synthetic:
                raise DomainError("SAMPLE_BLOCKED", "Real Case, current G3 and responsible human required", 409)
            spec = product.latest_spec(s, actor, case_id, g2.subject_id)
            if spec.sha256 != request.expected_spec_hash or instant(request.tested_at) > datetime.now(timezone.utc):
                raise DomainError("STALE_SUBJECT", "Sample must bind current Spec and a past test date", 409)
            facts = []
            for fact in request.facts:
                source = self.service.get_row(s, SourceDocument, actor, fact.source_id)
                content = self.service.objects.get(source.sha256).decode()
                if source.case_id != case_id or source.source_type != "sample" or source.is_synthetic or source.rights_status != "authorized" or fact.exact_excerpt not in content:
                    raise DomainError("SAMPLE_BLOCKED", "Real authorized sample source and exact excerpt required", 409)
                facts.append({**fact.model_dump(), "source_sha256": source.sha256, "status": "USER_ATTESTED", "confirmed_by": actor.id})
            truth = self.service.artifact(s, actor, case, "ProductTruthSnapshot", {"facts": facts, "spec_id": spec.id,
                "spec_hash": spec.sha256, "confirmed_at": request.tested_at, "responsible_person": request.responsible_person,
                "limitations": request.limitations, "independent_automation_verification": False}, g2.subject_hash)
            result = self.service.artifact(s, actor, case, "SampleValidation", {"truth_id": truth.id, "truth_hash": truth.sha256,
                "spec_hash": spec.sha256, "g3_id": g3.id, "is_synthetic": False, "facts": facts}, g2.subject_hash)
            self.service.event(s, actor, case_id, "sample.attested", {"sample_id": result.id})
            return row_dict(result)
        return self.service.command(actor, key, {"action": "sample.attest", "case": case_id, **request.model_dump()}, run)

    def rule(self, actor, case_id, request, key):
        self.service.require(actor, human=True)
        def run(s):
            case = self.service.case_row(s, actor, case_id, True)
            src = self.service.get_row(s, SourceDocument, actor, request.source_id)
            content = self.service.objects.get(src.sha256).decode()
            if src.case_id != case_id or src.source_type != "rule" or src.is_synthetic or src.rights_status != "authorized" or request.exact_excerpt not in content:
                raise DomainError("RULE_BLOCKED", "Current authorized rule source and exact excerpt required", 409)
            if not instant(request.effective_at) <= datetime.now(timezone.utc) < instant(request.review_due_at):
                raise DomainError("RULE_EXPIRED", "Rule is not currently effective/reviewed", 409)
            artifact = self.service.artifact(s, actor, case, "RuleSnapshot", {**request.model_dump(), "source_sha256": src.sha256,
                "status": "verified_by_human", "actor_id": actor.id, "is_synthetic": actor.synthetic}, src.sha256)
            self.service.event(s, actor, case_id, "rule.attested", {"rule_id": artifact.id})
            return row_dict(artifact)
        return self.service.command(actor, key, {"action": "rule.attest", "case": case_id, **request.model_dump()}, run)
