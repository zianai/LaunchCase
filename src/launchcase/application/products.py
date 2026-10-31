from sqlalchemy import select

from launchcase.application.research import ResearchService
from launchcase.application.services import row_dict
from launchcase.domain.common import DomainError, digest
from launchcase.domain.contracts import SpecClaim
from launchcase.infrastructure.models import Artifact, Evidence, GateDecision
from launchcase.infrastructure.tasks import TaskManager


class ProductService:
    def __init__(self, service):
        self.service = service

    def artifacts(self, s, actor, case_id, kind):
        return list(
            s.scalars(
                select(Artifact)
                .where(
                    Artifact.tenant_id == actor.tenant_id, Artifact.case_id == case_id, Artifact.kind == kind
                )
                .order_by(Artifact.version.desc())
            )
        )

    def latest_spec(self, s, actor, case_id, concept_id):
        return next(
            (
                x
                for x in self.artifacts(s, actor, case_id, "ProductSpec")
                if x.data["concept_id"] == concept_id
            ),
            None,
        )

    def latest_decision(self, s, actor, case_id, gate):
        return s.scalar(
            select(GateDecision)
            .where(
                GateDecision.tenant_id == actor.tenant_id,
                GateDecision.case_id == case_id,
                GateDecision.gate == gate,
            )
            .order_by(GateDecision.created_at.desc(), GateDecision.id.desc())
        )

    def subject(self, s, actor, case_id, gate, subject_id):
        source = ResearchService(self.service).snapshot(actor, case_id)
        artifact = self.service.get_row(s, Artifact, actor, subject_id)
        kinds = {
            "G1": "Opportunity",
            "G2": "Concept",
            "G3": "Feasibility",
            "G4": "SampleValidation",
            "G5": "LaunchPack",
        }
        if artifact.case_id != case_id or artifact.kind != kinds.get(gate):
            raise DomainError("SUBJECT_MISMATCH", "Gate subject belongs to another case/type")
        dependencies = {"source": source, "artifact_id": artifact.id, "artifact_hash": artifact.sha256}
        if gate == "G1":
            if artifact.dependency_hash != digest(source):
                raise DomainError("STALE_SUBJECT", "Opportunity is based on outdated sources", 409)
        if gate == "G2":
            g1 = self.current(s, actor, case_id, "G1", {"accept"})
            if not g1 or g1.subject_id != artifact.data["opportunity_id"]:
                raise DomainError("GATE_BLOCKED", "A current G1 selection is required", 409)
            spec = self.latest_spec(s, actor, case_id, artifact.id)
            if not spec:
                raise DomainError("GATE_BLOCKED", "Concept requires a proposed Spec", 409)
            dependencies.update(g1_id=g1.id, spec_id=spec.id, spec_hash=spec.sha256)
        if gate in {"G3", "G4", "G5"}:
            g2 = self.current(s, actor, case_id, "G2", {"select"})
            if not g2:
                raise DomainError("GATE_BLOCKED", "Current G2 selection required", 409)
            dependencies["g2_hash"] = g2.subject_hash
            dependencies["g2_id"] = g2.id
            if gate == "G3":
                from launchcase.application.feasibility import FeasibilityService

                valid, invalid = FeasibilityService(self.service).source_validity(s, actor, case_id)
                dependencies.update(valid_cost_sources=valid, invalid_cost_sources=invalid)
                latest = self.artifacts(s, actor, case_id, "Feasibility")
                if not latest or latest[0].id != artifact.id or artifact.data["g2_hash"] != g2.subject_hash:
                    raise DomainError(
                        "STALE_SUBJECT", "Feasibility no longer describes current selection", 409
                    )
                if valid != artifact.data["source_hashes"] or invalid != artifact.data["invalid_source_ids"]:
                    raise DomainError("STALE_SUBJECT", "Quote validity changed; recalculate feasibility", 409)
            if gate in {"G4", "G5"}:
                g3 = self.current(s, actor, case_id, "G3", {"sample_validation"})
                if not g3:
                    raise DomainError(
                        "GATE_BLOCKED", "Current G3 sample investigation approval required", 409
                    )
                dependencies["g3_id"] = g3.id
                if gate == "G4":
                    samples = self.artifacts(s, actor, case_id, "SampleValidation")
                    if not samples or samples[0].id != artifact.id:
                        raise DomainError("STALE_SUBJECT", "New sample record requires review", 409)
                    spec = self.latest_spec(s, actor, case_id, g2.subject_id)
                    if artifact.data["spec_hash"] != spec.sha256:
                        raise DomainError("STALE_SUBJECT", "Sample refers to an older Spec", 409)
                    for fact in artifact.data["facts"]:
                        from launchcase.infrastructure.models import SourceDocument

                        src = self.service.get_row(s, SourceDocument, actor, fact["source_id"])
                        self.service.objects.get(src.sha256)
                        if (
                            src.rights_status != "authorized"
                            or src.is_synthetic
                            or src.sha256 != fact["source_sha256"]
                        ):
                            raise DomainError("GATE_BLOCKED", "Sample evidence rights/integrity invalid", 409)
                else:
                    g4 = self.current(s, actor, case_id, "G4", {"verify_sample"})
                    if not g4:
                        raise DomainError("GATE_BLOCKED", "G4 real sample validation required", 409)
                    dependencies["g4_id"] = g4.id
                    from launchcase.application.launchpacks import LaunchPackService

                    packs = LaunchPackService(self.service)
                    case = self.service.case_row(s, actor, case_id)
                    if digest(packs.snapshot(s, actor, case)) != artifact.dependency_hash:
                        raise DomainError(
                            "STALE_PACK", "Rebuild pack after evidence or approvals change", 409
                        )
                    preparations = self.artifacts(s, actor, case_id, "HandoffPreparation")
                    preparation = next((x for x in preparations if x.data["pack_id"] == artifact.id), None)
                    dependencies["handoff_hash"] = preparation.sha256 if preparation else None
                    dependencies["rules"] = packs.rule_bindings(s, actor, case_id, preparation)

        return dependencies, digest(dependencies)

    def current(self, s, actor, case_id, gate, decisions):
        row = self.latest_decision(s, actor, case_id, gate)
        if not row or row.decision not in decisions:
            return None
        try:
            _, sha = self.subject(s, actor, case_id, gate, row.subject_id)
            return row if sha == row.subject_hash else None
        except DomainError:
            return None

    def gate_subject(self, actor, case_id, gate, subject_id):
        with self.service.sessions() as s:
            self.service.case_row(s, actor, case_id)
            dependencies, sha = self.subject(s, actor, case_id, gate, subject_id)
            return {"gate": gate, "subject_id": subject_id, "subject_hash": sha, "dependencies": dependencies}

    def decisions(self, actor, case_id, exclude_g5=False):
        with self.service.sessions() as s:
            self.service.case_row(s, actor, case_id)
            rows = list(
                s.scalars(
                    select(GateDecision)
                    .where(GateDecision.tenant_id == actor.tenant_id, GateDecision.case_id == case_id)
                    .order_by(GateDecision.created_at)
                )
            )
            result = []
            latest = {r.gate: r.id for r in rows}
            for row in rows:
                if exclude_g5 and row.gate == "G5":
                    continue
                try:
                    _, sha = self.subject(s, actor, case_id, row.gate, row.subject_id)
                    status = "current" if row.subject_hash == sha and latest[row.gate] == row.id else "stale"
                except DomainError:
                    status = "stale"
                result.append({**row_dict(row), "status": status})
            return result

    def decide(self, actor, case_id, gate, request, key):
        self.service.require(actor, human=True)
        choices = {
            "G1": {"accept", "research_more", "reject"},
            "G2": {"select", "revise", "reject"},
            "G3": {"sample_validation", "revise", "hold"},
            "G4": {"verify_sample", "rework", "hold"},
            "G5": {"internal_handoff", "needs_changes"},
        }
        types = {
            "G1": "opportunity",
            "G2": "concept",
            "G3": "feasibility",
            "G4": "sample",
            "G5": "launch_pack",
        }
        if request.decision not in choices.get(gate, set()) or request.subject_type != types.get(gate):
            raise DomainError("INVALID_DECISION", "Decision/type does not match this gate")

        def run(s):
            case = self.service.case_row(s, actor, case_id, True)
            dependencies, sha = self.subject(s, actor, case_id, gate, request.subject_id)
            if sha != request.expected_subject_hash:
                raise DomainError(
                    "STALE_SUBJECT", "Subject changed; re-read and review the current version", 409
                )
            subject = self.service.get_row(s, Artifact, actor, request.subject_id)
            if (
                gate == "G1"
                and request.decision == "accept"
                and subject.data["data_sufficiency_status"] == "needs_more_data"
            ):
                raise DomainError("GATE_BLOCKED", "Insufficient traceable evidence", 409)
            if (
                gate == "G4"
                and request.decision == "verify_sample"
                and (case.is_synthetic or actor.synthetic or subject.data["is_synthetic"])
            ):
                raise DomainError("GATE_BLOCKED", "Synthetic approvals cannot validate real samples", 409)
            if gate == "G5" and request.decision == "internal_handoff":
                from launchcase.application.launchpacks import LaunchPackService

                LaunchPackService(self.service).outward_prerequisites(s, actor, case, subject)
            row = GateDecision(
                tenant_id=actor.tenant_id,
                case_id=case_id,
                gate=gate,
                decision=request.decision,
                subject_type=request.subject_type,
                subject_id=request.subject_id,
                subject_hash=sha,
                dependencies=dependencies,
                actor_id=actor.id,
                role=actor.role,
                reason=request.reason,
                is_synthetic=actor.synthetic or case.is_synthetic,
            )
            s.add(row)
            s.flush()
            stage = {
                ("G1", "accept"): "concepting",
                ("G2", "select"): "feasibility_review",
                ("G3", "sample_validation"): "awaiting_sample_validation",
                ("G4", "verify_sample"): "launch_draft",
                ("G5", "internal_handoff"): "ready_for_internal_handoff",
            }.get(
                (gate, request.decision),
                {
                    "G1": "opportunity_review",
                    "G2": "concept_review",
                    "G3": "feasibility_review",
                    "G4": "awaiting_sample_validation",
                    "G5": "launch_draft",
                }[gate],
            )
            self.service.bump(case, stage, "needs_review")
            self.service.event(
                s, actor, case_id, "gate.decided", {"gate": gate, "decision_id": row.id, "subject_hash": sha}
            )
            return row_dict(row)

        return self.service.command(
            actor, key, {"action": "gate.decide", "case": case_id, "gate": gate, **request.model_dump()}, run
        )

    def concept_input(self, actor, case_id):
        with self.service.sessions() as s:
            self.service.case_row(s, actor, case_id)
            decision = self.current(s, actor, case_id, "G1", {"accept"})
            if not decision:
                raise DomainError(
                    "GATE_BLOCKED", "Current G1 approval required before concept generation", 409
                )
            return {"case_id": case_id, "g1_id": decision.id, "g1_hash": decision.subject_hash}

    def develop(self, actor, task_id, fence):
        manager = TaskManager(self.service)
        task = manager.get(actor, task_id)
        snapshot = self.concept_input(actor, task["case_id"])
        if digest(snapshot) != task["input_hash"]:
            raise DomainError("STALE_INPUT", "Opportunity selection changed", 409)
        with self.service.sessions() as s:
            existing = [
                x
                for x in self.artifacts(s, actor, task["case_id"], "Concept")
                if x.dependency_hash == task["input_hash"]
            ]
            if existing:
                return {"concept_ids": [x.id for x in existing]}
            decision = self.service.get_row(s, GateDecision, actor, snapshot["g1_id"])
            opp = self.service.get_row(s, Artifact, actor, decision.subject_id)
            context = opp.data
        from launchcase.agents.product import ProductRunner

        output = ProductRunner().run(context)
        with self.service.write() as s:
            manager.check_fence(s, actor, task_id, fence)
            case = self.service.case_row(s, actor, task["case_id"], True)
            if self.concept_input(actor, case.id) != snapshot:
                raise DomainError("STALE_INPUT", "G1 changed during product reasoning", 409)
            ids = []
            for draft in output["concepts"]:
                concept = self.service.artifact(
                    s,
                    actor,
                    case,
                    "Concept",
                    {
                        **draft,
                        "opportunity_id": opp.id,
                        "evidence_refs": context["evidence_refs"],
                        "classification": "proposal",
                        "internal_only": True,
                    },
                    task["input_hash"],
                )
                ids.append(concept.id)
                claims = [
                    SpecClaim(
                        name="design_direction", value=draft["design_intent"], status="proposed"
                    ).model_dump(),
                    *[
                        SpecClaim(name=n).model_dump()
                        for n in [
                            "dimensions",
                            "material",
                            "load_rating",
                            "pet_safety",
                            "manufacturing_tolerance",
                        ]
                    ],
                ]
                self.service.artifact(
                    s,
                    actor,
                    case,
                    "ProductSpec",
                    {
                        "concept_id": concept.id,
                        "claims": claims,
                        "reason": "Initial proposed definition; no product performance verified",
                        "parent_spec_id": None,
                    },
                    concept.sha256,
                )
            self.service.artifact(s, actor, case, "AgentRun", output["run"], task["input_hash"])
            self.service.bump(case, "concept_review", "needs_review")
            self.service.event(s, actor, case.id, "concepts.created", {"concept_ids": ids})
            return {"concept_ids": ids}

    def revise_spec(self, actor, case_id, concept_id, request, key):
        def run(s):
            case = self.service.case_row(s, actor, case_id, True)
            concept = self.service.get_row(s, Artifact, actor, concept_id)
            if concept.case_id != case_id or concept.kind != "Concept":
                raise DomainError("SUBJECT_MISMATCH", "Wrong concept")
            current = self.latest_spec(s, actor, case_id, concept_id)
            if not current or current.sha256 != request.expected_subject_hash:
                raise DomainError("STALE_SUBJECT", "Spec changed", 409)
            refs = {
                e.id
                for e in s.scalars(
                    select(Evidence).where(Evidence.tenant_id == actor.tenant_id, Evidence.case_id == case_id)
                )
            }
            if any(ref not in refs for c in request.claims for ref in c.evidence_refs):
                raise DomainError("INVALID_CITATION", "Spec evidence outside current case")
            data = {
                "concept_id": concept_id,
                "claims": [c.model_dump() for c in request.claims],
                "reason": request.reason,
                "parent_spec_id": current.id,
            }
            artifact = self.service.artifact(s, actor, case, "ProductSpec", data, concept.sha256)
            self.service.bump(case, "concept_review", "needs_review")
            self.service.event(
                s, actor, case_id, "spec.revised", {"spec_id": artifact.id, "prior_spec_id": current.id}
            )
            return row_dict(artifact)

        return self.service.command(
            actor,
            key,
            {"action": "spec.revise", "case": case_id, "concept": concept_id, **request.model_dump()},
            run,
        )

    def spec_diff(self, actor, case_id, left_id, right_id):
        with self.service.sessions() as s:
            self.service.case_row(s, actor, case_id)
            rows = [self.service.get_row(s, Artifact, actor, x) for x in [left_id, right_id]]
            if any(x.case_id != case_id or x.kind != "ProductSpec" for x in rows):
                raise DomainError("SUBJECT_MISMATCH", "Spec comparison requires same case")
            left, right = [{c["name"]: c for c in r.data["claims"]} for r in rows]
            return {
                "changes": [
                    {"name": n, "before": left.get(n), "after": right.get(n)}
                    for n in sorted(left.keys() | right.keys())
                    if left.get(n) != right.get(n)
                ]
            }
