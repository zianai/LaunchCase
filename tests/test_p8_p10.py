"""P8-P10 isolated contract regressions; TEST ONLY, never human business evidence."""

import pytest
from test_handoff import real_mode  # noqa: F401
from test_p7_sku import original, sku  # noqa: F401

from launchcase.agents.runtime import FakeSDKRunner
from launchcase.application.research import ResearchService
from launchcase.domain.common import DomainError, uid
from launchcase.domain.contracts import RightsChange
from launchcase.infrastructure.models import Artifact, Evidence
from launchcase.infrastructure.tasks import TaskManager
from launchcase.workflow.graph import enqueue_run, execute_task


def test_sku_read_preview_tenant_and_revoked_rights(sku):  # noqa: F811
    svc, actor, case, client, upload, *_ = sku
    src = original(sku)
    listing = client.get(f"/api/v1/product-cases/{case['id']}/sku-images")
    assert listing.status_code == 200
    assert listing.json()["items"][0]["subject_hash"] == src["subject_hash"]
    preview = client.get(f"/api/v1/sku-images/{src['id']}/content")
    assert preview.status_code == 200
    assert preview.headers["content-type"] == "image/png"
    assert preview.headers["x-content-type-options"] == "nosniff"
    token, _ = svc.provision("other-p8-tenant", "TEST ONLY outsider", "owner", False)
    assert (
        client.get(
            f"/api/v1/sku-images/{src['id']}/content", headers={"Authorization": f"Bearer {token}"}
        ).status_code
        == 404
    )
    svc.change_rights(
        actor,
        upload.rights.source_id,
        RightsChange(
            expected_revision=svc.get_case(actor, case["id"])["revision"],
            rights_status="revoked",
            reason="TEST ONLY withdrawal",
        ),
        uid(),
    )
    listing = client.get(f"/api/v1/product-cases/{case['id']}/sku-images").json()["items"]
    assert listing[0]["eligibility"]["current"] is False
    assert listing[0]["eligibility"]["reason"] == "RIGHTS_REQUIRED"


def test_research_provenance_and_source_revocation(setup, case, imported):
    svc, actor, _, client = setup
    task = enqueue_run(svc, actor, case["id"], "research", uid())
    assert execute_task(svc, actor, task["id"])["status"] == "succeeded"
    insight = svc.list_scoped(actor, case["id"], Artifact, kind="Insight")[0]
    response = client.get(f"/api/v1/insights/{insight['id']}/provenance")
    assert response.status_code == 200
    proof = response.json()
    assert proof["current"] is True and proof["reviewer_decision"] == "pending"
    assert proof["model_id"] == "deterministic-sdk-test"
    assert len(proof["prompt_hash"]) == len(proof["input_hash"]) == 64
    assert proof["skill_versions"] and proof["citations"]
    assert all(
        c["source_locator"] and c["excerpt"] and len(c["source_sha256"]) == 64 for c in proof["citations"]
    )
    svc.change_rights(
        actor,
        imported[1]["source_id"],
        RightsChange(
            expected_revision=svc.get_case(actor, case["id"])["revision"],
            rights_status="revoked",
            reason="TEST ONLY revoked source",
        ),
        uid(),
    )
    assert client.get(f"/api/v1/insights/{insight['id']}/provenance").json()["current"] is False


def test_research_rejects_nonexistent_citation_even_for_injected_runner(setup, case, imported):
    svc, actor, _, _ = setup

    class InvalidRunner:
        def run(self, evidence):
            result = FakeSDKRunner().run(evidence)
            result["output"]["themes"][0]["supporting_evidence_refs"] = ["other-case-or-missing"]
            return result

    task = enqueue_run(svc, actor, case["id"], "research", uid())
    claim = TaskManager(svc).claim(actor, task["id"], "test")
    with pytest.raises(DomainError, match="citation"):
        ResearchService(svc, InvalidRunner()).execute(actor, task["id"], claim["fence"])
    assert not svc.list_scoped(actor, case["id"], Artifact, kind="Insight")


def test_research_rejects_unlocatable_source_row(setup, case, imported):
    svc, actor, _, _ = setup
    evidence = svc.list_scoped(actor, case["id"], Evidence)[0]
    with svc.write() as s:
        row = svc.get_row(s, Evidence, actor, evidence["id"])
        row.source_locator = "row:999999"
    task = enqueue_run(svc, actor, case["id"], "research", uid())
    with pytest.raises(DomainError) as error:
        execute_task(svc, actor, task["id"])
    assert error.value.code == "CITATION_UNLOCATABLE"
    result = TaskManager(svc).get(actor, task["id"])
    assert result["status"] == "failed" and result["error_code"] == "CITATION_UNLOCATABLE"


