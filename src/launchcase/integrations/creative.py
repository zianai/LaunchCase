"""CreativeEngine 1.0.0 consumer; no upstream code/DB imports or image worker."""

import json
import re
import sqlite3
from pathlib import Path
from typing import Protocol
from urllib.parse import urlsplit

import httpx

from launchcase.domain.common import DomainError, digest


class UnknownReceipt(DomainError):
    def __init__(self):
        super().__init__("UNKNOWN_REMOTE", "Submission outcome is unknown; reconcile before any retry", 409)


class CreativeProvider(Protocol):
    def plan(self, external_id: str, request: dict) -> dict: ...
    def submit(self, plan: dict, key: str) -> dict: ...
    def batch(self, batch_id: str) -> dict: ...
    def reconcile(self, plan: dict) -> dict | None: ...
    def assets(self, batch: dict) -> list[dict]: ...
    def content(self, asset_id: str) -> bytes: ...
    def review(self, asset_id: str, decision: str, reviewer: str, notes: str) -> dict: ...
    def cancel(self, batch_id: str) -> dict: ...


def remote_id(value):
    if not re.fullmatch(r"[A-Za-z0-9_.:-]{1,160}", value):
        raise DomainError("ENGINE_CONTRACT", "Invalid remote ID", 502)
    return value


class CreativeEngineClient:
    def __init__(self, url, token, transport=None):
        parsed = urlsplit(url)
        if (
            parsed.scheme != "http"
            or parsed.hostname not in {"127.0.0.1", "::1"}
            or parsed.username
            or parsed.query
            or parsed.fragment
        ):
            raise DomainError(
                "ENGINE_URL", "V1 HTTP integration allows explicitly configured numeric loopback only"
            )
        if not token:
            raise DomainError("ENGINE_AUTH", "Authenticated local Engine required")
        self.client = httpx.Client(
            base_url=url.rstrip("/") + "/v1/",
            headers={"Authorization": f"Bearer {token}", "X-API-Version": "1.0.0"},
            timeout=10,
            follow_redirects=False,
            trust_env=False,
            transport=transport,
        )

    def request(self, method, path, body=None, key=None, raw=False):
        try:
            response = self.client.request(
                method, path, json=body, headers={"Idempotency-Key": key} if key else None
            )
        except httpx.TransportError as exc:
            if method == "POST" and path == "batches":
                raise UnknownReceipt() from exc
            raise DomainError(
                "ENGINE_UNAVAILABLE", "CreativeEngine unavailable; product work remains accessible", 503
            ) from exc
        if response.status_code >= 500 and method == "POST" and path == "batches":
            raise UnknownReceipt()
        if response.status_code < 200 or response.status_code >= 300:
            raise DomainError(
                "ENGINE_REJECTED", f"Engine rejected request (HTTP {response.status_code})", 409
            )
        if len(response.content) > 20 * 1024 * 1024:
            raise DomainError("ENGINE_CONTRACT", "Engine response too large", 502)
        return response.content if raw else response.json()

    def verify(self):
        health = self.request("GET", "health")
        api = self.request("GET", "openapi.json")
        if health.get("schema_version") != "1.0.0" or api.get("info", {}).get("version") != "1.0.0":
            raise DomainError("ENGINE_VERSION", "Expected CreativeEngine API 1.0.0", 409)
        skills = self.request("GET", "skills")
        if "product-concept" not in json.dumps(skills):
            raise DomainError("ENGINE_SKILL", "product-concept Skill unavailable", 409)

    def plan(self, external_id, request):
        self.verify()
        project = self.request("POST", "projects", {"name": f"LaunchCase internal {external_id}"})
        brief = self.request(
            "POST",
            "briefs",
            {
                "project_id": project["id"],
                "source": {"system": "launchcase", "external_id": external_id},
                "workflow": "product-concept",
                "provider": "mock",
                "budget_usd": 0,
                "intent": "design-exploration",
                "requirements": request["requirements"],
                "product": {"product_id": request["concept_id"], "stage": "concept"},
                "reference_asset_ids": [],
                "delivery_target": "internal_review",
                "variants": request["variants"],
                "claims": [],
            },
        )
        plan = self.request("POST", f"briefs/{remote_id(brief['id'])}/plan")
        if plan.get("strategy") == "blocked" or plan.get("blocked_reasons") or plan.get("provider") != "mock":
            raise DomainError("ENGINE_PLAN_BLOCKED", "Engine plan blocked or non-Mock provider", 409)
        return {"project_id": project["id"], "brief_id": brief["id"], "plan_id": plan["id"], "plan": plan}

    def submit(self, plan, key):
        self.verify()
        latest = self.request("GET", f"plans/{remote_id(plan['plan_id'])}")
        if digest(latest) != digest(plan["plan"]):
            raise DomainError("ENGINE_PLAN_STALE", "Engine plan changed; review again", 409)
        return self.request(
            "POST",
            "batches",
            {
                "plan_id": plan["plan_id"],
                "provider": "mock",
                "budget_usd": 0,
                "authorize_paid": False,
                "vision_review": False,
            },
            key,
        )

    def batch(self, batch_id):
        return self.request("GET", f"batches/{remote_id(batch_id)}")

    def reconcile(self, plan):
        for offset in range(0, 1000, 200):
            response = self.request(
                "GET", f"batches?project_id={remote_id(plan['project_id'])}&limit=200&offset={offset}"
            )
            matches = [b for b in response["items"] if b["plan_id"] == plan["plan_id"]]
            if len(matches) == 1:
                return matches[0]
            if len(matches) > 1:
                raise DomainError(
                    "AMBIGUOUS_RECEIPT", "Multiple remote batches require operator reconciliation", 409
                )
            if len(response["items"]) < 200:
                break
        return None

    def assets(self, batch):
        found = []
        for offset in range(0, 1000, 200):
            rows = self.request(
                "GET", f"assets?project_id={remote_id(batch['project_id'])}&limit=200&offset={offset}"
            )["items"]
            found.extend(a for a in rows if a.get("batch_id") == batch["id"])
            if len(rows) < 200:
                break
        return found

    def content(self, asset_id):
        return self.request("GET", f"assets/{remote_id(asset_id)}/file", raw=True)

    def review(self, asset_id, decision, reviewer, notes):
        return self.request(
            "POST",
            f"assets/{remote_id(asset_id)}/review",
            {"decision": decision, "reviewer": reviewer, "notes": notes},
        )

    def cancel(self, batch_id):
        return self.request("POST", f"batches/{remote_id(batch_id)}/cancel")


