from sqlalchemy import select

from launchcase.application.products import ProductService
from launchcase.application.services import row_dict
from launchcase.domain.common import DomainError, digest, now
from launchcase.infrastructure.models import VisualAsset, VisualTask
from launchcase.integrations.creative import UnknownReceipt, provider


class VisualService:
    def __init__(self, service, client=None):
        self.service = service
        self.client = client or provider(service.settings)

    def configuration_hash(self):
        s = self.service.settings
        return digest({"mode": s.creative_mode, "url": s.creative_url, "token_fingerprint": digest(s.creative_token.encode()), "provider": "mock", "budget": 0, "api": "1.0.0"})

    def dependency(self, s, actor, case_id, concept_id):
        product = ProductService(self.service)
        gate = product.current(s, actor, case_id, "G2", {"select"})
        if not gate or gate.subject_id != concept_id:
            raise DomainError("GATE_BLOCKED", "Current G2 selection of this concept required", 409)
        return gate.subject_hash

    def current(self, s, actor, task):
        if task.dependency_hash != self.dependency(s, actor, task.case_id, task.concept_id) or task.configuration_hash != self.configuration_hash():
            raise DomainError("STALE_VISUAL", "Spec, rights, selection or Engine configuration changed", 409)

    def get(self, actor, task_id):
        with self.service.sessions() as s:
            task = self.service.get_row(s, VisualTask, actor, task_id)
            data = row_dict(task)
            try:
                self.current(s, actor, task)
                data["current"] = True
            except DomainError:
                data["current"] = False
            data["assets"] = [row_dict(x) for x in s.scalars(select(VisualAsset).where(VisualAsset.tenant_id == actor.tenant_id, VisualAsset.visual_task_id == task_id))]
            return data

    def create(self, actor, case_id, request, key):
        if request.intent == "listing":
            raise DomainError("LISTING_BLOCKED", "Concept/Mock imagery cannot represent a verified SKU", 409)
        def run(s):
            self.service.case_row(s, actor, case_id, True)
            dep = self.dependency(s, actor, case_id, request.concept_id)
            task = VisualTask(tenant_id=actor.tenant_id, case_id=case_id, concept_id=request.concept_id,
                request=request.model_dump(), dependency_hash=dep, configuration_hash=self.configuration_hash())
            s.add(task)
            s.flush()
            self.service.event(s, actor, case_id, "visual.created", {"visual_task_id": task.id})
            return row_dict(task)
        task = self.service.command(actor, key, {"action": "visual.create", "case": case_id, **request.model_dump()}, run)
        return self.plan(actor, task["id"])

    def plan(self, actor, task_id):
        self.service.require(actor)
        with self.service.write() as s:
            task = self.service.get_row(s, VisualTask, actor, task_id)
            self.current(s, actor, task)
            if task.plan:
                return row_dict(task)
            try:
                plan = self.client.plan(task.id, task.request)
                task.plan, task.plan_hash = plan, digest({"plan": plan, "dependency": task.dependency_hash, "configuration": task.configuration_hash})
                task.state = "awaiting_plan_review"
            except DomainError as exc:
                task.state, task.error_code = "blocked", exc.code
            self.service.event(s, actor, task.case_id, "visual.planned", {"visual_task_id": task.id, "state": task.state})
            return row_dict(task)

    def approve(self, actor, task_id, request, key):
        self.service.require(actor, human=True)
        def run(s):
            task = self.service.get_row(s, VisualTask, actor, task_id)
            self.current(s, actor, task)
            if request.expected_subject_hash != task.plan_hash or task.state != "awaiting_plan_review":
                raise DomainError("STALE_SUBJECT", "Plan hash/state changed", 409)
            task.plan_review = {"actor_id": actor.id, "decision": request.decision, "reason": request.reason, "hash": task.plan_hash, "created_at": now(), "is_synthetic": actor.synthetic}
            task.state = "plan_approved" if request.decision == "approved" else "rejected"
            self.service.event(s, actor, task.case_id, "visual.plan_reviewed", {"visual_task_id": task.id, "decision": request.decision})
            return row_dict(task)
        return self.service.command(actor, key, {"action": "visual.approve", "task": task_id, **request.model_dump()}, run)

    def submit(self, actor, task_id):
        self.service.require(actor)
        with self.service.write() as s:
            task = self.service.get_row(s, VisualTask, actor, task_id)
            self.current(s, actor, task)
            if task.state in {"submitting", "reconciling", "submitted", "running", "awaiting_asset_review", "approved"}:
                return row_dict(task)
            if task.state != "plan_approved" or task.plan_review.get("hash") != task.plan_hash:
                raise DomainError("PLAN_REVIEW_REQUIRED", "Approve the exact plan before execution", 409)
            task.state = "submitting"
            plan, submission_key = task.plan, task.submission_key
            self.service.event(s, actor, task.case_id, "visual.submitting", {"visual_task_id": task.id, "payload_hash": digest(plan), "idempotency_key": submission_key})
        try:
            batch = self.client.submit(plan, submission_key)
        except DomainError as exc:
            with self.service.write() as s:
                task = self.service.get_row(s, VisualTask, actor, task_id)
                task.state = "reconciling" if isinstance(exc, UnknownReceipt) else "blocked"
                task.error_code = exc.code
                return row_dict(task)
        with self.service.write() as s:
            task = self.service.get_row(s, VisualTask, actor, task_id)
            task.remote = {"batch_id": batch["id"]}
            task.state = "submitted"
            self.service.artifact(s, actor, self.service.case_row(s, actor, task.case_id, True), "VisualRun", {"visual_task_id": task.id, "batch_id": batch["id"], "submission_key": task.submission_key, "authorize_paid": False}, task.plan_hash)
            return row_dict(task)

    def sync(self, actor, task_id):
        self.service.require(actor)
        with self.service.write() as s:
            task = self.service.get_row(s, VisualTask, actor, task_id)
            if task.state == "cancelled":
                return row_dict(task)
            batch_id = task.remote.get("batch_id")
            if not batch_id:
                if task.state not in {"submitting", "reconciling"}:
                    raise DomainError("NOT_SUBMITTED", "No remote batch to sync", 409)
                batch = self.client.reconcile(task.plan)
                if not batch:
                    task.state = "reconciling"
                    return row_dict(task)
                batch_id = batch["id"]
                task.remote = {"batch_id": batch_id}
            batch = self.client.batch(batch_id)
            if batch["status"] in {"failed", "blocked", "cancelled", "reconciling"}:
                task.state = batch["status"]
                return row_dict(task)
            assets = self.client.assets(batch)
            for asset in assets:
                if asset.get("identity") not in {"mock", "concept"} or asset.get("provider") != "mock":
                    raise DomainError("ENGINE_IDENTITY", "Unexpected product identity/provider", 409)
                data = self.client.content(asset["id"])
                if digest(data) != asset["sha256"] or not data.startswith(b"\x89PNG\r\n\x1a\n"):
                    raise DomainError("ASSET_CORRUPT", "Engine asset bytes or format mismatch", 409)
                exists = s.scalar(select(VisualAsset).where(VisualAsset.tenant_id == actor.tenant_id, VisualAsset.visual_task_id == task_id, VisualAsset.remote_id == asset["id"]))
                if not exists:
                    sha = self.service.objects.put(data)
                    s.add(VisualAsset(tenant_id=actor.tenant_id, case_id=task.case_id, visual_task_id=task_id,
                        remote_id=asset["id"], sha256=sha, identity=asset["identity"], qa=asset.get("qa") or {"status": "block"}))
            if task.state != "approved":
                task.state = "awaiting_asset_review" if assets else "running"
            return row_dict(task)

    def review(self, actor, asset_id, request, key):
        self.service.require(actor, human=True)
        def run(s):
            asset = self.service.get_row(s, VisualAsset, actor, asset_id)
            task = self.service.get_row(s, VisualTask, actor, asset.visual_task_id)
            self.current(s, actor, task)
            self.service.objects.get(asset.sha256)
            subject_hash = digest({"asset": asset.sha256, "plan": task.plan_hash, "dependency": task.dependency_hash})
            if subject_hash != request.expected_subject_hash:
                raise DomainError("STALE_SUBJECT", "Asset review subject changed", 409)
            if asset.qa.get("status") == "block" and request.decision == "approved":
                raise DomainError("QA_BLOCKED", "Machine QA block cannot be overridden", 409)
            self.client.review(asset.remote_id, request.decision, actor.id, request.reason)
            asset.review = {"actor_id": actor.id, "decision": request.decision, "hash": subject_hash, "created_at": now(), "reason": request.reason, "is_synthetic": actor.synthetic}
            task.state = "approved" if request.decision == "approved" else "awaiting_asset_review"
            self.service.event(s, actor, task.case_id, "visual.asset_reviewed", {"asset_id": asset.id, "decision": request.decision, "sha256": asset.sha256})
            return row_dict(asset)
        return self.service.command(actor, key, {"action": "visual.review", "asset": asset_id, **request.model_dump()}, run)

    def asset(self, actor, asset_id, content=False):
        with self.service.sessions() as s:
            asset = self.service.get_row(s, VisualAsset, actor, asset_id)
            task = self.service.get_row(s, VisualTask, actor, asset.visual_task_id)
            data = self.service.objects.get(asset.sha256)
            result = row_dict(asset)
            result["subject_hash"] = digest({"asset": asset.sha256, "plan": task.plan_hash, "dependency": task.dependency_hash})
            return data if content else result

    def cancel(self, actor, task_id):
        self.service.require(actor, human=True)
        with self.service.write() as s:
            task = self.service.get_row(s, VisualTask, actor, task_id)
            if task.state in {"submitting", "reconciling"} and not task.remote:
                raise DomainError("RECONCILE_REQUIRED", "Unknown remote state must be reconciled before cancellation", 409)
            if task.remote:
                self.client.cancel(task.remote["batch_id"])
            task.state = "cancelled"
            return row_dict(task)
