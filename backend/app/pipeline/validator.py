from datetime import datetime
from typing import Any


CRITICAL_FIELDS = {
    "document_number",
    "document_date",
    "grand_total",
    "currency",
}


def _to_number(value: str | None) -> float | None:
    if value is None:
        return None

    try:
        return float(
            value.replace(",", "").strip()
        )
    except (ValueError, AttributeError):
        return None


def _field_map(
    fields: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    return {
        field["field_name"]: field
        for field in fields
    }


def validate_document(
    fields: list[dict[str, Any]],
    document_type: str,
    classification_confidence: float,
) -> tuple[list[dict[str, Any]], str]:

    issues: list[dict[str, Any]] = []
    values = _field_map(fields)

    # Unknown classification
    if document_type == "UNKNOWN":
        issues.append(
            {
                "field_name": None,
                "issue_code": "UNKNOWN_DOCUMENT_TYPE",
                "severity": "ERROR",
                "message": (
                    "The document type could not be "
                    "classified with sufficient confidence."
                ),
            }
        )

    # Required fields
    for field_name in CRITICAL_FIELDS:
        field = values.get(field_name)

        if not field or not field.get("value"):
            issues.append(
                {
                    "field_name": field_name,
                    "issue_code": "MISSING_REQUIRED_FIELD",
                    "severity": "ERROR",
                    "message": (
                        f"Required field '{field_name}' "
                        "could not be extracted."
                    ),
                }
            )

    # Low-confidence critical fields
    for field_name in CRITICAL_FIELDS:
        field = values.get(field_name)

        if (
            field
            and field.get("value")
            and field.get("confidence", 0) < 0.70
        ):
            issues.append(
                {
                    "field_name": field_name,
                    "issue_code": "LOW_FIELD_CONFIDENCE",
                    "severity": "WARNING",
                    "message": (
                        f"Critical field '{field_name}' "
                        "has low extraction confidence."
                    ),
                }
            )

    subtotal = _to_number(
        values.get("subtotal", {}).get("value")
    )

    discount = _to_number(
        values.get("discount", {}).get("value")
    ) or 0.0

    tax = _to_number(
        values.get("tax", {}).get("value")
    ) or 0.0

    charges = _to_number(
        values.get("charges", {}).get("value")
    ) or 0.0

    grand_total = _to_number(
        values.get("grand_total", {}).get("value")
    )

    # Financial consistency:
    # subtotal - discount + tax + charges = total
    if subtotal is not None and grand_total is not None:
        expected_total = (
            subtotal
            - discount
            + tax
            + charges
        )

        if abs(expected_total - grand_total) > 0.05:
            issues.append(
                {
                    "field_name": "grand_total",
                    "issue_code": "TOTAL_MISMATCH",
                    "severity": "ERROR",
                    "message": (
                        f"Expected total {expected_total:.2f} "
                        f"but extracted total is "
                        f"{grand_total:.2f}."
                    ),
                }
            )

    # Due date must not precede document date.
    document_date = values.get(
        "document_date", {}
    ).get("value")

    due_date = values.get(
        "due_date", {}
    ).get("value")

    if document_date and due_date:
        try:
            document_dt = datetime.fromisoformat(document_date)
            due_dt = datetime.fromisoformat(due_date)

            if due_dt < document_dt:
                issues.append(
                    {
                        "field_name": "due_date",
                        "issue_code": "INVALID_DATE_RELATIONSHIP",
                        "severity": "ERROR",
                        "message": (
                            "Due date occurs before "
                            "the document date."
                        ),
                    }
                )
        except ValueError:
            issues.append(
                {
                    "field_name": "document_date",
                    "issue_code": "MALFORMED_DATE",
                    "severity": "WARNING",
                    "message": (
                        "One or more dates could not "
                        "be validated."
                    ),
                }
            )

    # Review routing
    has_error = any(
        issue["severity"] == "ERROR"
        for issue in issues
    )

    has_warning = any(
        issue["severity"] == "WARNING"
        for issue in issues
    )

    if (
        document_type == "UNKNOWN"
        or classification_confidence < 0.70
        or has_error
    ):
        review_status = "MANUAL_REQUIRED"

    elif (
        classification_confidence < 0.90
        or has_warning
    ):
        review_status = "REVIEW_RECOMMENDED"

    else:
        review_status = "AUTO_ACCEPTED"

    return issues, review_status