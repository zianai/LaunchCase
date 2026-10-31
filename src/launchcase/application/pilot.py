"""Read-only evaluation export; no evaluator can mint business approval."""

from sqlalchemy import select

from launchcase.application.provenance import insight_provenance
from launchcase.application.services import row_dict
from launchcase.domain.common import DomainError, digest
from launchcase.infrastructure.models import Artifact, SourceDocument
from launchcase.validation import PolicyDenied, ValidationRunPolicy


def export_pilot(service, actor, case_id, policy=None):
    case = service.get_case(actor, case_id)
    with service.sessions() as session:
        sources = [
            row_dict(source)
            for source in session.scalars(
                select(SourceDocument)
                .where(SourceDocument.tenant_id == actor.tenant_id, SourceDocument.case_id == case_id)
                .order_by(SourceDocument.created_at, SourceDocument.id)
                .limit(5001)
            )
        ]
    if len(sources) > 5000:
        raise DomainError(
            "PILOT_EXPORT_LIMIT",
            "Pilot export requires a complete manifest; split the dataset before review",
            409,
        )
    scope = {
        "case_id": case_id,
        "revision": case["revision"],
        "sources": [{"id": s["id"], "sha256": s["sha256"], "rights": s["rights_status"]} for s in sources],
    }
    contains_real_source = not case["is_synthetic"] or any(not s["is_synthetic"] for s in sources)
    if contains_real_source:
        # Reuse the existing OS-issued P7 grant; neither API nor evaluator issues grants.
        policy = policy or ValidationRunPolicy.from_env("launchcase")
        try:
            request = {
                **policy.context(),
                "action": "inspect_customer_data",
                "tenant_id": actor.tenant_id,
                "case_id": case_id,
                "input_hash": digest(scope),
                "rights_hash": digest(scope["sources"]),
                "rights_current": bool(sources) and all(s["rights_status"] == "authorized" for s in sources),
            }
            if request.get("data_classification") == "synthetic":
                raise PolicyDenied("DATA_CLASSIFICATION_MISMATCH")
            policy.validate(request, 0)
        except (PolicyDenied, OSError) as exc:
            raise DomainError(
                "BLOCKED_EXTERNAL", "Private pilot export needs a pinned operator data grant", 403
            ) from exc
    insights = service.list_scoped(actor, case_id, Artifact, limit=5000, kind="Insight")
    result = {
        "schema_version": "1.0.0",
        "project": "launchcase",
        "case_id": case_id,
        "tenant_id": actor.tenant_id,
        "revision": case["revision"],
        "synthetic": not contains_real_source,
        "source_manifest": [
            {
                "source_id": s["id"],
                "sha256": s["sha256"],
                "rights_status": s["rights_status"],
                "is_synthetic": s["is_synthetic"],
                "captured_at": s["created_at"],
            }
            for s in sources
        ],
        "insights": [
            {
                "id": i["id"],
                "claim": i["data"]["interpretation"],
                "provenance": insight_provenance(service, actor, i["id"]),
            }
            for i in insights
        ],
        "reviewers": [],
        "business_pilot_accepted": False,
        "metrics": {
            "paired_time_saved_ratio": None,
            "insight_accepted_rate": None,
            "status": "not_evaluable",
            "reason": "Independent human reviews and paired baselines required",
        },
        "external_publication_authorized": False,
    }
    return {**result, "subject_sha256": digest(result)}
