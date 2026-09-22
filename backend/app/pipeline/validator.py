import re
from datetime import datetime
from typing import Any


CRITICAL_FIELDS = {
    "document_number",
    "document_date",
    "grand_total",
    "currency",
}

FINANCIAL_FIELDS = {
    "subtotal",
    "discount",
    "tax",
    "charges",
    "grand_total",
}

ARITHMETIC_TOLERANCE = 0.05


def _to_number(
    value: str | None,
) -> float | None:
    if value is None:
        return None

    try:
        cleaned = (
            value
            .replace(",", "")
            .replace("$", "")
            .replace("€", "")
            .replace("Rs.", "")
            .replace("Rs", "")
            .strip()
        )

        return float(cleaned)

    except (ValueError, AttributeError):
        return None


def _field_map(
    fields: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    return {
        field["field_name"]: field
        for field in fields
    }


def _add_issue(
    issues: list[dict[str, Any]],
    field_name: str | None,
    issue_code: str,
    severity: str,
    message: str,
) -> None:
    issues.append(
        {
            "field_name": field_name,
            "issue_code": issue_code,
            "severity": severity,
            "message": message,
        }
    )


def _parse_date(
    value: str,
) -> datetime | None:
    """
    Support common ISO and day/month style dates.

    Ambiguous DD/MM vs MM/DD values are interpreted as
    DD/MM/YYYY for this assessment implementation.
    """

    formats = (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
    )

    for date_format in formats:
        try:
            return datetime.strptime(
                value,
                date_format,
            )
        except ValueError:
            continue

    return None


def _collect_line_items(
    values: dict[str, dict[str, Any]],
) -> dict[int, dict[str, dict[str, Any]]]:
    """
    Convert generic line-item field names into grouped items.

    line_item_1_quantity
    line_item_1_unit_price
    line_item_1_line_total
             ↓
    items[1]["quantity"], etc.
    """

    items: dict[int, dict[str, dict[str, Any]]] = {}

    pattern = re.compile(
        r"^line_item_(\d+)_(description|quantity|unit_price|line_total)$"
    )

    for field_name, field in values.items():
        match = pattern.match(field_name)

        if not match:
            continue

        index = int(match.group(1))
        component = match.group(2)

        items.setdefault(
            index,
            {},
        )[component] = field

    return items


def _validate_numeric_fields(
    values: dict[str, dict[str, Any]],
    issues: list[dict[str, Any]],
) -> None:
    for field_name in FINANCIAL_FIELDS:
        field = values.get(field_name)

        if not field:
            continue

        raw_value = field.get("value")

        if raw_value is None:
            continue

        if _to_number(raw_value) is None:
            _add_issue(
                issues,
                field_name,
                "MALFORMED_NUMERIC_VALUE",
                "ERROR",
                (
                    f"Field '{field_name}' contains "
                    "an invalid numeric value."
                ),
            )


def _validate_line_items(
    values: dict[str, dict[str, Any]],
    issues: list[dict[str, Any]],
) -> None:
    items = _collect_line_items(values)

    if not items:
        _add_issue(
            issues,
            None,
            "NO_LINE_ITEMS_EXTRACTED",
            "WARNING",
            (
                "No line items could be extracted "
                "from the document."
            ),
        )

        return

    for index, item in items.items():
        quantity_field = item.get("quantity")
        unit_price_field = item.get("unit_price")
        line_total_field = item.get("line_total")

        if not (
            quantity_field
            and unit_price_field
            and line_total_field
        ):
            _add_issue(
                issues,
                f"line_item_{index}",
                "INCOMPLETE_LINE_ITEM",
                "WARNING",
                (
                    f"Line item {index} is missing "
                    "quantity, unit price or line total."
                ),
            )

            continue

        quantity = _to_number(
            quantity_field.get("value")
        )

        unit_price = _to_number(
            unit_price_field.get("value")
        )

        line_total = _to_number(
            line_total_field.get("value")
        )

        if (
            quantity is None
            or unit_price is None
            or line_total is None
        ):
            _add_issue(
                issues,
                f"line_item_{index}",
                "MALFORMED_LINE_ITEM_NUMBER",
                "ERROR",
                (
                    f"Line item {index} contains "
                    "an invalid numeric value."
                ),
            )

            continue

        expected_line_total = (
            quantity * unit_price
        )

        if (
            abs(
                expected_line_total
                - line_total
            )
            > ARITHMETIC_TOLERANCE
        ):
            _add_issue(
                issues,
                f"line_item_{index}_line_total",
                "LINE_TOTAL_MISMATCH",
                "ERROR",
                (
                    f"Line item {index}: quantity "
                    f"{quantity:g} × unit price "
                    f"{unit_price:.2f} = "
                    f"{expected_line_total:.2f}, "
                    f"but extracted line total is "
                    f"{line_total:.2f}."
                ),
            )


def _validate_subtotal(
    values: dict[str, dict[str, Any]],
    issues: list[dict[str, Any]],
) -> None:
    items = _collect_line_items(values)

    if not items:
        return

    line_totals: list[float] = []

    for item in items.values():
        line_total_field = item.get(
            "line_total"
        )

        if not line_total_field:
            return

        line_total = _to_number(
            line_total_field.get("value")
        )

        if line_total is None:
            return

        line_totals.append(line_total)

    subtotal = _to_number(
        values.get(
            "subtotal",
            {},
        ).get("value")
    )

    if subtotal is None:
        return

    expected_subtotal = sum(line_totals)

    if (
        abs(
            expected_subtotal
            - subtotal
        )
        > ARITHMETIC_TOLERANCE
    ):
        _add_issue(
            issues,
            "subtotal",
            "SUBTOTAL_MISMATCH",
            "ERROR",
            (
                f"Line items total "
                f"{expected_subtotal:.2f}, "
                f"but extracted subtotal is "
                f"{subtotal:.2f}."
            ),
        )


def _validate_grand_total(
    values: dict[str, dict[str, Any]],
    issues: list[dict[str, Any]],
) -> None:
    subtotal = _to_number(
        values.get(
            "subtotal",
            {},
        ).get("value")
    )

    grand_total = _to_number(
        values.get(
            "grand_total",
            {},
        ).get("value")
    )

    if (
        subtotal is None
        or grand_total is None
    ):
        return

    discount = (
        _to_number(
            values.get(
                "discount",
                {},
            ).get("value")
        )
        or 0.0
    )

    tax = (
        _to_number(
            values.get(
                "tax",
                {},
            ).get("value")
        )
        or 0.0
    )

    charges = (
        _to_number(
            values.get(
                "charges",
                {},
            ).get("value")
        )
        or 0.0
    )

    expected_total = (
        subtotal
        - discount
        + tax
        + charges
    )

    if (
        abs(
            expected_total
            - grand_total
        )
        > ARITHMETIC_TOLERANCE
    ):
        _add_issue(
            issues,
            "grand_total",
            "TOTAL_MISMATCH",
            "ERROR",
            (
                f"Expected total "
                f"{expected_total:.2f}, "
                f"but extracted grand total is "
                f"{grand_total:.2f}."
            ),
        )


def _validate_dates(
    values: dict[str, dict[str, Any]],
    issues: list[dict[str, Any]],
) -> None:
    document_date_value = values.get(
        "document_date",
        {},
    ).get("value")

    if not document_date_value:
        return

    document_date = _parse_date(
        document_date_value
    )

    if document_date is None:
        _add_issue(
            issues,
            "document_date",
            "MALFORMED_DATE",
            "ERROR",
            "Document date is not in a supported format.",
        )

        return

    for field_name in (
        "due_date",
        "valid_until",
    ):
        date_value = values.get(
            field_name,
            {},
        ).get("value")

        if not date_value:
            continue

        parsed_date = _parse_date(
            date_value
        )

        if parsed_date is None:
            _add_issue(
                issues,
                field_name,
                "MALFORMED_DATE",
                "WARNING",
                (
                    f"Field '{field_name}' is not "
                    "in a supported date format."
                ),
            )

            continue

        if parsed_date < document_date:
            _add_issue(
                issues,
                field_name,
                "INVALID_DATE_RELATIONSHIP",
                "ERROR",
                (
                    f"'{field_name}' occurs before "
                    "the document date."
                ),
            )


def validate_document(
    fields: list[dict[str, Any]],
    document_type: str,
    classification_confidence: float,
) -> tuple[list[dict[str, Any]], str]:
    issues: list[dict[str, Any]] = []

    values = _field_map(fields)

    # -----------------------------------------------------
    # Classification validation
    # -----------------------------------------------------

    if document_type == "UNKNOWN":
        _add_issue(
            issues,
            None,
            "UNKNOWN_DOCUMENT_TYPE",
            "ERROR",
            (
                "The document type could not be "
                "classified with sufficient confidence."
            ),
        )

    # -----------------------------------------------------
    # Mandatory fields
    # -----------------------------------------------------

    for field_name in CRITICAL_FIELDS:
        field = values.get(field_name)

        if (
            not field
            or not field.get("value")
        ):
            _add_issue(
                issues,
                field_name,
                "MISSING_REQUIRED_FIELD",
                "ERROR",
                (
                    f"Required field '{field_name}' "
                    "could not be extracted."
                ),
            )

    # -----------------------------------------------------
    # Critical-field confidence
    # -----------------------------------------------------

    for field_name in CRITICAL_FIELDS:
        field = values.get(field_name)

        if (
            field
            and field.get("value")
            and field.get(
                "confidence",
                0.0,
            ) < 0.70
        ):
            _add_issue(
                issues,
                field_name,
                "LOW_FIELD_CONFIDENCE",
                "WARNING",
                (
                    f"Critical field '{field_name}' "
                    "has low extraction confidence."
                ),
            )

    # -----------------------------------------------------
    # Business validation
    # -----------------------------------------------------

    _validate_numeric_fields(
        values,
        issues,
    )

    _validate_line_items(
        values,
        issues,
    )

    _validate_subtotal(
        values,
        issues,
    )

    _validate_grand_total(
        values,
        issues,
    )

    _validate_dates(
        values,
        issues,
    )

    # -----------------------------------------------------
    # Human-review routing
    # -----------------------------------------------------

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