def test_pilot_export_is_versioned_and_never_business_approval(setup, case, imported):
    svc, actor, _, client = setup
    execute_task(svc, actor, enqueue_run(svc, actor, case["id"], "research", uid())["id"])
    response = client.get(f"/api/v1/product-cases/{case['id']}/pilot-export")
    assert response.status_code == 200
    data = response.json()
    assert data["business_pilot_accepted"] is False and data["synthetic"] is True
    assert data["metrics"]["paired_time_saved_ratio"] is None
    assert data["source_manifest"] and data["insights"]
    again = client.get(f"/api/v1/product-cases/{case['id']}/pilot-export").json()
    assert again["subject_sha256"] == data["subject_sha256"]


@pytest.mark.parametrize("change", ["no_cutout", "wrong_truth", "foreign_source"])
def test_strict_plan_rejects_missing_or_foreign_dependencies(sku, change):  # noqa: F811
    from test_p7_sku import visual_request

    from launchcase.application.sku_visuals import SkuVisualService
    from launchcase.application.visuals import VisualService
    from launchcase.infrastructure.models import SourceDocument

    svc, actor, case, _, _, *_ = sku
    source = original(sku)
    request = visual_request(sku, source)
    if change == "no_cutout":
        with svc.write() as session:
            image = svc.get_row(session, SourceDocument, actor, source["id"])
            image.metadata_json = {**image.metadata_json, "kind": "product_photo"}
            # Re-review the changed subject to isolate missing transparent cutout.
        from launchcase.domain.contracts import ReviewRequest

        with svc.sessions() as session:
            image = svc.get_row(session, SourceDocument, actor, source["id"])
            subject = SkuVisualService(svc).describe(image)["subject_hash"]
        SkuVisualService(svc).review(
            actor,
            source["id"],
            ReviewRequest(
                expected_subject_hash=subject, decision="approved", reason="TEST ONLY photo review"
            ),
            uid(),
        )
    elif change == "wrong_truth":
        request.truth_snapshot_id = "foreign-or-missing"
    else:
        with svc.write() as session:
            image = svc.get_row(session, SourceDocument, actor, source["id"])
            image.tenant_id = "foreign-tenant"
    with pytest.raises(DomainError) as denied:
        VisualService(svc).create(actor, case["id"], request, uid())
    assert denied.value.code in {"CUTOUT_REQUIRED", "TRUTH_MISMATCH", "NOT_FOUND"}


def test_sku_upload_paths_format_and_object_symlink(sku, tmp_path):  # noqa: F811
    from pydantic import ValidationError

    from launchcase.application.sku_visuals import SkuVisualService
    from launchcase.domain.contracts import SkuImageImport

    svc, actor, case, _, upload, *_ = sku
    for filename in ("../file.png", "/private/file.png", "dir\\file.png", "payload.svg"):
        with pytest.raises(ValidationError):
            SkuImageImport.model_validate({**upload.model_dump(), "filename": filename})
    with pytest.raises(DomainError, match="format"):
        SkuVisualService(svc).upload(
            actor, case["id"], upload.model_copy(update={"filename": "wrong.jpg"}), uid()
        )
    untouched = tmp_path / "TEST-ONLY-sensitive"
    untouched.write_bytes(b"TEST ONLY never overwrite")
    svc.objects.path(upload.original_sha256).symlink_to(untouched)
    with pytest.raises(DomainError, match="symlink"):
        SkuVisualService(svc).upload(actor, case["id"], upload, uid())
    assert untouched.read_bytes() == b"TEST ONLY never overwrite"


