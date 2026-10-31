import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from launchcase.api import app
from launchcase.domain.common import Contract


def test_health_offline():
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json()["paid_enabled"] is False


def test_strict_contract():
    with pytest.raises(ValidationError):
        Contract.model_validate({"schema_version": 1})
    with pytest.raises(ValidationError):
        Contract.model_validate({"reviewer": "agent"})
