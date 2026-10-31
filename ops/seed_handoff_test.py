"""Seed only disposable real-mode contract tests. Never business evidence."""

import json
import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "tests"))
from conftest import brief, setup  # noqa: E402
from test_handoff import real_mode  # noqa: E402

folder = Path(os.environ.get("LAUNCHCASE_HANDOFF_DIR") or root / ".launchcase" / "handoff-e2e")
folder.mkdir(parents=True, exist_ok=True)
# Each run uses a new disposable DB; existing test data is never overwritten.
from launchcase.domain.common import uid  # noqa: E402

run_dir = folder / uid()
run_dir.mkdir()
svc, actor, case, sample, client = real_mode.__wrapped__(setup.__wrapped__(run_dir), brief.__wrapped__())
token, _ = svc.provision(actor.tenant_id, "TEST ONLY browser reviewer", "owner", False)
(folder / "token").write_text(token)
(folder / "token").chmod(0o600)
(folder / "manifest.json").write_text(
    json.dumps(
        {
            "database": str(run_dir / "test.db"),
            "data_dir": str(run_dir),
            "case_id": case["id"],
            "sample": sample.model_dump(),
        },
        indent=2,
    )
)
print("Disposable G4/G5 contract fixture created; no real business validation.")
