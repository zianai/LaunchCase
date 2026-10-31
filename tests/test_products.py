import pytest
from conftest import decide
from pydantic import ValidationError

from launchcase.application.products import ProductService
from launchcase.domain.common import DomainError
from launchcase.domain.contracts import GateRequest, RightsChange, SpecClaim, SpecRevision
from launchcase.infrastructure.models import Artifact
from launchcase.workflow.graph import enqueue_run


def test_two_distinct_proposed_concepts_and_g2(setup, case, concepts):
    svc, actor, _, _ = setup
    assert len(concepts) == 2
    assert concepts[0]["data"]["design_intent"] != concepts[1]["data"]["design_intent"]
    assert all(x["data"]["classification"] == "proposal" for x in concepts)
    specs = svc.list_scoped(actor, case["id"], Artifact, kind="ProductSpec")
    assert all(c["value"] is None for sp in specs for c in sp["data"]["claims"] if c["name"] == "load_rating")
    decision = decide(svc, actor, case["id"], "G2", concepts[0]["id"], "select")
    assert decision["is_synthetic"]
    assert svc.get_case(actor, case["id"])["stage"] == "feasibility_review"


def test_spec_revision_stales_g2_preserves_history_and_rollback(setup, case, concepts):
    svc, actor, _, _ = setup
    product = ProductService(svc)
    concept = concepts[0]
    decide(svc, actor, case["id"], "G2", concept["id"], "select")
    spec = next(
        x
        for x in svc.list_scoped(actor, case["id"], Artifact, kind="ProductSpec")
        if x["data"]["concept_id"] == concept["id"]
    )
    revision = product.revise_spec(
        actor,
        case["id"],
        concept["id"],
        SpecRevision(
            expected_subject_hash=spec["sha256"],
            claims=[SpecClaim(name="material", value="Proposed plywood", status="proposed")],
            reason="Proposal revision only",
        ),
        "spec-change",
    )
    gates = product.decisions(actor, case["id"])
    assert next(x for x in gates if x["gate"] == "G2")["status"] == "stale"
    assert product.spec_diff(actor, case["id"], spec["id"], revision["id"])["changes"]
    rollback = product.revise_spec(
        actor,
        case["id"],
        concept["id"],
        SpecRevision(
            expected_subject_hash=revision["sha256"],
            claims=[SpecClaim.model_validate(c) for c in spec["data"]["claims"]],
            reason="Rollback as new immutable version",
        ),
        "rollback",
    )
    assert rollback["data"]["parent_spec_id"] == revision["id"]
    assert len(svc.list_scoped(actor, case["id"], Artifact, kind="ProductSpec")) == 4


def test_stale_hash_and_agent_self_approval(setup, case, concepts):
    svc, actor, _, client = setup
    product = ProductService(svc)
    req = GateRequest(
        decision="select",
        subject_type="concept",
        subject_id=concepts[0]["id"],
        expected_subject_hash="0" * 64,
        reason="Invalid stale review",
    )
    with pytest.raises(DomainError) as err:
        product.decide(actor, case["id"], "G2", req, "stale")
    assert err.value.status == 409
    _, agent = svc.provision("tenant-a", "Agent", "agent", True)
    with pytest.raises(DomainError) as err:
        product.decide(agent, case["id"], "G2", req, "agent")
    assert err.value.status == 403
    with pytest.raises(ValidationError):
        SpecClaim(name="certification", value="certified", status="verified")
    with pytest.raises(ValidationError):
        GateRequest.model_validate({**req.model_dump(), "reviewer": "human"})


def test_revocation_stales_downstream_and_sse_replay(setup, case, imported, concepts):
    svc, actor, _, client = setup
    decide(svc, actor, case["id"], "G2", concepts[0]["id"], "select")
    current = svc.get_case(actor, case["id"])
    svc.change_rights(
        actor,
        imported[1]["source_id"],
        RightsChange(
            expected_revision=current["revision"], rights_status="revoked", reason="Rights withdrawn"
        ),
        "revoke",
    )
    assert all(x["status"] == "stale" for x in ProductService(svc).decisions(actor, case["id"]))
    with pytest.raises(DomainError):
        enqueue_run(svc, actor, case["id"], "concepts", "cannot-run")
    response = client.get(f"/api/v1/product-cases/{case['id']}/events?after=3")
    assert response.status_code == 200 and "id: 1\n" not in response.text
    assert "source.rights_changed" in response.text


def test_concepts_require_g1(setup, case, imported):
    svc, actor, _, _ = setup
    with pytest.raises(DomainError, match="G1"):
        enqueue_run(svc, actor, case["id"], "concepts", "too-early")
