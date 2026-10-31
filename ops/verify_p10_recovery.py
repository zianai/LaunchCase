"""Stopped-writer SQLite recovery drill with immutable object/checkpoint verification."""

import json
import statistics
import tempfile
import time
from pathlib import Path

from launchcase.application.demo import demo
from launchcase.application.launchpacks import LaunchPackService
from launchcase.application.products import ProductService
from launchcase.application.services import Actor, CaseService
from launchcase.domain.common import digest
from launchcase.infrastructure.config import Settings
from launchcase.infrastructure.migrate import migrate
from launchcase.infrastructure.operations import backup, restore

ROOT = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix="launchcase-p10-recovery-") as temporary:
    root = Path(temporary)
    original = root / "original"
    manifest = demo(ROOT / "fixtures/scenarios/pet-furniture-us", original)
    settings = Settings(original, f"sqlite:///{original}/launchcase.db")
    source_service = CaseService(settings)
    actor = Actor(manifest["actor_id"], manifest["tenant_id"], "owner", True)
    original_decisions = ProductService(source_service).decisions(actor, manifest["case_id"])
    original_case = source_service.get_case(actor, manifest["case_id"])
    source_service.engine.dispose()
    snapshot = backup(settings, root / "backup")
    started = time.monotonic()
    restore(root / "backup", root / "restored")
    restored = root / "restored"
    restored_settings = Settings(restored, f"sqlite:///{restored}/launchcase.db")
    migrate(restored_settings)
    svc = CaseService(restored_settings)
    actor = Actor(manifest["actor_id"], manifest["tenant_id"], "owner", True)
    pack = LaunchPackService(svc).export(actor, manifest["pack_id"])
    assert pack == (original / "internal-draft.json").read_bytes()
    assert (restored / "checkpoints.db").exists()
    assert ProductService(svc).decisions(actor, manifest["case_id"]) == original_decisions
    assert svc.get_case(actor, manifest["case_id"]) == original_case
    for name, sha in snapshot["files"].items():
        if name.startswith("objects/"):
            assert digest((restored / name).read_bytes()) == sha
    recovery_seconds = time.monotonic() - started
    latencies = []
    for _ in range(100):
        t = time.monotonic()
        assert svc.get_case(actor, manifest["case_id"])["id"] == manifest["case_id"]
        latencies.append((time.monotonic() - t) * 1000)
    svc.engine.dispose()
    # Rollback uses the original immutable backup, never a production downgrade.
    restore(root / "backup", root / "rollback")
    for name, sha in snapshot["files"].items():
        assert digest((root / "rollback" / name).read_bytes()) == sha
    print(
        json.dumps(
            {
                "scope": "E1 synthetic single-host stopped-writer SQLite, 100 local case reads",
                "restored_files": len(snapshot["files"]),
                "pack_sha256": digest(pack),
                "checkpoint_sha256": snapshot["files"]["checkpoints.db"],
                "restore_migrate_read_seconds": recovery_seconds,
                "read_latency_ms": {
                    "samples": len(latencies),
                    "median": statistics.median(latencies),
                    "p95": sorted(latencies)[94],
                },
                "rollback_hashes_equal": True,
                "approval_subjects_equal": True,
                "business_case_equal": True,
                "production_rto_seconds": None,
                "production_rpo_seconds": None,
                "multi_host": "not_tested",
                "business_pilot_accepted": False,
            },
            indent=2,
        )
    )
