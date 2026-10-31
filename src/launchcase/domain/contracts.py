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


class GateRequest(Contract):
    decision: Literal[
        "accept",
        "research_more",
        "reject",
        "select",
        "revise",
        "sample_validation",
        "hold",
        "verify_sample",
        "rework",
        "internal_handoff",
        "needs_changes",
    ]
    subject_type: Literal["opportunity", "concept", "feasibility", "sample", "launch_pack"]
    subject_id: str = Field(min_length=1, max_length=100)
    expected_subject_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    reason: str = Field(min_length=5, max_length=2000)


class SpecClaim(Contract):
    name: str = Field(min_length=1, max_length=100)
    value: str | None = Field(default=None, max_length=1000)
    unit: str | None = Field(default=None, max_length=50)
    status: Literal["proposed", "unknown"] = "unknown"
    evidence_refs: list[str] = Field(default_factory=list, max_length=50)


class SpecRevision(Contract):
    expected_subject_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    claims: list[SpecClaim] = Field(min_length=1, max_length=50)
    reason: str = Field(min_length=5, max_length=2000)


class VisualRequest(Contract):
    concept_id: str
    intent: Literal["concept_exploration", "listing"] = "concept_exploration"
    requirements: str = Field(min_length=5, max_length=5000)
    variants: int = Field(default=1, ge=1, le=3)
    budget_usd: Literal[0] = 0
    source_asset_ids: list[str] = Field(default_factory=list, max_length=0)


class ReviewRequest(Contract):
    expected_subject_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    decision: Literal["approved", "rejected"]
    reason: str = Field(min_length=5, max_length=2000)


class MoneyInput(Contract):
    amount: str | None = Field(default=None, max_length=24, pattern=r"^\d+(\.\d{1,8})?$")
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    unit: Literal["piece", "dozen", "carton"] = "piece"
    units_per_carton: int | None = Field(default=None, ge=1, le=10000)
    provenance: Literal["quote", "assumption", "missing"] = "missing"
    source_id: str | None = None


class FXRate(Contract):
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    usd_per_unit: str = Field(max_length=24, pattern=r"^\d+(\.\d{1,10})?$")
    effective_at: str
    source_id: str


class CostRequest(Contract):
    components: dict[str, MoneyInput]
    fixed_costs: dict[str, MoneyInput] = Field(default_factory=dict)
    fx_rates: list[FXRate] = Field(default_factory=list, max_length=20)
    assumptions: list[str] = Field(default_factory=list, max_length=50)


class FactAttestation(Contract):
    name: str = Field(min_length=2, max_length=100)
    value: str = Field(min_length=1, max_length=1000)
    source_id: str
    exact_excerpt: str = Field(min_length=5, max_length=3000)
    external_allowed: bool = False


class SampleAttestation(Contract):
    expected_spec_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    facts: list[FactAttestation] = Field(min_length=1, max_length=50)
    tested_at: str
    responsible_person: str = Field(min_length=2, max_length=100)
    limitations: str = Field(min_length=5, max_length=2000)


class RuleAttestation(Contract):
    source_id: str
    authority_url: str = Field(pattern=r"^https://[^\s]+$", max_length=2000)
    market: Literal["US"] = "US"
    marketplace: Literal["amazon_us"] = "amazon_us"
    product_scope: str = Field(min_length=2, max_length=300)
    revision: str = Field(min_length=1, max_length=100)
    effective_at: str
    review_due_at: str
    exact_excerpt: str = Field(min_length=5, max_length=3000)
    applicability_reason: str = Field(min_length=10, max_length=2000)
