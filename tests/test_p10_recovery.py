# ruff: noqa: F811
"""Real process contention and recovery on disposable single-host SQLite."""

import json
import os
import subprocess
import sys

import pytest

from launchcase.domain.common import DomainError, uid
from launchcase.infrastructure.models import Artifact
from launchcase.infrastructure.tasks import TaskManager
from launchcase.workflow.graph import enqueue_run


@pytest.mark.parametrize("crash_point", ["before_execution", "after_checkpoint"])
def test_two_worker_processes_recover_one_expired_task(setup, case, imported, crash_point):
    svc, actor, _, _ = setup
    task = enqueue_run(svc, actor, case["id"], "research", uid())
    manager = TaskManager(svc)
    code = """
import json, sys
from pathlib import Path
from launchcase.application.services import Actor, CaseService
from launchcase.infrastructure.config import Settings
from launchcase.workflow.graph import execute_task
x=json.loads(sys.argv[1])
svc=CaseService(Settings(Path(x['root']),x['database']))
actor=Actor(x['actor'],x['tenant'],'owner',True)
execute_task(svc,actor,x['task'])
"""
    payload = json.dumps(
        {
            "root": str(svc.settings.data_dir),
            "database": svc.settings.database_url,
            "actor": actor.id,
            "tenant": actor.tenant_id,
            "task": task["id"],
        }
    )
    env = {k: os.environ[k] for k in ("PATH", "HOME", "TMPDIR") if k in os.environ}
    env["OPENAI_AGENTS_DISABLE_TRACING"] = "1"
    if crash_point == "before_execution":
        assert manager.claim(actor, task["id"], "crashed-before-execution", lease_seconds=-1)
    else:
        crash_code = code.replace(
            "execute_task(svc,actor,x['task'])",
            """
import os
from launchcase.infrastructure.tasks import TaskManager
TaskManager.finish = lambda *args, **kwargs: os._exit(71)
execute_task(svc,actor,x['task'])
""",
        )
        crashed = subprocess.run(
            [sys.executable, "-c", crash_code, payload], env=env, capture_output=True, timeout=30
        )
        assert crashed.returncode == 71, crashed.stderr.decode()
        assert (svc.settings.data_dir / "checkpoints.db").stat().st_size > 0
        assert len(svc.list_scoped(actor, case["id"], Artifact, kind="Research")) == 1
        from launchcase.infrastructure.models import Task

        with svc.write() as session:
            row = svc.get_row(session, Task, actor, task["id"])
            assert row.status == "running"
            row.lease_until = -1
    processes = [
        subprocess.Popen(
            [sys.executable, "-c", code, payload], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        for _ in range(2)
    ]
    for p in processes:
        out, err = p.communicate(timeout=30)
        assert p.returncode == 0, err.decode()
    result = manager.get(actor, task["id"])
    assert result["status"] == "succeeded" and result["attempts"] == 2
    assert len(svc.list_scoped(actor, case["id"], Artifact, kind="Research")) == 1
    assert result["result"]["waiting_for"] == "G1"


def test_private_pilot_export_without_current_grant_blocked(real_mode):
    _, _, case, _, client = real_mode
    response = client.get(f"/api/v1/product-cases/{case['id']}/pilot-export")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "BLOCKED_EXTERNAL"


def test_token_rotation_revocation_and_tenant_operations(setup, case):
    svc, actor, other, client = setup
    old, identity = svc.provision(actor.tenant_id, "TEST ONLY token rotation", "viewer", True)
    new = svc.rotate_token(actor, identity.id)
    with pytest.raises(DomainError):
        svc.authenticate(old)
    assert svc.authenticate(new).id == identity.id
    with pytest.raises(DomainError):
        svc.rotate_token(other, identity.id)
    svc.rotate_token(actor, identity.id, True)
    with pytest.raises(DomainError):
        svc.authenticate(new)
    task = enqueue_run(svc, actor, case["id"], "research", uid())
    assert TaskManager(svc).claim(actor, task["id"], "expired-test", lease_seconds=-1)
    response = client.get("/api/v1/operations/status")
    assert response.status_code == 200
    assert response.json()["alerts"] == ["expired_leases"]
    from launchcase.infrastructure.operations import status

    assert not status(svc, other)["alerts"]


from test_handoff import real_mode  # noqa: E402,F401
