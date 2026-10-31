import time
from dataclasses import replace

import httpx
import pytest
from conftest import decide

from launchcase.application.services import CaseService
from launchcase.application.visuals import VisualService
from launchcase.domain.common import DomainError
from launchcase.domain.contracts import ReviewRequest, SpecClaim, SpecRevision, VisualRequest
from launchcase.infrastructure.models import Artifact
from launchcase.integrations.creative import CreativeEngineClient, MockClient, UnknownReceipt


@pytest.fixture
def visual(setup, case, concepts):
    svc, actor, _, _ = setup
    decide(svc, actor, case["id"], "G2", concepts[0]["id"], "select")
    visual = VisualService(svc)
    task = visual.create(
        actor,
        case["id"],
        VisualRequest(concept_id=concepts[0]["id"], requirements="Internal concept only; no product claims"),
        "visual",
    )
    return visual, task


def approve_plan(visual, actor, task):
    return visual.approve(
        actor,
        task["id"],
        ReviewRequest(
            expected_subject_hash=task["plan_hash"],
            decision="approved",
            reason="Synthetic internal zero-cost plan approval",
        ),
        "plan-review",
    )


def test_plan_review_separate_asset_review_and_duplicate_submit(setup, visual):
    _, actor, other, _ = setup
    service, task = visual
    with pytest.raises(DomainError, match="Approve"):
        service.submit(actor, task["id"])
    approve_plan(service, actor, task)
    submitted = service.submit(actor, task["id"])
    assert service.submit(actor, task["id"])["remote"] == submitted["remote"]
    service.sync(actor, task["id"])
    current = service.get(actor, task["id"])
    assert current["state"] == "awaiting_asset_review"
    asset = service.asset(actor, current["assets"][0]["id"])
    assert asset["review"] == {} and asset["identity"] == "mock"
    assert service.asset(actor, asset["id"], True).startswith(b"\x89PNG")
    service.review(
        actor,
        asset["id"],
        ReviewRequest(
            expected_subject_hash=asset["subject_hash"],
            decision="approved",
            reason="Synthetic review of fixed Mock raster",
        ),
        "review",
    )
    assert service.get(actor, task["id"])["state"] == "approved"
    with pytest.raises(DomainError) as error:
        service.asset(other, asset["id"])
    assert error.value.status == 404


def test_unknown_receipt_no_resubmit_and_reconcile(setup, visual):
    svc, actor, _, _ = setup
    service, task = visual

    class Ambiguous(MockClient):
        calls = 0

        def submit(self, plan, key):
            self.calls += 1
            super().submit(plan, key)
            raise UnknownReceipt()

    client = Ambiguous(svc.settings.data_dir)
    service.client = client
    approve_plan(service, actor, task)
    assert service.submit(actor, task["id"])["state"] == "reconciling"
    assert service.submit(actor, task["id"])["state"] == "reconciling"
    assert client.calls == 1
    service.sync(actor, task["id"])
    assert service.get(actor, task["id"])["state"] == "awaiting_asset_review"


def test_engine_failure_does_not_block_product(setup, case, concepts):
    svc, actor, _, _ = setup
    decide(svc, actor, case["id"], "G2", concepts[0]["id"], "select")

    class Down(MockClient):
        def plan(self, *_):
            raise DomainError("ENGINE_UNAVAILABLE", "Engine down", 503)

    task = VisualService(svc, Down(svc.settings.data_dir)).create(
        actor, case["id"], VisualRequest(concept_id=concepts[0]["id"], requirements="Internal only"), "down"
    )
    assert task["state"] == "blocked"
    assert svc.get_case(actor, case["id"])["stage"] == "feasibility_review"


