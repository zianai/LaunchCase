import io
import json
import zipfile
from datetime import datetime, timezone

import pytest
from conftest import decide
from pydantic import ValidationError

from launchcase.application.feasibility import FeasibilityService
from launchcase.application.launchpacks import LaunchPackService
from launchcase.application.products import ProductService
from launchcase.domain.common import DomainError
from launchcase.domain.contracts import (
    CostRequest,
    FactAttestation,
    FXRate,
    GateRequest,
    MoneyInput,
    SampleAttestation,
    SourceImport,
)
from launchcase.domain.economics import COMPONENTS, calculate
from launchcase.infrastructure.models import Artifact
from launchcase.workflow.graph import enqueue_run, execute_task


def full_costs():
    return CostRequest(
        components={
            name: MoneyInput(amount="100" if index == 0 else "1", provenance="assumption")
            for index, name in enumerate(COMPONENTS)
        }
    )


def test_exact_decimal_formula_and_fixed_cost_separation():
    request = full_costs()
    request.fixed_costs["tooling"] = MoneyInput(amount="900", provenance="assumption")
    result = calculate(request, {})
    assert result["unit_contribution"] == "90.0000"
    assert result["landed_product_cost"] == "4.0000"
    assert result["fixed_costs"]["tooling"] == "900.0000"
    assert result["status"] == "conditional"


def test_missing_not_zero_and_unknown_currency():
    request = full_costs()
    request.components["referral_fee"] = MoneyInput()
    assert calculate(request, {})["unit_contribution"] is None
    request = full_costs()
    request.components["freight"] = MoneyInput(amount="12", currency="EUR", provenance="assumption")
    assert "freight:fx_missing" in calculate(request, {})["missing"]


def test_currency_unit_fx_validity():
    request = full_costs()
    request.components["ex_factory"] = MoneyInput(
        amount="120", currency="EUR", unit="dozen", provenance="quote", source_id="quote"
    )
    request.fx_rates = [
        FXRate(currency="EUR", usd_per_unit="1.25", effective_at="2026-01-01T00:00:00Z", source_id="fx")
    ]
    result = calculate(request, {"quote": "hash", "fx": "hash"}, datetime(2026, 10, 30, tzinfo=timezone.utc))
    assert result["components"]["ex_factory"] == "12.5000"
    assert result["unit_contribution"] == "78.5000"
    assert calculate(request, {"fx": "hash"})["unit_contribution"] is None
    request.components["freight"] = MoneyInput(amount="12", unit="carton", provenance="assumption")
    with pytest.raises(DomainError, match="Carton"):
        calculate(request, {"quote": "hash", "fx": "hash"})


@pytest.mark.parametrize("amount", ["NaN", "Infinity", "-1", "1e99"])
def test_invalid_money_rejected(amount):
    with pytest.raises(ValidationError):
        MoneyInput(amount=amount)


@pytest.fixture
def feasibility(setup, case, concepts):
    svc, actor, _, _ = setup
    decide(svc, actor, case["id"], "G2", concepts[0]["id"], "select")
    run = enqueue_run(svc, actor, case["id"], "feasibility", "feasibility-run")
    result = execute_task(svc, actor, run["id"])
    assert result["result"]["waiting_for"] == "G3"
    return svc.list_scoped(actor, case["id"], Artifact, kind="Feasibility")[-1]


