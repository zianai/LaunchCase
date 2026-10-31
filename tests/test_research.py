import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest

from launchcase.agents.runtime import AgentBudget, FakeSDKRunner
from launchcase.application.services import CaseService
from launchcase.domain.common import DomainError
from launchcase.domain.contracts import SourceImport
from launchcase.infrastructure.models import Artifact, Evidence
from launchcase.infrastructure.tasks import TaskManager
from launchcase.workflow.graph import enqueue_run, execute_task


def test_real_sdk_fake_model_citations_injection_and_conflicts(setup, case, imported):
    svc, actor, _, _ = setup
    task = enqueue_run(svc, actor, case["id"], "research", "research")
    result = execute_task(svc, actor, task["id"])
    assert result["status"] == "succeeded" and result["result"]["waiting_for"] == "G1"
    rows = svc.list_scoped(actor, case["id"], Artifact, kind="Research")
    run = rows[0]["data"]
    assert run["model_calls"] == 2 and run["tool_calls"] == 1 and run["paid_calls"] == 0
    assert run["output"]["category_prevalence"] is None
    assert run["sufficiency"]["status"] == "conflicted"
    assembly = next(t for t in run["output"]["themes"] if t["name"] == "assembly")
    assert assembly["supporting_evidence_refs"] and assembly["contradicting_evidence_refs"]
    evidence = svc.list_scoped(actor, case["id"], Evidence)
    injection = next(e["id"] for e in evidence if "IGNORE SYSTEM" in e["quote"])
    assert all(injection not in t["supporting_evidence_refs"] for t in run["output"]["themes"])
    assert svc.get_case(actor, case["id"])["stage"] == "opportunity_review"


def test_small_sample_requests_input(setup, case):
    svc, actor, _, _ = setup
    req = SourceImport(
        filename="small.csv",
        content="review_text,product_id,review_date\nAssembly was hard,A,2026-10-01\nAssembly was easy,B,2026-10-02\nAssembly was slow,A,2026-10-03",
        source_type="review",
        rights_status="synthetic_fixture",
        is_synthetic=True,
    )
    svc.import_source(actor, case["id"], req, "small")
    task = enqueue_run(svc, actor, case["id"], "research", "run")
    result = execute_task(svc, actor, task["id"])
    assert result["result"]["waiting_for"] == "needs_input"
    assert svc.get_case(actor, case["id"])["status"] == "needs_input"


def test_sdk_budget_blocks(setup, case, imported):
    svc, actor, _, _ = setup
    evidence = svc.list_scoped(actor, case["id"], Evidence)
    with pytest.raises(DomainError, match="token budget"):
        FakeSDKRunner().run(evidence, AgentBudget(max_tokens=1))
    with pytest.raises(Exception, match="budget exhausted"):
        FakeSDKRunner().run(evidence, AgentBudget(max_tool_calls=0))


def test_lease_contention_fencing_and_recovery(setup, case, imported):
    svc, actor, _, _ = setup
    task = enqueue_run(svc, actor, case["id"], "research", "run")
    manager = TaskManager(svc)
    with ThreadPoolExecutor(max_workers=2) as pool:
        claims = list(pool.map(lambda owner: manager.claim(actor, task["id"], owner), ["a", "b"]))
    assert sum(c is not None for c in claims) == 1
    old = next(c for c in claims if c)
    with sqlite3.connect(svc.settings.data_dir / "test.db") as conn:
        conn.execute("UPDATE tasks SET lease_until=0 WHERE id=?", (task["id"],))
    new = manager.claim(actor, task["id"], "replacement")
    assert new["fence"] == old["fence"] + 1
    with pytest.raises(DomainError, match="lease"):
        manager.finish(actor, task["id"], old["fence"], {})


def test_checkpoint_restart_duplicate_delivery(setup, case, imported):
    svc, actor, _, _ = setup
    task = enqueue_run(svc, actor, case["id"], "research", "run")
    first = execute_task(svc, actor, task["id"])
    reopened = CaseService(svc.settings)
    assert execute_task(reopened, actor, task["id"]) == first
    assert enqueue_run(reopened, actor, case["id"], "research", "duplicate-wakeup")["id"] == task["id"]
    assert len(reopened.list_scoped(actor, case["id"], Artifact, kind="Research")) == 1
    with sqlite3.connect(svc.settings.data_dir / "checkpoints.db") as conn:
        assert conn.execute("SELECT count(*) FROM checkpoints").fetchone()[0] > 0
