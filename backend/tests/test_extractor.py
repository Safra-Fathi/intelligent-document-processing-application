from app.pipeline.extractor import extract_fields


def field_map(fields):
    return {
        field["field_name"]: field["value"]
        for field in fields
    }


def test_extract_invoice_fields_and_multiple_line_items():
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
    Currency: USD
    """

    fields = extract_fields(
        text,
        "INVOICE",
    )

    values = field_map(fields)

    assert values["document_number"] == "INV-1001"
    assert values["document_date"] == "2026-09-22"
    assert values["vendor"] == "ABC Technology"
    assert values["customer"] == "Neirah Tech"

    assert values["line_item_1_description"] == "Laptop Stand"
    assert values["line_item_1_quantity"] == "2"
    assert values["line_item_1_unit_price"] == "25.00"
    assert values["line_item_1_line_total"] == "50.00"

    assert values["line_item_2_description"] == "Wireless Mouse"
    assert values["line_item_2_quantity"] == "3"
    assert values["line_item_2_unit_price"] == "20.00"
    assert values["line_item_2_line_total"] == "60.00"

    assert values["subtotal"] == "110.00"
    assert values["discount"] == "10.00"
    assert values["tax"] == "5.00"
    assert values["charges"] == "5.00"
    assert values["grand_total"] == "110.00"
    assert values["currency"] == "USD"


def test_extract_lkr_currency():
    text = """
    RECEIPT
    Receipt No: REC-500
    Date: 2026-09-22
    Merchant: Colombo Store

    Notebook 2 500.00 1000.00

    Subtotal: LKR 1000.00
    Total Paid: LKR 1000.00
    """

    fields = extract_fields(
        text,
        "RECEIPT",
    )

    values = field_map(fields)

    assert values["document_number"] == "REC-500"
    assert values["vendor"] == "Colombo Store"
    assert values["currency"] == "LKR"
    assert values["line_item_1_description"] == "Notebook"
    assert values["line_item_1_quantity"] == "2"
    assert values["line_item_1_line_total"] == "1000.00"