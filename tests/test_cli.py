import json
import sys

import pytest
from conftest import decide

from launchcase.application.visuals import VisualService
from launchcase.cli import main


def test_cli_visual_uses_service_gate_and_persistent_receipts(
    setup, case, concepts, monkeypatch, capsys, tmp_path
):
    svc, actor, _, _ = setup
    decide(svc, actor, case["id"], "G2", concepts[0]["id"], "select")
    token, cli_actor = svc.provision(actor.tenant_id, "CLI synthetic operator", "owner", True)
    monkeypatch.setenv("LAUNCHCASE_TOKEN", token)
    monkeypatch.setenv("LAUNCHCASE_DATA_DIR", str(svc.settings.data_dir))
    monkeypatch.setenv("LAUNCHCASE_DATABASE_URL", svc.settings.database_url)

    def invoke(*args):
        monkeypatch.setattr(sys, "argv", ["launchcase", "--json", *args])
        main()
        return json.loads(capsys.readouterr().out)

    request = tmp_path / "visual.json"
    request.write_text(
        json.dumps({"concept_id": concepts[0]["id"], "requirements": "Synthetic internal plan only"})
    )
    task = invoke("visual", "plan", "--case", case["id"], "--file", str(request))
    with pytest.raises(SystemExit):
        invoke("visual", "submit", task["id"])
    assert "PLAN_REVIEW_REQUIRED" in capsys.readouterr().out
    request.write_text(
        json.dumps(
            {
                "expected_subject_hash": task["plan_hash"],
                "decision": "approved",
                "reason": "Synthetic plan approval only",
            }
        )
    )
    invoke("visual", "approve-plan", task["id"], "--file", str(request))
    first = invoke("visual", "submit", task["id"])
    assert invoke("visual", "submit", task["id"])["remote"] == first["remote"]
    invoke("visual", "sync", task["id"])
    current = invoke("visual", "status", task["id"])
    asset = VisualService(svc).asset(cli_actor, current["assets"][0]["id"])
    request.write_text(
        json.dumps(
            {
                "expected_subject_hash": asset["subject_hash"],
                "decision": "approved",
                "reason": "Synthetic asset review only",
            }
        )
    )
    invoke("visual", "review-asset", asset["id"], "--file", str(request))
    assert invoke("visual", "status", task["id"])["state"] == "approved"


def test_cli_rotation_writes_private_file_and_never_prints_token(setup, monkeypatch, capsys, tmp_path):
    svc, actor, _, _ = setup
    owner_token, _ = svc.provision(actor.tenant_id, "TEST ONLY rotation owner", "owner", True)
    old_token, target = svc.provision(actor.tenant_id, "TEST ONLY target", "viewer", True)
    monkeypatch.setenv("LAUNCHCASE_TOKEN", owner_token)
    monkeypatch.setenv("LAUNCHCASE_DATA_DIR", str(svc.settings.data_dir))
    monkeypatch.setenv("LAUNCHCASE_DATABASE_URL", svc.settings.database_url)
    destination = tmp_path / "private-token"
    monkeypatch.setattr(
        sys, "argv", ["launchcase", "rotate-token", "--identity", target.id, "--out", str(destination)]
    )
    main()
    replacement = destination.read_text()
    printed = capsys.readouterr().out
    assert replacement not in printed and old_token not in printed
    assert destination.stat().st_mode & 0o777 == 0o600
    assert svc.authenticate(replacement).id == target.id
    with pytest.raises(SystemExit):
        main()
    assert svc.authenticate(replacement).id == target.id
