from app.pipeline.extractor import extract_fields
from app.pipeline.validator import validate_document


def issue_codes(issues):
    return {
        issue["issue_code"]
        for issue in issues
    }


def test_valid_invoice_is_auto_accepted():
    text = """
    INVOICE
    Invoice No: INV-1001
    Invoice Date: 2026-09-22
    Vendor: ABC Technology
    Bill To: Neirah Tech

    Laptop Stand 2 25.00 50.00
    Wireless Mouse 3 20.00 60.00

    Subtotal: USD 110.00
    Discount: USD 10.00
    Tax: USD 5.00
    Shipping: USD 5.00
    Grand Total: USD 110.00
    """

    fields = extract_fields(
        text,
        "INVOICE",
    )

    issues, review_status = validate_document(
        fields=fields,
        document_type="INVOICE",
        classification_confidence=0.95,
    )

    assert issues == []
    assert review_status == "AUTO_ACCEPTED"


def test_incorrect_arithmetic_requires_manual_review():
    text = """
    INVOICE
    Invoice No: INV-1002
    Invoice Date: 2026-09-22
    Vendor: ABC Technology
    Bill To: Neirah Tech

    Laptop Stand 2 25.00 70.00
    Wireless Mouse 3 20.00 60.00

    Subtotal: USD 120.00
    Discount: USD 10.00
    Tax: USD 5.00
    Shipping: USD 5.00
    Grand Total: USD 150.00
    """

    fields = extract_fields(
        text,
        "INVOICE",
    )

    issues, review_status = validate_document(
        fields=fields,
        document_type="INVOICE",
        classification_confidence=0.95,
    )

    codes = issue_codes(issues)

    assert "LINE_TOTAL_MISMATCH" in codes
    assert "SUBTOTAL_MISMATCH" in codes
    assert "TOTAL_MISMATCH" in codes

    assert review_status == "MANUAL_REQUIRED"


def test_unknown_document_requires_manual_review():
    fields = extract_fields(
        "This is an unrelated document.",
        "UNKNOWN",
    )

    issues, review_status = validate_document(
        fields=fields,
        document_type="UNKNOWN",
        classification_confidence=0.40,
    )

    codes = issue_codes(issues)

    assert "UNKNOWN_DOCUMENT_TYPE" in codes
    assert review_status == "MANUAL_REQUIRED"


def test_missing_critical_fields_require_manual_review():
    text = """
    INVOICE
    Vendor: ABC Technology

    Product 1 50.00 50.00

    Subtotal: USD 50.00
    """

    fields = extract_fields(
        text,
        "INVOICE",
    )

    issues, review_status = validate_document(
        fields=fields,
        document_type="INVOICE",
        classification_confidence=0.95,
    )

    codes = issue_codes(issues)

    assert "MISSING_REQUIRED_FIELD" in codes
    assert review_status == "MANUAL_REQUIRED"


def test_due_date_before_document_date_is_invalid():
    text = """
    INVOICE
    Invoice No: INV-2001
    Invoice Date: 2026-09-22
    Due Date: 2026-09-10
    Vendor: ABC Technology

    Service 1 100.00 100.00

    Subtotal: USD 100.00
    Grand Total: USD 100.00
    """

    fields = extract_fields(
        text,
        "INVOICE",
    )

    issues, review_status = validate_document(
        fields=fields,
        document_type="INVOICE",
        classification_confidence=0.95,
    )

    codes = issue_codes(issues)

    assert "INVALID_DATE_RELATIONSHIP" in codes
    assert review_status == "MANUAL_REQUIRED"


def test_medium_classifier_confidence_recommends_review():
    text = """
    INVOICE
    Invoice No: INV-3001
    Invoice Date: 2026-09-22
    Vendor: ABC Technology

    Service 1 100.00 100.00

    Subtotal: USD 100.00
    Grand Total: USD 100.00
    """

    fields = extract_fields(
        text,
        "INVOICE",
    )

    issues, review_status = validate_document(
        fields=fields,
        document_type="INVOICE",
        classification_confidence=0.82,
    )

    assert not any(
        issue["severity"] == "ERROR"
        for issue in issues
    )

    assert review_status == "REVIEW_RECOMMENDED"