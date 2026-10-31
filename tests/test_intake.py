from pathlib import Path

import pytest
from pydantic import ValidationError

from launchcase.domain.common import DomainError
from launchcase.domain.contracts import BriefRevision, RightsChange, SourceImport
from launchcase.infrastructure.models import AuditEvent, Evidence, SourceDocument
from launchcase.infrastructure.store import read_import_file


def test_idempotency_and_payload_conflict(setup, brief, case):
    svc, actor, _, _ = setup
    assert svc.create_case(actor, brief, "case-create")["id"] == case["id"]
    with pytest.raises(DomainError, match="different request"):
        svc.create_case(actor, brief.model_copy(update={"title": "Another title"}), "case-create")


def test_exact_row_provenance_duplicate_and_conflict_preserved(setup, case, imported):
    svc, actor, _, _ = setup
    request, result = imported
    assert result["rows_imported"] == 24 and result["rows_skipped"] == 0
    rows = svc.list_scoped(actor, case["id"], Evidence)
    assert any(
        x["source_locator"] == "synthetic-voc.csv#row=2"
        and x["quote"] == "The screws were hard to align during assembly."
        for x in rows
    )
    assert any("simple" in x["quote"] for x in rows)
    assert svc.import_source(actor, case["id"], request, "again")["rows_imported"] == 0
    assert len(svc.list_scoped(actor, case["id"], Evidence)) == 24
    assert svc.read_source(actor, result["source_id"], True) == request.content.encode()


def test_tenant_checks_service_api_source_events(setup, case, imported):
    svc, actor, other, client = setup
    _, result = imported
    for fn in [
        lambda: svc.get_case(other, case["id"]),
        lambda: svc.read_source(other, result["source_id"]),
        lambda: svc.list_scoped(other, case["id"], AuditEvent),
    ]:
        with pytest.raises(DomainError) as e:
            fn()
        assert e.value.status == 404
    token, _ = svc.provision("tenant-b", "B", "owner")
    for path in [
        f"product-cases/{case['id']}",
        f"sources/{result['source_id']}/content",
        f"product-cases/{case['id']}/activity",
    ]:
        assert client.get("/api/v1/" + path, headers={"Authorization": f"Bearer {token}"}).status_code == 404


@pytest.mark.parametrize("content", ["\x00bad", '<svg onload="evil"/>', "{broken", "[]", "[1]"])
def test_malformed_no_partial_import(setup, case, content):
    svc, actor, _, _ = setup
    req = SourceImport(
        filename="bad.json",
        content=content,
        source_type="review",
        rights_status="unknown",
        is_synthetic=False,
    )
    with pytest.raises(DomainError):
        svc.import_source(actor, case["id"], req, "bad")
    assert svc.list_scoped(actor, case["id"], SourceDocument) == []


def test_size_unicode_and_traversal(setup, case, tmp_path):
    svc, actor, _, _ = setup
    for filename in ["../secret.txt", "/etc/passwd.txt", "x.svg"]:
        with pytest.raises(ValidationError):
            SourceImport(
                filename=filename,
                content="x",
                source_type="spec",
                rights_status="unknown",
                is_synthetic=False,
            )
    req = SourceImport(
        filename="large.txt",
        content="猫" * 400000,
        source_type="spec",
        rights_status="unknown",
        is_synthetic=False,
    )
    with pytest.raises(DomainError):
        svc.import_source(actor, case["id"], req, "large")
    (tmp_path / "real.txt").write_text("sample")
    (tmp_path / "alias.txt").symlink_to(tmp_path / "real.txt")
    with pytest.raises(DomainError):
        read_import_file(tmp_path / "alias.txt")
    with pytest.raises(DomainError):
        read_import_file(Path("../secret.txt"))


def test_hash_tamper_blocks_read(setup, imported):
    svc, actor, _, _ = setup
    _, result = imported
    svc.objects.path(result["sha256"]).write_bytes(b"tampered")
    with pytest.raises(DomainError, match="hash changed"):
        svc.read_source(actor, result["source_id"], True)


def test_brief_revision_cas_and_rights_history(setup, case, brief, imported):
    svc, actor, _, _ = setup
    request = BriefRevision(expected_revision=2, brief=brief)
    updated = svc.revise_brief(actor, case["id"], request, "revise")
    assert updated["brief_version"] == 2
    with pytest.raises(DomainError):
        svc.revise_brief(actor, case["id"], request, "stale")
    change = RightsChange(expected_revision=3, rights_status="revoked", reason="Fixture rights withdrawn")
    assert svc.change_rights(actor, imported[1]["source_id"], change, "rights")["rights_status"] == "revoked"
    assert any(e["action"] == "source.rights_changed" for e in svc.list_scoped(actor, case["id"], AuditEvent))


def test_synthetic_cannot_be_relabelled(setup, case, imported):
    svc, actor, _, _ = setup
    req = RightsChange(expected_revision=2, rights_status="authorized", reason="Try to relabel")
    with pytest.raises(DomainError, match="cannot be relabeled"):
        svc.change_rights(actor, imported[1]["source_id"], req, "relabel")


def test_api_auth_strict_role(setup, brief):
    svc, _, _, client = setup
    assert client.get("/api/v1/product-cases", headers={"Authorization": ""}).status_code == 401
    res = client.post(
        "/api/v1/product-cases",
        json={**brief.model_dump(), "reviewer": "agent"},
        headers={"Idempotency-Key": "unknown"},
    )
    assert res.status_code == 422
    token, _ = svc.provision("tenant-a", "reader", "viewer")
    assert (
        client.post(
            "/api/v1/product-cases",
            json=brief.model_dump(),
            headers={"Idempotency-Key": "viewer", "Authorization": f"Bearer {token}"},
        ).status_code
        == 403
    )
