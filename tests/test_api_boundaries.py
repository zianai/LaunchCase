import pytest
from pydantic import ValidationError

from launchcase.domain.contracts import MoneyInput, SourceImport
from launchcase.infrastructure.models import AuditEvent


def test_request_limit_including_stream_without_length(setup, case):
    _, _, _, client = setup
    path = f"/api/v1/product-cases/{case['id']}/sources/import"
    response = client.post(path, content=iter([b"x" * 1048576] * 3))
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "REQUEST_TOO_LARGE"


def test_version_and_large_money_rejected():
    with pytest.raises(ValidationError):
        MoneyInput(schema_version="2.0.0")
    with pytest.raises(ValidationError):
        MoneyInput(amount="9" * 10000)
    with pytest.raises(ValidationError):
        SourceImport(
            schema_version="2.0.0",
            filename="x.txt",
            content="test",
            source_type="review",
            rights_status="synthetic_fixture",
            is_synthetic=True,
        )


def test_sse_reconnect_past_first_page_keeps_sequence_and_scope(setup, case):
    svc, actor, other, client = setup
    with svc.write() as session:
        session.add_all(
            AuditEvent(
                tenant_id=actor.tenant_id,
                case_id=case["id"],
                actor_id=actor.id,
                action="test.event",
                sequence=seq,
                data={},
            )
            for seq in range(2, 6003)
        )
    response = client.get(f"/api/v1/product-cases/{case['id']}/events", headers={"Last-Event-ID": "6000"})
    assert response.status_code == 200
    assert "id: 6001\n" in response.text and "id: 6002\n" in response.text
    assert "id: 6000\n" not in response.text
    from launchcase.domain.common import DomainError

    with pytest.raises(DomainError):
        svc.replay_events(other, case["id"], 6000)
