"""Isolated software fixtures exercise real-mode contracts; no real product approval."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from conftest import FIXTURE, decide
from fastapi.testclient import TestClient

from launchcase.application.feasibility import FeasibilityService
from launchcase.application.launchpacks import LaunchPackService
from launchcase.application.products import ProductService
from launchcase.domain.common import DomainError, uid
from launchcase.domain.contracts import (
    FactAttestation,
    HandoffPreparation,
    RightsChange,
    RuleAttestation,
    SampleAttestation,
    SourceImport,
)
from launchcase.infrastructure.models import Artifact
from launchcase.workflow.graph import enqueue_run, execute_task


@pytest.fixture
def real_mode(setup, brief):
    svc, _, other, client = setup
    token, actor = svc.provision("isolated-contract-test", "TEST ONLY reviewer", "owner", False)
    brief.title = "TEST ONLY real-mode contract; no actual product"
    brief.data_policy.is_synthetic = False
    brief.data_policy.rights_status = "authorized"
    brief.data_policy.data_origin = "isolated software test; never business evidence"
    case = svc.create_case(actor, brief, uid())
    # Intentionally unflagged fictional inputs to exercise real-mode API in a disposable DB.
    text = (FIXTURE / "synthetic-voc.csv").read_text().replace("true", "false")
    svc.import_source(
        actor,
        case["id"],
        SourceImport(
            filename="test-only.csv",
            content=text,
            source_type="review",
            rights_status="authorized",
            is_synthetic=False,
        ),
        uid(),
    )
    task = enqueue_run(svc, actor, case["id"], "research", uid())
    execute_task(svc, actor, task["id"])
    opp = svc.list_scoped(actor, case["id"], Artifact, kind="Opportunity")[0]
    decide(svc, actor, case["id"], "G1", opp["id"], "accept")
    task = enqueue_run(svc, actor, case["id"], "concepts", uid())
    execute_task(svc, actor, task["id"])
    concept = svc.list_scoped(actor, case["id"], Artifact, kind="Concept")[0]
    decide(svc, actor, case["id"], "G2", concept["id"], "select")
    feasibility = FeasibilityService(svc).evaluate(actor, case["id"], None, uid())
    decide(svc, actor, case["id"], "G3", feasibility["id"], "sample_validation")
    with svc.sessions() as s:
        spec = ProductService(svc).latest_spec(s, actor, case["id"], concept["id"])
        spec_hash = spec.sha256
    source = svc.import_source(
        actor,
        case["id"],
        SourceImport(
            filename="TEST-ONLY-sample.txt",
            content="TEST ONLY fixture: measured width 40 cm. No actual sample exists.",
            source_type="sample",
            rights_status="authorized",
            is_synthetic=False,
        ),
        uid(),
    )
    request = SampleAttestation(
        expected_spec_hash=spec_hash,
        sample_identifier="TEST-ONLY-SKU-1",
        test_method="TEST ONLY fixture measurement method; no real measurement.",
        facts=[
            FactAttestation(
                name="width",
                value="40 cm",
                source_id=source["source_id"],
                exact_excerpt="TEST ONLY fixture: measured width 40 cm.",
            )
        ],
        tested_at=(datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
        responsible_person="TEST ONLY",
        limitations="Fictional fixture. No actual testing, demand validation or external approval.",
    )
    return svc, actor, case, request, TestClient(client.app, headers={"Authorization": f"Bearer {token}"})


def add_rule(svc, actor, case):
    folder = Path(__file__).resolve().parents[1] / "fixtures/public-references"
    ref = json.loads((folder / "manifest.json").read_text())["references"][0]
    text = (folder / ref["file"]).read_text()
    source = svc.import_source(
        actor,
        case["id"],
        SourceImport(
            filename=ref["file"],
            content=text,
            source_type="rule",
            rights_status="authorized",
            is_synthetic=False,
            source_url=ref["url"],
        ),
        uid(),
    )
    now = datetime.now(timezone.utc)
    request = RuleAttestation(
        source_id=source["source_id"],
        authority_url=ref["url"],
        product_scope="pet furniture and dog crate furniture",
        revision="TEST ONLY applicability review",
        effective_at=(now - timedelta(days=1)).isoformat(),
        review_due_at=(now + timedelta(days=1)).isoformat(),
        exact_excerpt=text.strip(),
        applicability_reason="TEST ONLY contract review, not a compliance conclusion.",
    )
    return FeasibilityService(svc).rule(actor, case["id"], request, uid()), request


def ready(real_mode):
    svc, actor, case, request, client = real_mode
    sample = FeasibilityService(svc).sample(actor, case["id"], request, uid())
    decide(svc, actor, case["id"], "G4", sample["id"], "verify_sample")
    rule, rule_request = add_rule(svc, actor, case)
    pack = LaunchPackService(svc).build(actor, case["id"], uid())
    prep = HandoffPreparation(
        pack_id=pack["id"],
        expected_pack_hash=pack["sha256"],
        rule_ids=[rule["id"]],
        responsible_person="TEST ONLY owner",
        risk_acceptance="All costs unknown; TEST ONLY owner must obtain quotes before any business decision.",
        excluded_claims="No tested performance, market demand, safety or certification claims.",
        internal_assets_only=True,
    )
    return pack, prep, rule_request


def test_g4_g5_api_handoff_and_stable_export(real_mode):
    svc, actor, case, request, client = real_mode
    pack, prep, _ = ready(real_mode)
    response = client.post(
        f"/api/v1/product-cases/{case['id']}/handoff-preparations",
        json=prep.model_dump(),
        headers={"Idempotency-Key": "prep"},
    )
    assert response.status_code == 200, response.text
    assert (
        client.post(
            f"/api/v1/product-cases/{case['id']}/handoff-preparations",
            json=prep.model_dump(),
            headers={"Idempotency-Key": "prep"},
        ).json()["id"]
        == response.json()["id"]
    )
    decide(svc, actor, case["id"], "G5", pack["id"], "internal_handoff")
    task = enqueue_run(svc, actor, case["id"], "handoff", uid())
    result = execute_task(svc, actor, task["id"])
    assert result["result"]["waiting_for"] == "complete_internal_handoff"
    receipt = client.get(f"/api/v1/launch-packs/{pack['id']}/handoff-receipt")
    assert receipt.status_code == 200, receipt.text
    assert receipt.json()["publishable"] is False
    import io
    import zipfile

    response = client.get(f"/api/v1/launch-packs/{pack['id']}/handoff-export")
    assert response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert "approval.json" in archive.namelist()
        assert any(name.startswith("rules/") for name in archive.namelist())
        assert json.loads(archive.read("manifest.json"))["publishable"] is False
    assert LaunchPackService(svc).read(actor, pack["id"])["current"]
    exported = json.loads(LaunchPackService(svc).export(actor, pack["id"]))
    assert exported["product_truth"]["data"]["facts"][0]["value"] == "40 cm"
    assert not any("G4:" in b for b in exported["blockers"])
    assert client.post("/api/v1/publish").status_code == 404


@pytest.mark.parametrize("mutation", ["web", "invented_value", "future", "wrong_spec", "missing_identity"])
def test_g4_rejects_invalid_sample(real_mode, mutation):
    svc, actor, case, req, _ = real_mode
    if mutation == "web":
        with svc.sessions.begin() as s:
            from launchcase.infrastructure.models import SourceDocument

            source = s.get(SourceDocument, req.facts[0].source_id)
            source.metadata_json = {**source.metadata_json, "source_url": "https://www.cpsc.gov/example"}
    elif mutation == "invented_value":
        req.facts[0].value = "999 kg"
    elif mutation == "future":
        req.tested_at = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    elif mutation == "wrong_spec":
        req.expected_spec_hash = "0" * 64
    else:
        req.sample_identifier = None
    with pytest.raises(DomainError):
        FeasibilityService(svc).sample(actor, case["id"], req, uid())


@pytest.mark.parametrize("mutation", ["rights", "expiry", "sample", "preparation"])
def test_g5_invalidation(real_mode, mutation, monkeypatch):
    svc, actor, case, req, client = real_mode
    pack, prep, rule_request = ready(real_mode)
    LaunchPackService(svc).prepare(actor, case["id"], prep, uid())
    decide(svc, actor, case["id"], "G5", pack["id"], "internal_handoff")
    if mutation == "rights":
        src = svc.get_case(actor, case["id"])
        svc.change_rights(
            actor,
            rule_request.source_id,
            RightsChange(
                expected_revision=src["revision"],
                rights_status="revoked",
                reason="TEST ONLY revoke source rights",
            ),
            uid(),
        )
    elif mutation == "expiry":

        class FutureClock:
            @staticmethod
            def now(tz):
                return datetime.now(tz) + timedelta(days=2)

        monkeypatch.setattr("launchcase.application.launchpacks.datetime", FutureClock)
    elif mutation == "sample":
        FeasibilityService(svc).sample(actor, case["id"], req, uid())
    else:
        prep.risk_acceptance = "Revised TEST ONLY risk owner and limitations; requires new approval."
        LaunchPackService(svc).prepare(actor, case["id"], prep, uid())
    assert client.get(f"/api/v1/launch-packs/{pack['id']}/handoff-receipt").status_code == 409
    assert (
        next(g for g in ProductService(svc).decisions(actor, case["id"]) if g["gate"] == "G5")["status"]
        == "stale"
    )


def test_rule_url_scope_and_cross_tenant(real_mode):
    svc, actor, case, req, client = real_mode
    rule, rr = add_rule(svc, actor, case)
    rr.authority_url = "https://www.ftc.gov/different"
    with pytest.raises(DomainError, match="Original official"):
        FeasibilityService(svc).rule(actor, case["id"], rr, uid())
    _, other = svc.provision("other-tenant", "TEST ONLY", "owner", False)
    with pytest.raises(DomainError):
        svc.list_scoped(other, case["id"], Artifact, kind="SampleValidation")


def test_unprepared_handoff_and_old_pack_rejected(real_mode):
    svc, actor, case, req, _ = real_mode
    old = LaunchPackService(svc).build(actor, case["id"], uid())
    pack, prep, _ = ready(real_mode)
    with pytest.raises(DomainError):
        decide(svc, actor, case["id"], "G5", pack["id"], "internal_handoff")
    with pytest.raises(DomainError):
        decide(svc, actor, case["id"], "G5", old["id"], "internal_handoff")