@pytest.mark.parametrize("change", ["spec", "rule"])
def test_g4_g5_receipt_and_pack_stale_after_dependency_revision(real_mode, change):  # noqa: F811
    from conftest import decide
    from test_handoff import ready

    from launchcase.application.feasibility import FeasibilityService
    from launchcase.application.launchpacks import LaunchPackService
    from launchcase.application.products import ProductService
    from launchcase.domain.contracts import SpecClaim, SpecRevision

    svc, actor, case, _, client = real_mode
    pack, prep, rule_request = ready(real_mode)
    packs = LaunchPackService(svc)
    packs.prepare(actor, case["id"], prep, uid())
    decide(svc, actor, case["id"], "G5", pack["id"], "internal_handoff")
    assert client.get(f"/api/v1/launch-packs/{pack['id']}/handoff-receipt").status_code == 200
    if change == "spec":
        product = ProductService(svc)
        with svc.sessions() as session:
            concept = product.current(session, actor, case["id"], "G2", {"select"}).subject_id
            spec = product.latest_spec(session, actor, case["id"], concept)
            spec_hash = spec.sha256
        product.revise_spec(
            actor,
            case["id"],
            concept,
            SpecRevision(
                expected_subject_hash=spec_hash,
                claims=[SpecClaim(name="material", value="TEST ONLY revision", status="proposed")],
                reason="TEST ONLY revision invalidates decisions",
            ),
            uid(),
        )
    else:
        rule_request.revision = "TEST ONLY revision 2"
        FeasibilityService(svc).rule(actor, case["id"], rule_request, uid())
    assert client.get(f"/api/v1/launch-packs/{pack['id']}/handoff-receipt").status_code == 409
    with pytest.raises(DomainError):
        packs.export(actor, pack["id"])
    decisions = ProductService(svc).decisions(actor, case["id"])
    assert any(g["gate"] == "G5" and g["status"] == "stale" for g in decisions)
    assert svc.list_scoped(actor, case["id"], Artifact, kind="LaunchPack")


def test_synthetic_case_cannot_export_mixed_real_sources_without_grant(setup, case, imported):
    from launchcase.domain.contracts import SourceImport

    svc, actor, _, client = setup
    svc.import_source(
        actor,
        case["id"],
        SourceImport(
            filename="TEST-ONLY-real-mode-source.txt",
            content="TEST ONLY fictional source exercising mixed classification",
            source_type="spec",
            is_synthetic=False,
            rights_status="authorized",
        ),
        uid(),
    )
    assert svc.get_case(actor, case["id"])["is_synthetic"] is True
    response = client.get(f"/api/v1/product-cases/{case['id']}/pilot-export")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "BLOCKED_EXTERNAL"


@pytest.mark.parametrize("mutation", ["deleted_source", "foreign_source"])
def test_insight_source_loss_or_tenant_change_marks_stale(setup, case, imported, mutation):
    from launchcase.infrastructure.models import SourceDocument

    svc, actor, _, client = setup
    execute_task(svc, actor, enqueue_run(svc, actor, case["id"], "research", uid())["id"])
    insight = svc.list_scoped(actor, case["id"], Artifact, kind="Insight")[0]
    with svc.write() as session:
        source = svc.get_row(session, SourceDocument, actor, imported[1]["source_id"])
        if mutation == "deleted_source":
            from sqlalchemy import delete

            session.execute(delete(Evidence).where(Evidence.source_id == source.id))
            session.delete(source)
        else:
            source.tenant_id = "foreign-tenant"
    proof = client.get(f"/api/v1/insights/{insight['id']}/provenance")
    assert proof.status_code == 200
    assert proof.json()["current"] is False
    assert proof.json()["business_accepted"] is False


def test_wrong_case_citation_rejected_even_if_id_exists(setup, case, imported, brief):
    svc, actor, _, _ = setup
    second = svc.create_case(actor, brief, uid())
    svc.import_source(actor, second["id"], imported[0], uid())
    foreign = svc.list_scoped(actor, second["id"], Evidence)[0]["id"]

    class WrongCaseRunner:
        def run(self, evidence):
            result = FakeSDKRunner().run(evidence)
            result["output"]["themes"][0]["supporting_evidence_refs"] = [foreign]
            return result

    task = enqueue_run(svc, actor, case["id"], "research", uid())
    claim = TaskManager(svc).claim(actor, task["id"], "test")
    with pytest.raises(DomainError):
        ResearchService(svc, WrongCaseRunner()).execute(actor, task["id"], claim["fence"])
    assert not svc.list_scoped(actor, case["id"], Artifact, kind="Insight")


