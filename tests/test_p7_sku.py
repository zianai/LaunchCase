# ruff: noqa: F811
# pytest injects the imported fixture by name.
"""TEST ONLY original-SKU contracts in disposable DB; no genuine photos or approvals."""

import base64
import io
import os
import time
from datetime import datetime, timedelta, timezone

import pytest
from conftest import decide
from PIL import Image, ImageDraw
from test_handoff import add_rule, real_mode  # noqa: F401

from launchcase.application.feasibility import FeasibilityService
from launchcase.application.sku_visuals import SkuVisualService, raster
from launchcase.application.visuals import VisualService
from launchcase.domain.common import DomainError, digest, uid
from launchcase.domain.contracts import (
    ReviewRequest,
    RightsChange,
    RightsProof,
    SkuImageImport,
    SourceImport,
    VisualRequest,
)
from launchcase.integrations.creative import CreativeEngineClient


@pytest.fixture
def sku(real_mode):
    svc, actor, case, request, client = real_mode
    request.facts[0].external_allowed = True
    sample = FeasibilityService(svc).sample(actor, case["id"], request, uid())
    decide(svc, actor, case["id"], "G4", sample["id"], "verify_sample")
    rule, _ = add_rule(svc, actor, case)
    text = "TEST ONLY fixture rights: owner permits internal Listing composition and image transfer to the isolated local Engine."
    rights = svc.import_source(
        actor,
        case["id"],
        SourceImport(
            filename="test-rights.txt",
            content=text,
            source_type="rights",
            rights_status="authorized",
            is_synthetic=False,
        ),
        uid(),
    )
    image = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    ImageDraw.Draw(image).rectangle((32, 16, 96, 112), fill=(185, 92, 44, 255))
    out = io.BytesIO()
    image.save(out, format="PNG")
    raw = out.getvalue()
    upload = SkuImageImport(
        sku=request.sample_identifier,
        filename="TEST-ONLY-cutout.png",
        data_base64=base64.b64encode(raw).decode(),
        original_sha256=digest(raw),
        kind="cutout",
        is_synthetic=False,
        rights=RightsProof(
            source_id=rights["source_id"],
            exact_excerpt=text,
            expires_at_utc=(datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            external_allowed=True,
        ),
    )
    from launchcase.application.products import ProductService

    with svc.sessions() as s:
        concept_id = ProductService(svc).current(s, actor, case["id"], "G2", {"select"}).subject_id
    return svc, actor, case, client, upload, sample, rule, concept_id


def original(sku):
    svc, actor, case, _, upload, _, _, _ = sku
    api = SkuVisualService(svc)
    src = api.upload(actor, case["id"], upload, uid())
    api.review(
        actor,
        src["id"],
        ReviewRequest(
            expected_subject_hash=src["subject_hash"],
            decision="approved",
            reason="TEST ONLY verification of original fixture bytes",
        ),
        uid(),
    )
    return src


def visual_request(sku, src):
    _, _, _, _, _, sample, rule, concept = sku
    return VisualRequest(
        concept_id=concept,
        intent="listing",
        requirements="Internal strict SKU layout; no publication.",
        source_asset_ids=[src["id"]],
        truth_snapshot_id=sample["data"]["truth_id"],
        platform_rule_id=rule["id"],
        allowed_changes=["background", "layout"],
    )


def test_original_upload_rights_identity_hash_and_tenant(sku):
    svc, actor, case, client, upload, _, _, _ = sku
    response = client.post(
        f"/api/v1/product-cases/{case['id']}/sku-images",
        json=upload.model_dump(),
        headers={"Idempotency-Key": uid()},
    )
    assert response.status_code == 200, response.text
    src = response.json()
    assert src["metadata_json"]["review"] == {}
    api = SkuVisualService(svc)
    with pytest.raises(DomainError):
        api.review(
            actor,
            src["id"],
            ReviewRequest(expected_subject_hash="a" * 64, decision="approved", reason="TEST ONLY stale hash"),
            uid(),
        )
    with svc.sessions() as s:
        from launchcase.infrastructure.models import SourceDocument

        row = svc.get_row(s, SourceDocument, actor, src["id"])
        with pytest.raises(DomainError, match="verification"):
            api.valid_source(s, actor, row)
    _, other = svc.provision("other-tenant", "TEST ONLY", "owner", False)
    with pytest.raises(DomainError):
        api.review(
            other,
            src["id"],
            ReviewRequest(
                expected_subject_hash=src["subject_hash"],
                decision="approved",
                reason="TEST ONLY wrong tenant",
            ),
            uid(),
        )


def test_missing_rights_concept_and_bad_raster(sku):
    svc, actor, case, _, upload, _, _, _ = sku
    with pytest.raises(DomainError):
        SkuVisualService(svc).upload(
            actor, case["id"], upload.model_copy(update={"original_sha256": "a" * 64}), uid()
        )
    for raw in [b"<svg>secret</svg>", b"\x89PNG\r\n\x1a\nmalformed", b"A" * (1024 * 1024 + 1)]:
        with pytest.raises(DomainError):
            raster(raw)
    bad = upload.model_copy(update={"is_synthetic": True})
    src = SkuVisualService(svc).upload(actor, case["id"], bad, uid())
    with pytest.raises(DomainError, match="concept/Mock"):
        SkuVisualService(svc).review(
            actor,
            src["id"],
            ReviewRequest(
                expected_subject_hash=src["subject_hash"],
                decision="approved",
                reason="Cannot upgrade synthetic",
            ),
            uid(),
        )


def test_sku_rights_revocation_invalidates_dependency(sku):
    svc, actor, case, _, upload, _, _, _ = sku
    src = original(sku)
    request = visual_request(sku, src)
    with svc.sessions() as s:
        snap = SkuVisualService(svc).snapshot(s, actor, case["id"], request.model_dump())
        assert snap["external_publication_authorized"] is False
    current = svc.get_case(actor, case["id"])
    svc.change_rights(
        actor,
        upload.rights.source_id,
        RightsChange(
            expected_revision=current["revision"],
            rights_status="revoked",
            reason="TEST ONLY revoke source rights",
        ),
        uid(),
    )
    with svc.sessions() as s:
        with pytest.raises(DomainError, match="rights"):
            SkuVisualService(svc).snapshot(s, actor, case["id"], request.model_dump())


def test_actual_http_strict_sku_and_review(sku, monkeypatch):
    if os.getenv("LAUNCHCASE_TEST_ENGINE_HTTP") != "1":
        pytest.skip("Requires isolated actual Node HTTP Engine")
    svc, actor, case, _, _, _, _, _ = sku
    src = original(sku)
    request = visual_request(sku, src)
    client = CreativeEngineClient(
        os.environ["LAUNCHCASE_TEST_ENGINE_URL"],
        os.getenv("LAUNCHCASE_TEST_ENGINE_TOKEN", "launchcase-isolated-test-token"),
    )
    api = VisualService(svc, client)
    task = api.create(actor, case["id"], request, uid())
    assert task["state"] == "awaiting_plan_review", task
    assert task["plan"]["plan"]["strategy"] in {"compose", "reuse"}
    assert task["plan"]["plan"]["fidelity"] == "strict"
    assert task["plan"]["plan"]["source"]["system"] == "launchcase"
    _, synthetic_reviewer = svc.provision(actor.tenant_id, "TEST ONLY synthetic reviewer", "reviewer", True)
    with pytest.raises(DomainError, match="Synthetic reviewer"):
        api.approve(
            synthetic_reviewer,
            task["id"],
            ReviewRequest(
                expected_subject_hash=task["plan_hash"],
                decision="approved",
                reason="TEST ONLY cannot promote approval",
            ),
            uid(),
        )
    assert api.get(actor, task["id"])["plan_review"] == {}
    api.approve(
        actor,
        task["id"],
        ReviewRequest(
            expected_subject_hash=task["plan_hash"],
            decision="approved",
            reason="TEST ONLY zero-cost deterministic plan",
        ),
        uid(),
    )
    sent = api.submit(actor, task["id"])
    assert api.submit(actor, task["id"])["remote"] == sent["remote"]
    for _ in range(50):
        api.sync(actor, task["id"])
        current = api.get(actor, task["id"])
        if current["assets"]:
            break
        time.sleep(0.1)
    assert current["state"] == "awaiting_asset_review", current
    asset = api.asset(actor, current["assets"][0]["id"])
    assert asset["identity"] == "real_product" and asset["review"] == {}
    assert digest(api.asset(actor, asset["id"], True)) == asset["sha256"]
    with monkeypatch.context() as patch:
        patch.setattr(api.client, "review", lambda *args: pytest.fail("Synthetic reviewer reached CE"))
        with pytest.raises(DomainError, match="Synthetic reviewer"):
            api.review(
                synthetic_reviewer,
                asset["id"],
                ReviewRequest(
                    expected_subject_hash=asset["subject_hash"],
                    decision="approved",
                    reason="TEST ONLY cannot promote approval",
                ),
                uid(),
            )
    assert api.asset(actor, asset["id"])["review"] == {}
    assert api.get(actor, task["id"])["state"] == "awaiting_asset_review"
    api.review(
        actor,
        asset["id"],
        ReviewRequest(
            expected_subject_hash=asset["subject_hash"],
            decision="approved",
            reason="TEST ONLY internal visual review; no publication",
        ),
        uid(),
    )
    assert api.get(actor, task["id"])["state"] == "approved"
    # Engine assets remain artifacts, never SourceDocument facts.
    from launchcase.infrastructure.models import SourceDocument

    assert asset["sha256"] not in [x["sha256"] for x in svc.list_scoped(actor, case["id"], SourceDocument)]

    # A real HTTP receipt never makes old source rights permanent.
    from launchcase.application.launchpacks import LaunchPackService

    pack = LaunchPackService(svc).build(actor, case["id"], uid())
    assert LaunchPackService(svc).export(actor, pack["id"])
    _, outsider = svc.provision("other-http-tenant", "TEST ONLY outsider", "owner", False)
    for read in (
        lambda: api.asset(outsider, asset["id"], True),
        lambda: LaunchPackService(svc).export(outsider, pack["id"]),
    ):
        with pytest.raises(DomainError) as denied:
            read()
        assert denied.value.status == 404
    upload = sku[4]
    svc.change_rights(
        actor,
        upload.rights.source_id,
        RightsChange(
            expected_revision=svc.get_case(actor, case["id"])["revision"],
            rights_status="revoked",
            reason="TEST ONLY revoke after asset approval",
        ),
        uid(),
    )
    assert api.get(actor, task["id"])["current"] is False
    assert api.asset(actor, asset["id"])["current"] is False
    with pytest.raises(DomainError):
        api.asset(actor, asset["id"], True)
    with pytest.raises(DomainError):
        LaunchPackService(svc).export(actor, pack["id"])
