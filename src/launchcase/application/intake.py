import csv
import io
import json
from datetime import datetime, timezone

from launchcase.domain.common import DomainError, digest, now


def parse_import(request):
    raw = request.content.encode("utf-8")
    if len(raw) > 1048576 or "\x00" in request.content or request.content.lstrip().startswith(("<", "#!")):
        raise DomainError("UNSAFE_FILE", "Only bounded inert UTF-8 text/CSV/JSON is accepted")
    try:
        if request.filename.endswith(".csv"):
            reader = csv.DictReader(io.StringIO(request.content))
            if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
                raise ValueError("Invalid header")
            rows = list(reader)
            if any(None in r or None in r.values() for r in rows):
                raise ValueError("Malformed CSV row")
        elif request.filename.endswith(".json"):
            value = json.loads(request.content, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
            rows = value if isinstance(value, list) else [value]
        else:
            rows = [{"text": line} for line in request.content.splitlines() if line.strip()]
        if not rows or len(rows) > 5000 or any(not isinstance(x, dict) for x in rows):
            raise ValueError("Expected 1..5000 record objects")
        normalized = []
        for i, row in enumerate(rows, 2 if request.filename.endswith(".csv") else 1):
            quote = row.get(
                "review_text", row.get("text", json.dumps(row, ensure_ascii=False, sort_keys=True))
            )
            if not isinstance(quote, str) or not quote.strip() or len(quote) > 20000:
                raise ValueError("Invalid quote")
            if request.source_type == "review" and not row.get("review_text", row.get("text")):
                raise ValueError("Review text required")
            dt = row.get("review_date", row.get("collected_at", request.collected_at))
            if dt:
                dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                observed = dt.astimezone(timezone.utc).isoformat()
            else:
                observed = None
            synthetic = (
                request.is_synthetic
                or request.rights_status == "synthetic_fixture"
                or str(row.get("is_synthetic", "")).lower() == "true"
            )
            # Identical wording does not establish one reviewer/event. Preserve
            # independently identified/date-stamped rows and variant conflicts.
            fingerprint = digest({"type": request.source_type, "raw_row": row})
            normalized.append(
                {
                    "quote": quote,
                    "fingerprint": fingerprint,
                    "row": i,
                    "is_synthetic": synthetic,
                    "data": {
                        "raw": row,
                        "observed_at": observed,
                        "collected_at": request.collected_at or now(),
                        "classification": "observed",
                        "product_identity": row.get("product_id", "unresolved"),
                        "variant": row.get("variant", "unknown"),
                        "source_type": request.source_type,
                        "identity_status": "unverified",
                        "flags": [] if observed else ["date_unknown"],
                    },
                }
            )
        return raw, normalized
    except (ValueError, TypeError, csv.Error, OverflowError) as exc:
        raise DomainError("INVALID_SOURCE", "Malformed source; no rows were imported") from exc
