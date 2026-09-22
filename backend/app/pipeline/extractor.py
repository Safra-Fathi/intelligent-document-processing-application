import re
from typing import Any


MONEY_PATTERN = r"[\d,]+(?:\.\d{1,2})?"


FIELD_PATTERNS = {
    "document_number": [
        r"(?:invoice\s*(?:number|no\.?|#)|invoice\s*#)\s*:?\s*([A-Z0-9\-/]+)",
        r"(?:quotation\s*(?:number|no\.?|#)|quote\s*(?:number|no\.?|#)|quote\s*#)\s*:?\s*([A-Z0-9\-/]+)",
        r"(?:receipt\s*(?:number|no\.?|#)|receipt\s*#)\s*:?\s*([A-Z0-9\-/]+)",
    ],
    "document_date": [
        r"(?:invoice\s+date|quotation\s+date|quote\s+date|receipt\s+date|issue\s+date|date)\s*:?\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})",
        r"(?:invoice\s+date|quotation\s+date|quote\s+date|receipt\s+date|issue\s+date|date)\s*:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{4})",
    ],
    "due_date": [
        r"due\s+date\s*:?\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})",
        r"due\s+date\s*:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{4})",
    ],
    "valid_until": [
        r"(?:valid\s+until|valid\s+through|expiry\s+date)\s*:?\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})",
        r"(?:valid\s+until|valid\s+through|expiry\s+date)\s*:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{4})",
    ],
    "vendor": [
        r"(?:vendor|merchant|seller|prepared\s+by|company)\s*:?\s*([^\n]+)",
    ],
    "customer": [
        r"(?:bill\s+to|customer|client|sold\s+to)\s*:?\s*([^\n]+)",
    ],
    "address": [
        r"(?:address|billing\s+address)\s*:?\s*([^\n]+)",
    ],
    "contact": [
        r"(?:phone|telephone|contact)\s*:?\s*([^\n]+)",
    ],
    "subtotal": [
        rf"subtotal\s*:?\s*(?:USD|LKR|EUR|Rs\.?|\$|€)?\s*({MONEY_PATTERN})",
    ],
    "discount": [
        rf"discount\s*:?\s*(?:USD|LKR|EUR|Rs\.?|\$|€)?\s*({MONEY_PATTERN})",
    ],
    "tax": [
        rf"(?:estimated\s+tax|sales\s+tax|vat|tax)\s*:?\s*(?:USD|LKR|EUR|Rs\.?|\$|€)?\s*({MONEY_PATTERN})",
    ],
    "charges": [
        rf"(?:additional\s+charges|service\s+charge|delivery|shipping|charges)\s*:?\s*(?:USD|LKR|EUR|Rs\.?|\$|€)?\s*({MONEY_PATTERN})",
    ],
   "grand_total": [
    rf"(?m)^[ \t]*(?:grand[ \t]+total|quoted[ \t]+total|total[ \t]+paid|amount[ \t]+due|final[ \t]+total|total)[ \t]*:?[ \t]*(?:USD|LKR|EUR|Rs\.?|\$|€)?[ \t]*({MONEY_PATTERN})[ \t]*$",
],
}


def _find_value(
    text: str,
    patterns: list[str],
) -> str | None:
    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:
            return match.group(1).strip()

    return None


def _field_confidence(
    value: str | None,
    field_name: str,
) -> float:
    """
    Explainable rule-based extraction confidence.

    This is separate from classifier probability.
    """

    if value is None:
        return 0.0

    if field_name in {
        "subtotal",
        "discount",
        "tax",
        "charges",
        "grand_total",
    }:
        return 0.95

    if field_name in {
        "document_number",
        "document_date",
        "due_date",
        "valid_until",
    }:
        return 0.92

    return 0.85


def _clean_money(value: str) -> str:
    return value.replace(",", "").strip()


def _looks_like_summary_line(line: str) -> bool:
    """
    Prevent totals such as 'Subtotal 100.00' from being
    incorrectly interpreted as line items.
    """

    lowered = line.lower().strip()

    summary_words = (
        "subtotal",
        "grand total",
        "total paid",
        "amount due",
        "final total",
        "quoted total",
        "discount",
        "tax",
        "vat",
        "shipping",
        "additional charges",
        "service charge",
    )

    return any(
        lowered.startswith(word)
        for word in summary_words
    )


