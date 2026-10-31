import json
from pathlib import Path

import pytest

from launchcase.application.demo import demo, validate
from launchcase.application.services import Actor, CaseService
from launchcase.domain.common import DomainError
from launchcase.infrastructure.config import Settings
from launchcase.infrastructure.operations import backup, restore, retention
from launchcase.infrastructure.tasks import TaskManager
from launchcase.workflow.graph import enqueue_run, execute_task
from launchcase.workflow.worker import recover_once

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures/scenarios/pet-furniture-us"


def test_full_demo_strict_validator_and_false_label(tmp_path):
    output = tmp_path / "demo"
    manifest = demo(FIXTURE, output)
    assert manifest["counts"]["concepts"] == 2 and manifest["counts"]["evidence"] == 28
    assert validate(output)["valid"]
    manifest["scope"] = "tested_live"
    (output / "demo-manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(DomainError, match="relabeled"):
        validate(output)


def test_strict_validator_rejects_tampered_original_quote(tmp_path):
    import sqlite3

    output = tmp_path / "demo"
    demo(FIXTURE, output)
    with sqlite3.connect(output / "launchcase.db") as conn:
        conn.execute(
            "UPDATE evidence SET quote='invented statement' WHERE id=(SELECT id FROM evidence LIMIT 1)"
        )
    with pytest.raises(DomainError, match="exact original row"):
        validate(output)


def test_backup_restore_same_hashes_and_decisions(tmp_path):
    output = tmp_path / "demo"
    manifest = demo(FIXTURE, output)
    settings = Settings(output, f"sqlite:///{output}/launchcase.db")
    backup_dir = tmp_path / "backup"
    backup(settings, backup_dir)
    restored = tmp_path / "restored"
    restore(backup_dir, restored)
    # Restore app state; exported deliverables are separately immutable and can be regenerated.
    svc = CaseService(Settings(restored, f"sqlite:///{restored}/launchcase.db"))
    actor = Actor(manifest["actor_id"], manifest["tenant_id"], "owner", True)
    from launchcase.application.launchpacks import LaunchPackService

    assert LaunchPackService(svc).read(actor, manifest["pack_id"])["current"]
    assert (
        LaunchPackService(svc).export(actor, manifest["pack_id"])
        == (output / "internal-draft.json").read_bytes()
    )
    original = next((backup_dir / "objects").iterdir())
    original.write_bytes(b"corrupt")
    with pytest.raises(DomainError, match="invalid"):
        restore(backup_dir, tmp_path / "unsafe")
    assert not (tmp_path / "unsafe").exists()


def test_recovery_after_task_expiration_and_tenant_retention(setup, case, imported):
    svc, actor, other, _ = setup
    task = enqueue_run(svc, actor, case["id"], "research", "recovery")
    manager = TaskManager(svc)
    claim = manager.claim(actor, task["id"], "killed-worker", lease_seconds=-1)
    assert claim
    result = recover_once(svc)
    assert result[0]["status"] == "succeeded"
    assert execute_task(svc, actor, task["id"])["attempts"] == 2
    assert retention(svc, actor)["dry_run"]
    other_before = svc.list_cases(other)
    assert retention(svc, actor, actor.tenant_id)["dry_run"] is False
    assert svc.list_cases(actor) == [] and svc.list_cases(other) == other_before
    import sqlite3

    with sqlite3.connect(svc.settings.data_dir / "checkpoints.db") as conn:
        assert conn.execute("SELECT count(*) FROM checkpoints").fetchone()[0] == 0


def test_last_attempt_expiry_becomes_terminal(setup, case, imported):
    svc, actor, _, _ = setup
    task = enqueue_run(svc, actor, case["id"], "research", "exhaustion")
    manager = TaskManager(svc)
    for index in range(3):
        assert manager.claim(actor, task["id"], f"dead-worker-{index}", lease_seconds=-1)
    result = recover_once(svc)[0]
    assert result["status"] == "failed" and result["error_code"] == "ATTEMPTS_EXHAUSTED"
    assert recover_once(svc) == []