class MockClient:
    """Persistent protocol fake returning a fixed labelled fixture; no image execution."""

    def __init__(self, root):
        self.path = root / "creative-mock.db"
        self.fixture = Path(__file__).with_name("mock-concept.png").read_bytes()
        with sqlite3.connect(self.path) as c:
            c.execute("CREATE TABLE IF NOT EXISTS objects (id TEXT PRIMARY KEY, kind TEXT, data TEXT)")

    def put(self, key, kind, data):
        with sqlite3.connect(self.path) as c:
            c.execute("INSERT OR REPLACE INTO objects VALUES (?,?,?)", (key, kind, json.dumps(data)))
        return data

    def get(self, key):
        with sqlite3.connect(self.path) as c:
            row = c.execute("SELECT data FROM objects WHERE id=?", (key,)).fetchone()
        if not row:
            raise DomainError("ENGINE_NOT_FOUND", "Mock remote object missing", 404)
        return json.loads(row[0])

    def plan(self, external_id, request):
        key = f"plan-{external_id}"
        data = {
            "project_id": f"project-{external_id}",
            "brief_id": f"brief-{external_id}",
            "plan_id": key,
            "plan": {
                "id": key,
                "provider": "mock",
                "strategy": "generate",
                "source": {"system": "launchcase", "external_id": external_id},
                "workflow": "product-concept",
                "budget_usd": 0,
                "variants": request["variants"],
                "requirements": request["requirements"],
                "skill_snapshot": {"version": "1.0.0", "digest": digest("fixed-offline-fixture".encode())},
            },
        }
        return self.put(key, "plan", data)

    def submit(self, plan, key):
        batch_id = "batch-" + key
        try:
            return self.get(batch_id)
        except DomainError:
            pass
        asset = {
            "id": "asset-" + key,
            "batch_id": batch_id,
            "project_id": plan["project_id"],
            "sha256": digest(self.fixture),
            "identity": "mock",
            "review_status": "pending",
            "provider": "mock",
            "allowed_uses": ["internal_review"],
            "qa": {
                "status": "warn",
                "checks": [],
                "issues": [{"description": "Fixed offline fixture; no semantic image validation"}],
                "vision": {"status": "skipped"},
            },
        }
        self.put(asset["id"], "asset", asset)
        return self.put(
            batch_id,
            "batch",
            {
                "id": batch_id,
                "plan_id": plan["plan_id"],
                "project_id": plan["project_id"],
                "status": "review_pending",
                "asset_ids": [asset["id"]],
                "cost_usd": 0,
                "authorize_paid": False,
            },
        )

    def batch(self, batch_id):
        return self.get(batch_id)

    def reconcile(self, plan):
        with sqlite3.connect(self.path) as c:
            rows = c.execute("SELECT data FROM objects WHERE kind='batch'").fetchall()
        return next((json.loads(r[0]) for r in rows if json.loads(r[0])["plan_id"] == plan["plan_id"]), None)

    def assets(self, batch):
        return [self.get(x) for x in batch["asset_ids"]]

    def content(self, asset_id):
        self.get(asset_id)
        return self.fixture

    def review(self, asset_id, decision, reviewer, notes):
        asset = self.get(asset_id)
        asset["review_status"] = decision
        return self.put(asset_id, "asset", asset)

    def cancel(self, batch_id):
        data = self.get(batch_id)
        data["status"] = "cancelled"
        return self.put(batch_id, "batch", data)


def provider(settings):
    if settings.creative_mode == "mock":
        return MockClient(settings.data_dir)
    if settings.creative_mode == "http":
        return CreativeEngineClient(settings.creative_url, settings.creative_token)
    raise DomainError("VISUAL_DISABLED", "Visual generation is disabled", 409)
