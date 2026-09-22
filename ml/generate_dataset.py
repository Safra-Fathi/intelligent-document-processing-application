import csv
import random
from pathlib import Path

random.seed(42)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

VENDORS = [
    "Nova Office Supplies",
    "GreenTech Solutions",
    "Metro Electronics",
    "BlueWave Trading",
    "Sunrise Stationery",
    "Alpha Business Services",
    "Prime Distribution",
    "City Computer Store",
]

CUSTOMERS = [
    "ABC Holdings",
    "Northstar Consulting",
    "Bright Future Ltd",
    "Global Retail Group",
    "Ocean View Enterprises",
]

ITEMS = [
    "Wireless Keyboard",
    "Office Chair",
    "Printer Paper",
    "Laptop Stand",
    "USB Cable",
    "Consulting Service",
    "Network Installation",
    "Printer Cartridge",
]


def money(value: float) -> str:
    return f"{value:.2f}"


def generate_invoice(index: int) -> str:
    vendor = random.choice(VENDORS)
    customer = random.choice(CUSTOMERS)
    item = random.choice(ITEMS)

    quantity = random.randint(1, 8)
    unit_price = random.uniform(20, 300)
    line_total = quantity * unit_price
    tax = line_total * 0.10
    total = line_total + tax

    return f"""
INVOICE

Invoice Number: INV-{1000 + index}
Invoice Date: 2026-09-{random.randint(1, 28):02d}
Due Date: 2026-10-{random.randint(1, 28):02d}

Vendor: {vendor}
Bill To: {customer}

Description: {item}
Quantity: {quantity}
Unit Price: USD {money(unit_price)}
Line Total: USD {money(line_total)}

Subtotal: USD {money(line_total)}
Tax: USD {money(tax)}
Grand Total: USD {money(total)}

Payment Terms: Net 30
Thank you for your business.
""".strip()


def generate_quotation(index: int) -> str:
    vendor = random.choice(VENDORS)
    customer = random.choice(CUSTOMERS)
    item = random.choice(ITEMS)

    quantity = random.randint(1, 10)
    unit_price = random.uniform(30, 500)
    subtotal = quantity * unit_price
    tax = subtotal * 0.10
    total = subtotal + tax

    return f"""
QUOTATION

Quote Number: QT-{2000 + index}
Quotation Date: 2026-09-{random.randint(1, 28):02d}
Valid Until: 2026-10-{random.randint(1, 28):02d}

Prepared By: {vendor}
Customer: {customer}

Item Description: {item}
Quantity: {quantity}
Unit Price: USD {money(unit_price)}
Amount: USD {money(subtotal)}

Subtotal: USD {money(subtotal)}
Estimated Tax: USD {money(tax)}
Quoted Total: USD {money(total)}

This quotation is valid for 30 days.
Prices are subject to the stated terms.
""".strip()


def generate_receipt(index: int) -> str:
    vendor = random.choice(VENDORS)
    item = random.choice(ITEMS)

    quantity = random.randint(1, 5)
    unit_price = random.uniform(5, 150)
    subtotal = quantity * unit_price
    tax = subtotal * 0.08
    total = subtotal + tax

    return f"""
SALES RECEIPT

Receipt No: RCP-{3000 + index}
Date: 2026-09-{random.randint(1, 28):02d}

Merchant: {vendor}

{item}
Qty: {quantity}
Price: USD {money(unit_price)}
Amount: USD {money(subtotal)}

Subtotal: USD {money(subtotal)}
Tax: USD {money(tax)}
Total Paid: USD {money(total)}

Payment Method: Card
Payment Status: PAID

Thank you for your purchase.
""".strip()


def build_examples(count_per_class: int):
    examples = []

    generators = {
        "INVOICE": generate_invoice,
        "QUOTATION": generate_quotation,
        "RECEIPT": generate_receipt,
    }

    for label, generator in generators.items():
        for index in range(count_per_class):
            examples.append(
                {
                    "text": generator(index),
                    "label": label,
                }
            )

    random.shuffle(examples)
    return examples


def write_csv(path: Path, examples):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["text", "label"],
        )
        writer.writeheader()
        writer.writerows(examples)


def main():
    datasets = {
        "train": build_examples(120),
        "dev": build_examples(30),
        "eval": build_examples(30),
    }

    for split, examples in datasets.items():
        output = DATA_DIR / split / "documents.csv"
        write_csv(output, examples)

        print(
            f"{split}: {len(examples)} examples -> {output}"
        )


if __name__ == "__main__":
    main()