def _extract_line_items(
    text: str,
) -> list[dict[str, Any]]:
    """
    Extract line items from common OCR text layouts.

    Expected patterns include examples such as:

        Laptop Stand 2 25.00 50.00
        Consulting Service   3   100.00   300.00

    The implementation is intentionally layout-tolerant:
    it works line-by-line and does not depend on fixed
    x/y coordinates.
    """

    items: list[dict[str, Any]] = []

    # Description | quantity | unit price | line total
    pattern = re.compile(
        rf"^\s*"
        rf"(.+?)"
        rf"\s+"
        rf"(\d+(?:\.\d+)?)"
        rf"\s+"
        rf"(?:USD|LKR|EUR|Rs\.?|\$|€)?\s*"
        rf"({MONEY_PATTERN})"
        rf"\s+"
        rf"(?:USD|LKR|EUR|Rs\.?|\$|€)?\s*"
        rf"({MONEY_PATTERN})"
        rf"\s*$",
        flags=re.IGNORECASE,
    )

    for raw_line in text.splitlines():
        line = " ".join(raw_line.split())

        if not line:
            continue

        if _looks_like_summary_line(line):
            continue

        match = pattern.match(line)

        if not match:
            continue

        description = match.group(1).strip()
        quantity = match.group(2).strip()
        unit_price = _clean_money(match.group(3))
        line_total = _clean_money(match.group(4))

        # Avoid treating table headers as data.
        if description.lower() in {
            "description",
            "item",
            "product",
            "service",
        }:
            continue

        items.append(
            {
                "description": description,
                "quantity": quantity,
                "unit_price": unit_price,
                "line_total": line_total,
            }
        )

    return items


def _append_line_item_fields(
    results: list[dict[str, Any]],
    line_items: list[dict[str, Any]],
) -> None:
    """
    Store line items using the existing generic field model.

    Example:
        line_item_1_description
        line_item_1_quantity
        line_item_1_unit_price
        line_item_1_line_total
    """

    for index, item in enumerate(
        line_items,
        start=1,
    ):
        prefix = f"line_item_{index}"

        results.extend(
            [
                {
                    "field_name": f"{prefix}_description",
                    "value": item["description"],
                    "confidence": 0.85,
                },
                {
                    "field_name": f"{prefix}_quantity",
                    "value": item["quantity"],
                    "confidence": 0.90,
                },
                {
                    "field_name": f"{prefix}_unit_price",
                    "value": item["unit_price"],
                    "confidence": 0.90,
                },
                {
                    "field_name": f"{prefix}_line_total",
                    "value": item["line_total"],
                    "confidence": 0.90,
                },
            ]
        )


def _detect_currency(
    text: str,
) -> str | None:
    if re.search(
        r"\bUSD\b|\$",
        text,
        re.IGNORECASE,
    ):
        return "USD"

    if re.search(
        r"\bLKR\b|\bRs\.?\s|\brupees?\b|රු",
        text,
        re.IGNORECASE,
    ):
        return "LKR"

    if re.search(
        r"\bEUR\b|€",
        text,
        re.IGNORECASE,
    ):
        return "EUR"

    return None


def extract_fields(
    text: str,
    document_type: str,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    # Extract common/document-level fields.
    for field_name, patterns in FIELD_PATTERNS.items():
        value = _find_value(
            text,
            patterns,
        )

        results.append(
            {
                "field_name": field_name,
                "value": value,
                "confidence": _field_confidence(
                    value,
                    field_name,
                ),
            }
        )

    # Extract line items.
    line_items = _extract_line_items(text)

    _append_line_item_fields(
        results,
        line_items,
    )

    # Detect currency independently.
    currency = _detect_currency(text)

    results.append(
        {
            "field_name": "currency",
            "value": currency,
            "confidence": 0.95 if currency else 0.0,
        }
    )

    return results