def test_internal_pack_graph_stops_g4_and_never_publishable(setup, case, concepts, feasibility):
    svc, actor, _, client = setup
    assert feasibility["data"]["economics"]["unit_contribution"] is None
    decide(svc, actor, case["id"], "G3", feasibility["id"], "sample_validation")
    task = enqueue_run(svc, actor, case["id"], "launch_draft", "draft")
    result = execute_task(svc, actor, task["id"])
    assert result["result"]["waiting_for"] == "G4"
    pack_id = result["result"]["pack_id"]
    service = LaunchPackService(svc)
    pack = service.read(actor, pack_id)
    assert pack["current"] is True
    assert pack["data"]["publishable"] is False
    assert any("G4" in b for b in pack["data"]["blockers"])
    assert pack["data"]["manifest"]["assets"] == []
    blob = service.export(actor, pack_id, "zip")
    assert blob == service.export(actor, pack_id, "zip")
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        assert json.loads(z.read("manifest.json"))["publishable"] is False
    assert client.post("/api/v1/publish").status_code == 404
    with pytest.raises(DomainError):
        subject = ProductService(svc).gate_subject(actor, case["id"], "G5", pack_id)
        ProductService(svc).decide(
            actor,
            case["id"],
            "G5",
            GateRequest(
                decision="internal_handoff",
                subject_type="launch_pack",
                subject_id=pack_id,
                expected_subject_hash=subject["subject_hash"],
                reason="Cannot pass without real sample",
            ),
            "g5",
        )


def test_synthetic_sample_rejected(setup, case, concepts, feasibility):
    svc, actor, _, _ = setup
    decide(svc, actor, case["id"], "G3", feasibility["id"], "sample_validation")
    spec = svc.list_scoped(actor, case["id"], Artifact, kind="ProductSpec")[0]
    request = SampleAttestation(
        expected_spec_hash=spec["sha256"],
        facts=[FactAttestation(name="load", value="10 kg", source_id="fake", exact_excerpt="invented test")],
        tested_at="2026-10-01T00:00:00Z",
        responsible_person="Fixture Actor",
        limitations="No actual sample exists",
    )
    with pytest.raises(DomainError, match="Real Case"):
        FeasibilityService(svc).sample(actor, case["id"], request, "fake-sample")


def test_quote_change_stales_g3_and_pack(setup, case, concepts, feasibility):
    svc, actor, _, _ = setup
    decide(svc, actor, case["id"], "G3", feasibility["id"], "sample_validation")
    pack = LaunchPackService(svc).build(actor, case["id"], "pack")
    req = SourceImport(
        filename="expired.json",
        source_type="quote",
        rights_status="synthetic_fixture",
        is_synthetic=True,
        content=json.dumps(
            {
                "unit_ex_factory_cost": "10",
                "currency": "USD",
                "unit": "piece",
                "expires_at": "2020-01-01T00:00:00Z",
                "is_synthetic": True,
            }
        ),
    )
    svc.import_source(actor, case["id"], req, "quote")
    assert (
        next(x for x in ProductService(svc).decisions(actor, case["id"]) if x["gate"] == "G3")["status"]
        == "stale"
    )
    with pytest.raises(DomainError, match="rebuild"):
        LaunchPackService(svc).export(actor, pack["id"])
    new = FeasibilityService(svc).evaluate(actor, case["id"], None, "recalculate")
    assert new["data"]["economics"]["unit_contribution"] is None
    assert new["data"]["invalid_source_ids"]


def test_source_id_cannot_launder_invented_quote(setup, case, concepts):
    svc, actor, _, _ = setup
    decide(svc, actor, case["id"], "G2", concepts[0]["id"], "select")
    source = svc.import_source(
        actor,
        case["id"],
        SourceImport(
            filename="quote.json",
            source_type="quote",
            rights_status="synthetic_fixture",
            is_synthetic=True,
            content=json.dumps({"unit_ex_factory_cost": "12", "currency": "USD", "unit": "piece"}),
        ),
        "quote-values",
    )
    cost = full_costs()
    cost.components["ex_factory"] = MoneyInput(amount="1", provenance="quote", source_id=source["source_id"])
    with pytest.raises(DomainError, match="match an immutable"):
        FeasibilityService(svc).evaluate(actor, case["id"], cost, "invented-quote")
    cost.components["ex_factory"].amount = "12"
    assert (
        FeasibilityService(svc).evaluate(actor, case["id"], cost, "matching-quote")["data"]["economics"][
            "components"
        ]["ex_factory"]
        == "12.0000"
    )
