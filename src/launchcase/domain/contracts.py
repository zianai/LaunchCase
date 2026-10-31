from typing import Literal

from pydantic import Field

from launchcase.domain.common import Contract


class Constraints(Contract):
    budget_usd: float | None = Field(default=None, ge=0)
    target_retail_price_usd: float | None = Field(default=None, ge=0)
    target_landed_cost_usd: float | None = Field(default=None, ge=0)
    must_preserve: list[str] = Field(default_factory=list, max_length=30)
    must_not_claim: list[str] = Field(default_factory=list, max_length=30)


class DataPolicy(Contract):
    data_origin: str = Field(max_length=200)
    rights_status: Literal["synthetic_fixture", "authorized", "unknown"]
    allowed_external_use: Literal[False] = False
    is_synthetic: bool


class ProductBrief(Contract):
    schema_version: Literal["1.0.0"] = "1.0.0"
    title: str = Field(min_length=3, max_length=200)
    mode: Literal["differentiation"] = "differentiation"
    target_market: Literal["US"] = "US"
    marketplace: Literal["amazon_us"] = "amazon_us"
    category: str = Field(min_length=2, max_length=200)
    target_segment: str = Field(min_length=3, max_length=1000)
    problem_statement: str = Field(min_length=10, max_length=5000)
    goals: list[str] = Field(min_length=1, max_length=30)
    constraints: Constraints = Field(default_factory=Constraints)
    data_policy: DataPolicy


class SourceImport(Contract):
    filename: str = Field(min_length=1, max_length=180, pattern=r"^[^/\\\x00]+\.(csv|json|txt|md)$")
    content: str = Field(min_length=1, max_length=1048576)
    source_type: Literal["review", "competitor", "spec", "quote", "sample", "rule"]
    rights_status: Literal["synthetic_fixture", "authorized", "unknown", "revoked"]
    is_synthetic: bool
    source_url: str | None = Field(default=None, max_length=2000)
    collected_at: str | None = Field(default=None, max_length=60)


class BriefRevision(Contract):
    expected_revision: int = Field(ge=1)
    brief: ProductBrief


class RightsChange(Contract):
    expected_revision: int = Field(ge=1)
    rights_status: Literal["authorized", "unknown", "revoked"]
    reason: str = Field(min_length=5, max_length=1000)
