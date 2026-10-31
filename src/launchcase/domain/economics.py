from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from launchcase.domain.common import DomainError

COMPONENTS = ("net_sales_revenue_ex_tax", "ex_factory", "freight", "tariff_duty", "import_handling",
              "referral_fee", "fulfillment", "variable_storage", "advertising_allocated", "returns_allowance", "other_variable_costs")
FIXED = {"rnd", "tooling", "sample", "overhead"}


def instant(value):
    try:
        date = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if date.tzinfo is None:
            raise ValueError()
        return date.astimezone(timezone.utc)
    except (ValueError, TypeError) as exc:
        raise DomainError("INVALID_DATE", "An ISO timestamp with timezone is required") from exc


def calculate(request, valid_sources, at=None):
    at = at or datetime.now(timezone.utc)
    if set(request.components) - set(COMPONENTS) or set(request.fixed_costs) - FIXED:
        raise DomainError("COST_COMPONENT", "Unknown or double-counted cost component")
    rates = {}
    for rate in request.fx_rates:
        if rate.currency in rates or rate.currency == "USD":
            raise DomainError("FX_CONFLICT", "Duplicate or unnecessary FX rate")
        if rate.source_id not in valid_sources or instant(rate.effective_at) > at:
            raise DomainError("FX_SOURCE", "FX requires an effective, current source")
        value = Decimal(rate.usd_per_unit)
        if not value.is_finite() or value <= 0:
            raise DomainError("FX_RATE", "Positive finite FX rate required")
        rates[rate.currency] = value
    missing, conditional = [], []

    def convert(name, item):
        if item is None or item.amount is None or item.provenance == "missing":
            missing.append(name)
            return None
        if item.provenance == "quote" and item.source_id not in valid_sources:
            missing.append(name + ":invalid_or_expired_source")
            return None
        if item.provenance == "assumption":
            conditional.append(name)
        try:
            amount = Decimal(item.amount)
        except InvalidOperation as exc:
            raise DomainError("COST_AMOUNT", "Invalid decimal amount") from exc
        if not amount.is_finite() or amount < 0 or amount > Decimal("1000000000"):
            raise DomainError("COST_AMOUNT", "Amount outside finite nonnegative range")
        divisor = Decimal(12) if item.unit == "dozen" else Decimal(item.units_per_carton or 0) if item.unit == "carton" else Decimal(1)
        if divisor <= 0:
            raise DomainError("COST_UNIT", "Carton requires a positive pieces-per-carton count")
        rate = Decimal(1) if item.currency == "USD" else rates.get(item.currency)
        if rate is None:
            missing.append(name + ":fx_missing")
            return None
        return amount * rate / divisor

    values = {name: convert(name, request.components.get(name)) for name in COMPONENTS}
    fixed = {name: convert("fixed_"+name, item) for name, item in request.fixed_costs.items()}
    required_missing = any(value is None for value in values.values())
    landed = None if any(values[x] is None for x in ("ex_factory", "freight", "tariff_duty", "import_handling")) else sum(values[x] for x in ("ex_factory", "freight", "tariff_duty", "import_handling"))
    contribution = None if required_missing else values[COMPONENTS[0]] - sum(values[x] for x in COMPONENTS[1:])
    def money(value):
        return None if value is None else str(value.quantize(Decimal("0.0001")))
    return {"currency": "USD", "unit": "piece", "components": {k: money(v) for k, v in values.items()},
            "fixed_costs": {k: money(v) for k, v in fixed.items()}, "landed_product_cost": money(landed),
            "unit_contribution": money(contribution), "missing": missing, "assumed_components": conditional,
            "status": "needs_input" if required_missing else "conditional" if conditional else "calculated",
            "formula": "net_sales_revenue_ex_tax - ex_factory - freight - tariff_duty - import_handling - referral_fee - fulfillment - variable_storage - advertising_allocated - returns_allowance - other_variable_costs",
            "fixed_costs_excluded_from_unit_contribution": True, "assumptions": request.assumptions,
            "profitability_decision": "requires_human_review"}