def test_derived_asset_cannot_be_original_or_sample_evidence(sku):  # noqa: F811
    import base64

    from launchcase.application.feasibility import FeasibilityService
    from launchcase.application.sku_visuals import SkuVisualService
    from launchcase.application.visuals import VisualService
    from launchcase.domain.contracts import FactAttestation, ReviewRequest, SampleAttestation, VisualRequest

    svc, actor, case, _, upload, sample, _, concept = sku
    visuals = VisualService(svc)
    task = visuals.create(
        actor,
        case["id"],
        VisualRequest(concept_id=concept, requirements="TEST ONLY exploratory concept image"),
        uid(),
    )
    visuals.approve(
        actor,
        task["id"],
        ReviewRequest(
            expected_subject_hash=task["plan_hash"], decision="approved", reason="TEST ONLY concept plan"
        ),
        uid(),
    )
    visuals.submit(actor, task["id"])
    visuals.sync(actor, task["id"])
    asset = visuals.get(actor, task["id"])["assets"][0]
    raw = visuals.asset(actor, asset["id"], True)
    with pytest.raises(DomainError) as denied:
        SkuVisualService(svc).upload(
            actor,
            case["id"],
            upload.model_copy(
                update={
                    "filename": "derived.png",
                    "data_base64": base64.b64encode(raw).decode(),
                    "original_sha256": asset["sha256"],
                    "kind": "product_photo",
                }
            ),
            uid(),
        )
    assert denied.value.code == "DERIVED_ASSET"
    with pytest.raises(DomainError):
        FeasibilityService(svc).sample(
            actor,
            case["id"],
            SampleAttestation(
                expected_spec_hash=sample["data"]["spec_hash"],
                sample_identifier="TEST-ONLY-SKU-1",
                test_method="TEST ONLY generated image cannot prove measurement",
                facts=[
                    FactAttestation(
                        name="width", value="40 cm", source_id=asset["id"], exact_excerpt="40 cm mock image"
                    )
                ],
                tested_at="2026-10-01T00:00:00Z",
                responsible_person="TEST ONLY",
                limitations="TEST ONLY no real sample",
            ),
            uid(),
        )


def test_voc_dedup_preserves_independent_ids_dates_and_variant_conflicts(setup, case):
    from launchcase.domain.contracts import SourceImport

    svc, actor, _, _ = setup
    text = (
        "review_id,product_id,variant,review_date,review_text\n"
        "A,SKU-A,small,2026-10-01,Assembly is hard\n"
        "A,SKU-A,small,2026-10-01,Assembly is hard\n"
        "B,SKU-A,small,2026-10-02,Assembly is hard\n"
        "C,SKU-A,large,2026-10-03,Assembly is easy\n"
    )
    request = SourceImport(
        filename="TEST-ONLY-conflicts.csv",
        content=text,
        source_type="review",
        rights_status="synthetic_fixture",
        is_synthetic=True,
    )
    first = svc.import_source(actor, case["id"], request, uid())
    assert first["rows_imported"] == 3 and first["rows_skipped"] == 1
    assert svc.import_source(actor, case["id"], request, uid())["rows_imported"] == 0
    rows = svc.list_scoped(actor, case["id"], Evidence)
    assert {row["data"]["raw"]["review_id"] for row in rows} == {"A", "B", "C"}
    assert {row["data"]["variant"] for row in rows} == {"small", "large"}
    execute_task(svc, actor, enqueue_run(svc, actor, case["id"], "research", uid())["id"])
    research = svc.list_scoped(actor, case["id"], Artifact, kind="Research")[0]
    assert research["data"]["output"]["category_prevalence"] is None
    assert research["data"]["sufficiency"]["status"] == "needs_more_data"


def test_real_pilot_export_cannot_borrow_synthetic_grant_context(real_mode):  # noqa: F811
    from launchcase.application.pilot import export_pilot

    svc, actor, case, _, _ = real_mode

    class SyntheticContext:
        def context(self):
            return {"data_classification": "synthetic"}

        def validate(self, request, upper):
            raise AssertionError("Synthetic context must be rejected before grant validation/export")

    with pytest.raises(DomainError) as denied:
        export_pilot(svc, actor, case["id"], SyntheticContext())
    assert denied.value.code == "BLOCKED_EXTERNAL"


def test_pilot_manifest_limit_never_silently_hides_real_source(setup, case):
    from launchcase.domain.common import digest
    from launchcase.infrastructure.models import SourceDocument

    svc, actor, _, client = setup
    with svc.write() as session:
        session.add_all(
            [
                SourceDocument(
                    tenant_id=actor.tenant_id,
                    case_id=case["id"],
                    filename=f"TEST-ONLY-{index}.txt",
                    sha256=digest(str(index).encode()),
                    source_type="spec",
                    rights_status="synthetic_fixture" if index < 5000 else "authorized",
                    is_synthetic=index < 5000,
                    metadata_json={},
                )
                for index in range(5001)
            ]
        )
    response = client.get(f"/api/v1/product-cases/{case['id']}/pilot-export")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PILOT_EXPORT_LIMIT"
    assert "source_manifest" not in response.json()
