"""Locatable source proofs, independent of model self-reported citations."""

from launchcase.application.intake import parse_import
from launchcase.domain.common import DomainError, digest
from launchcase.domain.contracts import SourceImport
from launchcase.infrastructure.models import Artifact, Evidence, SourceDocument


def evidence_proof(service, s, actor, case_id, evidence):
    source = service.get_row(s, SourceDocument, actor, evidence["source_id"])
    if source.case_id != case_id or source.rights_status not in {"authorized", "synthetic_fixture"}:
        raise DomainError(
            "CITATION_UNLOCATABLE", "Citation source is outside the current authorized case", 409
        )
    raw = service.objects.get(source.sha256)
    _, rows = parse_import(
        SourceImport(
            filename=source.filename,
            content=raw.decode("utf-8"),
            source_type=source.source_type,
            rights_status=source.rights_status,
            is_synthetic=source.is_synthetic,
            collected_at=source.metadata_json.get("collected_at"),
        )
    )
    row = next((r for r in rows if f"{source.filename}#row={r['row']}" == evidence["source_locator"]), None)
    if not row or row["quote"] != evidence["quote"] or row["fingerprint"] != evidence["fingerprint"]:
        raise DomainError("CITATION_UNLOCATABLE", "Citation does not match the immutable original row", 409)
    return {
        "evidence_id": evidence["id"],
        "source_id": source.id,
        "source_sha256": source.sha256,
        "row_sha256": digest(row["data"]["raw"]),
        "source_locator": evidence["source_locator"],
        "excerpt": evidence["quote"],
        "rights_status": source.rights_status,
        "is_synthetic": source.is_synthetic,
        "product_identity": row["data"]["product_identity"],
        "variant": row["data"]["variant"],
        "observed_at": row["data"]["observed_at"],
    }


def insight_provenance(service, actor, insight_id):
    from launchcase.application.services import row_dict

    with service.sessions() as s:
        insight = service.get_row(s, Artifact, actor, insight_id)
        if insight.kind != "Insight":
            raise DomainError("NOT_FOUND", "Insight not found", 404)
        proof = insight.data.get("provenance")
        if not proof:
            return {"current": False, "reason": "PROVENANCE_NOT_RECORDED", "reviewer_decision": "pending"}
        current, reasons = True, []
        for citation in proof["citations"]:
            try:
                item = service.get_row(s, Evidence, actor, citation["evidence_id"])
                if (
                    item.case_id != insight.case_id
                    or evidence_proof(service, s, actor, insight.case_id, row_dict(item)) != citation
                ):
                    raise DomainError("CITATION_CHANGED", "Citation changed", 409)
            except DomainError as exc:
                current = False
                reasons.append(exc.code)
        return {
            **proof,
            "current": current,
            "reasons": sorted(set(reasons)),
            "subject_sha256": insight.sha256,
            "reviewer_decision": "pending",
            "classification": "inferred",
            "business_accepted": False,
        }