def test_stale_spec_or_config_blocks_plan(setup, case, concepts, visual):
    svc, actor, _, _ = setup
    service, task = visual
    changed = VisualService(CaseService(replace(svc.settings, creative_url="http://127.0.0.1:9999")))
    with pytest.raises(DomainError, match="configuration"):
        approve_plan(changed, actor, task)
    from launchcase.application.products import ProductService

    spec = next(
        x
        for x in svc.list_scoped(actor, case["id"], Artifact, kind="ProductSpec")
        if x["data"]["concept_id"] == concepts[0]["id"]
    )
    ProductService(svc).revise_spec(
        actor,
        case["id"],
        concepts[0]["id"],
        SpecRevision(
            expected_subject_hash=spec["sha256"],
            claims=[SpecClaim(name="material")],
            reason="Changed proposed spec",
        ),
        "revise",
    )
    assert service.get(actor, task["id"])["current"] is False
    with pytest.raises(DomainError):
        approve_plan(service, actor, task)


def test_listing_blocked_and_version_mismatch(setup, case, concepts):
    svc, actor, _, _ = setup
    with pytest.raises(DomainError, match="verified SKU"):
        VisualService(svc).create(
            actor,
            case["id"],
            VisualRequest(concept_id=concepts[0]["id"], intent="listing", requirements="Pretend actual item"),
            "listing",
        )
    client = CreativeEngineClient(
        "http://127.0.0.1:4311",
        "fixture",
        transport=httpx.MockTransport(
            lambda r: httpx.Response(200, json={"schema_version": "9.0.0", "info": {"version": "9.0.0"}})
        ),
    )
    with pytest.raises(DomainError, match="1.0.0"):
        client.verify()
    with pytest.raises(DomainError):
        CreativeEngineClient("http://169.254.169.254", "fixture")


def test_asset_hash_tamper_blocks_review(setup, visual):
    svc, actor, _, _ = setup
    service, task = visual
    approve_plan(service, actor, task)
    service.submit(actor, task["id"])
    service.sync(actor, task["id"])
    asset = service.asset(actor, service.get(actor, task["id"])["assets"][0]["id"])
    svc.objects.path(asset["sha256"]).write_bytes(b"corrupt")
    with pytest.raises(DomainError, match="hash changed"):
        service.review(
            actor,
            asset["id"],
            ReviewRequest(
                expected_subject_hash=asset["subject_hash"],
                decision="approved",
                reason="Bad bytes cannot pass",
            ),
            "corrupt-review",
        )


def test_real_local_http_mock_contract(setup, case, concepts):
    import os

    if os.getenv("LAUNCHCASE_TEST_ENGINE_HTTP") != "1":
        pytest.skip("Explicit isolated local Engine HTTP test not enabled")
    svc, actor, _, _ = setup
    decide(svc, actor, case["id"], "G2", concepts[0]["id"], "select")
    settings = replace(
        svc.settings,
        creative_mode="http",
        creative_url=os.getenv("LAUNCHCASE_TEST_ENGINE_URL", "http://127.0.0.1:4311"),
        creative_token=os.getenv("LAUNCHCASE_TEST_ENGINE_TOKEN", "launchcase-isolated-test-token"),
    )
    service = VisualService(CaseService(settings))
    task = service.create(
        actor,
        case["id"],
        VisualRequest(
            concept_id=concepts[0]["id"],
            requirements="SYNTHETIC internal conceptual pet furniture; no safety claims",
        ),
        "http-visual",
    )
    assert task["state"] == "awaiting_plan_review", task
    assert task["plan"]["plan"]["source"]["system"] == "launchcase"
    approve_plan(service, actor, task)
    submitted = service.submit(actor, task["id"])
    assert submitted["remote"]["batch_id"]
    for _ in range(30):
        service.sync(actor, task["id"])
        detail = service.get(actor, task["id"])
        if detail["assets"]:
            break
        time.sleep(0.1)
    assert detail["assets"], detail
    asset = service.asset(actor, detail["assets"][0]["id"])
    assert asset["identity"] == "mock"
    assert asset["qa"]["vision"]["status"] != "completed"
    service.review(
        actor,
        asset["id"],
        ReviewRequest(
            expected_subject_hash=asset["subject_hash"],
            decision="approved",
            reason="Synthetic HTTP contract asset review only",
        ),
        "http-asset-review",
    )
    assert service.get(actor, task["id"])["state"] == "approved"
