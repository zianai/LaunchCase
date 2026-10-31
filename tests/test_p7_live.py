# ruff: noqa: F811
# pytest injects the imported fixture by name.
import pytest
from test_p7_policy import policy  # noqa: F401

from launchcase.agents.live import LiveBudget, RealAgentRunner
from launchcase.agents.runtime import DeterministicModel, analyze
from launchcase.validation import PolicyDenied, digest


def prepared(policy):
    p, r, g, install = policy
    evidence = [
        {"id": "ev-1", "quote": "Assembly is hard", "is_synthetic": True, "data": {"source_type": "review"}}
    ]
    rate = 0.000001
    context = {
        **r,
        "input_hash": digest(evidence),
        "provider_config_hash": digest({"model": "stub-model", "rate": rate}),
        "provider": "openai",
        "domain": "api.openai.com",
    }
    import json

    (p.root / "context.json").write_text(json.dumps(context))
    grant = {
        **g,
        "input_hash": context["input_hash"],
        "provider_config_hash": context["provider_config_hash"],
        "capabilities": {
            "submit_model": dict(
                provider="openai",
                model="stub-model",
                domain="api.openai.com",
                max_requests=3,
                max_images=0,
                max_attempts=1,
                max_usd=".3",
            )
        },
    }
    p = install(grant)
    return p, context, evidence, rate


def test_real_runner_uses_sdk_with_frozen_read_only_tools(policy):
    p, r, evidence, rate = prepared(policy)
    runner = RealAgentRunner(
        r["tenant_id"],
        r["case_id"],
        policy=p,
        model=DeterministicModel(analyze(evidence).model_dump()),
        model_name="stub-model",
        rate=rate,
    )
    result = runner.run(evidence, LiveBudget(max_tokens=50000, max_cost_usd=0.3))
    assert result["model_calls"] == 2 and result["tool_calls"] == 1
    assert result["paid_calls"] == 0 and result["status"] == "tested_offline"
    assert result["output"]["category_prevalence"] is None
    assert result["cost_actual_usd"] is None
    assert len(result["request_receipts"]) == 2
    assert all(
        item["total_tokens"] >= 0 and item["cost_actual_usd"] is None for item in result["request_receipts"]
    )


def test_real_runner_cannot_call_on_missing_or_changed_authority(policy):
    p, r, evidence, rate = prepared(policy)
    model = DeterministicModel(analyze(evidence).model_dump())
    runner = RealAgentRunner(
        "other-tenant", r["case_id"], policy=p, model=model, model_name="stub-model", rate=rate
    )
    with pytest.raises(PolicyDenied):
        runner.run(evidence, LiveBudget(max_cost_usd=0.3))
    assert model.calls == 0


def test_real_runner_rejects_invented_citation(policy):
    p, r, evidence, rate = prepared(policy)
    output = analyze(evidence).model_dump()
    output["themes"][0]["supporting_evidence_refs"] = ["invented"]
    runner = RealAgentRunner(
        r["tenant_id"],
        r["case_id"],
        policy=p,
        model=DeterministicModel(output),
        model_name="stub-model",
        rate=rate,
    )
    with pytest.raises(Exception, match="Out-of-scope"):
        runner.run(evidence, LiveBudget(max_tokens=50000, max_cost_usd=0.3))


def test_real_runner_unknown_receipt_never_retries(policy):
    p, r, evidence, rate = prepared(policy)

    class Ambiguous(DeterministicModel):
        async def get_response(self, *args, **kwargs):
            self.calls += 1
            raise TimeoutError("accepted then connection lost")

    model = Ambiguous({})
    runner = RealAgentRunner(
        r["tenant_id"], r["case_id"], policy=p, model=model, model_name="stub-model", rate=rate
    )
    with pytest.raises(TimeoutError):
        runner.run(evidence, LiveBudget(max_tokens=50000, max_cost_usd=0.3))
    with pytest.raises(PolicyDenied, match="UNRESOLVED_RECEIPT"):
        runner.run(evidence, LiveBudget(max_tokens=50000, max_cost_usd=0.3))
    assert model.calls == 1


def test_live_receipt_preserves_raw_cache_usage(policy):
    p, r, evidence, rate = prepared(policy)

    class UsageModel(DeterministicModel):
        async def get_response(self, *args, **kwargs):
            assert kwargs["model_settings"].preserve_raw_usage is True
            response = await super().get_response(*args, **kwargs)
            response.raw_usage = {
                "input_tokens_details": {"cached_tokens": 11, "cache_write_tokens": 17},
                "vendor_future_field": 23,
            }
            return response

    result = RealAgentRunner(
        r["tenant_id"],
        r["case_id"],
        policy=p,
        model=UsageModel(analyze(evidence).model_dump()),
        model_name="stub-model",
        rate=rate,
    ).run(evidence, LiveBudget(max_tokens=50000, max_cost_usd=0.3))
    assert all(
        receipt["raw_usage"]["input_tokens_details"]["cache_write_tokens"] == 17
        for receipt in result["request_receipts"]
    )
    assert result["request_receipts"][0]["raw_usage"]["vendor_future_field"] == 23
    assert result["cost_actual_usd"] is None


def test_denied_later_run_does_not_report_previous_receipts(policy):
    p, r, evidence, rate = prepared(policy)
    model = DeterministicModel(analyze(evidence).model_dump())
    runner = RealAgentRunner(
        r["tenant_id"],
        r["case_id"],
        policy=p,
        model=model,
        model_name="stub-model",
        rate=rate,
        budget=LiveBudget(max_tokens=50000, max_cost_usd=0.3),
    )
    runner.run(evidence)
    assert len(runner.last_receipts) == 2
    (p.root / "revoked").touch()
    with pytest.raises(PolicyDenied, match="AUTH_REVOKED"):
        runner.run(evidence)
    assert runner.last_receipts == [] and model.calls == 2
