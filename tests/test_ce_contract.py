"""Pinned LaunchCase consumer fixture; no dependency on any other checkout."""

import copy
import hashlib
import json
from pathlib import Path

import pytest

from launchcase.domain.common import DomainError
from launchcase.integrations.creative import validate_asset, validate_batch

ROOT = Path(__file__).resolve().parents[1] / "contracts/launchcase/1.0.0"
FIXTURE = json.loads((ROOT / "fixtures.json").read_text())


def test_frozen_fixture_sha():
    expected = (ROOT / "SHA256SUMS").read_text().split()[0]
    assert hashlib.sha256((ROOT / "fixtures.json").read_bytes()).hexdigest() == expected


def test_additive_fields_compatible_and_vision_skipped_is_not_pass():
    batch = {**FIXTURE["batch"], "optional_extension": "accepted"}
    assert validate_batch(batch, FIXTURE["plan"]) == batch
    asset = {**FIXTURE["asset"], "optional_extension": {"future": True}}
    assert validate_asset(asset, batch)["qa"]["vision"]["status"] == "skipped"
    assert asset["review_status"] == "pending"


@pytest.mark.parametrize("cost", [None, "0", True, -1, 1, float("nan"), float("inf")])
def test_unknown_or_changed_cost_refused(cost):
    with pytest.raises(DomainError):
        validate_batch({**FIXTURE["batch"], "cost_usd": cost}, FIXTURE["plan"])


def test_financial_unit_change_and_missing_required_field_refused():
    data = copy.deepcopy(FIXTURE["batch"])
    data["cost_cents"] = data.pop("cost_usd")
    with pytest.raises(DomainError):
        validate_batch(data, FIXTURE["plan"])
    for field in ["qa", "sha256", "batch_id", "project_id"]:
        data = copy.deepcopy(FIXTURE["asset"])
        data.pop(field)
        with pytest.raises(DomainError):
            validate_asset(data, FIXTURE["batch"])


@pytest.mark.parametrize("qa", [{}, {"status": "unknown"}, {"status": "pass"}, {"status": None}])
def test_missing_or_unknown_qa_refused(qa):
    with pytest.raises(DomainError):
        validate_asset({**FIXTURE["asset"], "qa": qa}, FIXTURE["batch"])


def test_foreign_receipts_refused():
    with pytest.raises(DomainError):
        validate_batch({**FIXTURE["batch"], "project_id": "foreign"}, FIXTURE["plan"])
    with pytest.raises(DomainError):
        validate_asset({**FIXTURE["asset"], "batch_id": "foreign"}, FIXTURE["batch"])
