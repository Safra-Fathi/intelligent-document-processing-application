import re
from typing import Any


FIELD_PATTERNS = {
    "document_number": [
        r"(?:invoice\s*(?:number|no\.?|#)|quote\s*(?:number|no\.?|#)|receipt\s*(?:number|no\.?|#))\s*:?\s*([A-Z0-9\-]+)",
    ],
    "document_date": [
        r"(?:invoice\s+date|quotation\s+date|quote\s+date|date)\s*:?\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})",
        r"(?:invoice\s+date|quotation\s+date|quote\s+date|date)\s*:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{4})",
    ],
    "due_date": [
        r"due\s+date\s*:?\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})",
    ],
    "valid_until": [
        r"valid\s+until\s*:?\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})",
    ],
    "vendor": [
        r"(?:vendor|merchant|prepared\s+by)\s*:?\s*([^\n]+)",
    ],
    "customer": [
        r"(?:bill\s+to|customer)\s*:?\s*([^\n]+)",
    ],
    "subtotal": [
        r"subtotal\s*:?\s*(?:USD|\$)?\s*([\d,]+(?:\.\d{1,2})?)",
    ],
    "discount": [
        r"discount\s*:?\s*(?:USD|\$)?\s*([\d,]+(?:\.\d{1,2})?)",
    ],
    "tax": [
        r"(?:estimated\s+tax|tax)\s*:?\s*(?:USD|\$)?\s*([\d,]+(?:\.\d{1,2})?)",
    ],
    "charges": [
        r"(?:additional\s+charges|charges|shipping)\s*:?\s*(?:USD|\$)?\s*([\d,]+(?:\.\d{1,2})?)",
    ],
    "grand_total": [
        r"(?:grand\s+total|quoted\s+total|total\s+paid|total)\s*:?\s*(?:USD|\$)?\s*([\d,]+(?:\.\d{1,2})?)",
    ],
}


def _find_value(text: str, patterns: list[str]) -> str | None:
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
    Initial explainable confidence heuristic.

    This is extraction confidence, not classifier confidence.
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


def extract_fields(
    text: str,
    document_type: str,
) -> list[dict[str, Any]]:

    results = []

    for field_name, patterns in FIELD_PATTERNS.items():
        value = _find_value(text, patterns)

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

    # Currency detection
    currency = None

    if re.search(r"\bUSD\b|\$", text, re.IGNORECASE):
        currency = "USD"
    elif re.search(r"\bLKR\b|Rs\.?|රු", text, re.IGNORECASE):
        currency = "LKR"
    elif re.search(r"\bEUR\b|€", text, re.IGNORECASE):
        currency = "EUR"

    results.append(
        {
            "field_name": "currency",
            "value": currency,
            "confidence": 0.95 if currency else 0.0,
        }
    )

    return results