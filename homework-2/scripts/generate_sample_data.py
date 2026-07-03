"""Generates the deliverable sample data files required by TASKS.md:

    demo/sample_tickets.csv   (50 valid tickets)
    demo/sample_tickets.json  (20 valid tickets)
    demo/sample_tickets.xml   (30 valid tickets)
    demo/invalid_sample_tickets.{csv,json,xml}  (negative-test fixtures)

Run with: `python scripts/generate_sample_data.py` from the `homework-2/` directory.
Deterministic (seeded) so re-running produces identical output.
"""

from __future__ import annotations

import csv
import io
import json
import random
from pathlib import Path
from xml.sax.saxutils import escape

from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "demo"

CATEGORY_TEMPLATES = {
    "account_access": [
        ("Cannot log in to my account", "I forgot my password and the reset email never arrived, I'm locked out."),
        ("Two-factor authentication not working", "My 2FA app codes are being rejected every time I try to sign in."),
        ("Need to reset my password", "I would like to reset my password but the confirmation link keeps expiring."),
        ("Locked out after too many login attempts", "I am locked out of my account after entering my password incorrectly."),
    ],
    "technical_issue": [
        ("Application crashes on startup", "The app crashes every time I open it on my laptop after the last update."),
        ("Getting a 500 error on checkout", "I keep getting an internal server error when trying to check out."),
        ("Dashboard freezes when loading reports", "The dashboard hangs and never finishes loading the monthly report."),
        ("Sync feature keeps failing", "The sync feature fails with an exception every time I try to run it."),
    ],
    "billing_question": [
        ("Question about my last invoice", "I was charged twice for my subscription this month and need a refund."),
        ("Refund request for duplicate charge", "My credit card was charged twice for the same order, please refund it."),
        ("Pricing for the enterprise plan", "Could you clarify the pricing details for the enterprise subscription tier?"),
        ("Unexpected charge on my account", "There is a billing charge on my account that I do not recognize at all."),
    ],
    "feature_request": [
        ("Feature request: dark mode", "It would be great if the app supported a dark mode theme option."),
        ("Suggestion: export to PDF", "Please add support for exporting reports directly to PDF format."),
        ("Enhancement idea for search", "An enhancement to add fuzzy search would really improve the experience."),
        ("Please add support for bulk editing", "It would be great to add support for editing multiple records at once."),
    ],
    "bug_report": [
        ("Save button misaligned", "Steps to reproduce: open settings, resize the window, the save button overlaps cancel."),
        ("Incorrect totals on invoice page", "Steps to reproduce: add three items to the cart; the expected behavior is a correct total but it is wrong."),
        ("Regression in filter dropdown", "This looks like a regression: the filter dropdown stopped working after the latest release."),
        ("Defect in date picker", "There is a defect in the date picker: selecting a past date shows the wrong month."),
    ],
    "other": [
        ("General inquiry about your company", "Just wanted to ask a general question about your company history."),
        ("Question about documentation", "I have a general question about where to find your API documentation."),
    ],
}

PRIORITY_SUFFIXES = {
    "urgent": " This is critical, our production is down and we can't access anything.",
    "high": " This is important and blocking our whole team, please handle asap.",
    "low": " This is just a minor, cosmetic suggestion, not urgent at all.",
    "medium": "",
}

CATEGORIES = list(CATEGORY_TEMPLATES.keys())
PRIORITIES = ["urgent", "high", "medium", "low"]
STATUSES = ["new", "in_progress", "waiting_customer", "resolved", "closed"]
SOURCES = ["web_form", "email", "api", "chat", "phone"]
DEVICE_TYPES = ["desktop", "mobile", "tablet"]
BROWSERS = ["Chrome", "Firefox", "Safari", "Edge"]
TAG_POOL = ["urgent", "billing", "login", "ui", "refund", "crash", "mobile", "vip"]
AGENTS = [None, None, "agent-1", "agent-2", "agent-3"]


def make_ticket(index: int) -> dict:
    category = CATEGORIES[index % len(CATEGORIES)]
    subject, description = random.choice(CATEGORY_TEMPLATES[category])
    priority = random.choice(PRIORITIES)
    description = description + PRIORITY_SUFFIXES[priority]
    return {
        "customer_id": f"cust-{1000 + index}",
        "customer_email": fake.unique.email(),
        "customer_name": fake.name(),
        "subject": subject,
        "description": description,
        "category": category,
        "priority": priority,
        "status": random.choice(STATUSES),
        "tags": random.sample(TAG_POOL, k=random.randint(0, 2)),
        "assigned_to": random.choice(AGENTS),
        "metadata": {
            "source": random.choice(SOURCES),
            "browser": random.choice(BROWSERS),
            "device_type": random.choice(DEVICE_TYPES),
        },
    }


def write_csv(path: Path, tickets: list[dict]) -> None:
    fieldnames = [
        "customer_id", "customer_email", "customer_name", "subject", "description",
        "category", "priority", "status", "tags", "assigned_to",
        "metadata_source", "metadata_browser", "metadata_device_type",
    ]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    for ticket in tickets:
        row = {
            "customer_id": ticket["customer_id"],
            "customer_email": ticket["customer_email"],
            "customer_name": ticket["customer_name"],
            "subject": ticket["subject"],
            "description": ticket["description"],
            "category": ticket["category"],
            "priority": ticket["priority"],
            "status": ticket["status"],
            "tags": ";".join(ticket["tags"]),
            "assigned_to": ticket["assigned_to"] or "",
            "metadata_source": ticket["metadata"]["source"],
            "metadata_browser": ticket["metadata"]["browser"],
            "metadata_device_type": ticket["metadata"]["device_type"],
        }
        writer.writerow(row)
    path.write_text(buffer.getvalue(), encoding="utf-8")


def write_json(path: Path, tickets: list[dict]) -> None:
    path.write_text(json.dumps({"tickets": tickets}, indent=2), encoding="utf-8")


def write_xml(path: Path, tickets: list[dict]) -> None:
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', "<tickets>"]
    for ticket in tickets:
        lines.append("  <ticket>")
        for field in (
            "customer_id", "customer_email", "customer_name", "subject",
            "description", "category", "priority", "status",
        ):
            lines.append(f"    <{field}>{escape(str(ticket[field]))}</{field}>")
        if ticket["assigned_to"]:
            lines.append(f"    <assigned_to>{escape(ticket['assigned_to'])}</assigned_to>")
        if ticket["tags"]:
            lines.append("    <tags>")
            for tag in ticket["tags"]:
                lines.append(f"      <tag>{escape(tag)}</tag>")
            lines.append("    </tags>")
        lines.append("    <metadata>")
        for key, value in ticket["metadata"].items():
            lines.append(f"      <{key}>{escape(str(value))}</{key}>")
        lines.append("    </metadata>")
        lines.append("  </ticket>")
    lines.append("</tickets>")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_invalid_records(count: int) -> list[dict]:
    """Deliberately broken records covering the main validation failure modes."""
    templates = [
        {
            "customer_id": "cust-9001",
            "customer_email": "not-an-email",
            "customer_name": "Invalid Email",
            "subject": "Bad email test",
            "description": "This record has an invalid email address for negative testing purposes.",
        },
        {
            "customer_id": "cust-9002",
            "customer_email": "shortdesc@example.com",
            "customer_name": "Short Description",
            "subject": "Description too short",
            "description": "Too short",
        },
        {
            "customer_id": "cust-9003",
            "customer_email": "badcategory@example.com",
            "customer_name": "Bad Category",
            "subject": "Invalid category value",
            "description": "This record uses a category value that is not part of the allowed enum.",
            "category": "not_a_real_category",
        },
        {
            "customer_id": "cust-9004",
            "customer_email": "badpriority@example.com",
            "customer_name": "Bad Priority",
            "subject": "Invalid priority value",
            "description": "This record uses a priority value that is not part of the allowed enum.",
            "priority": "super-urgent",
        },
        {
            "customer_id": "",
            "customer_email": "missingcustomerid@example.com",
            "customer_name": "Missing Customer Id",
            "subject": "Missing customer id",
            "description": "This record is missing the required customer_id field entirely.",
        },
    ]
    return templates[:count]


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    csv_tickets = [make_ticket(i) for i in range(50)]
    json_tickets = [make_ticket(i) for i in range(50, 70)]
    xml_tickets = [make_ticket(i) for i in range(70, 100)]

    write_csv(OUTPUT_DIR / "sample_tickets.csv", csv_tickets)
    write_json(OUTPUT_DIR / "sample_tickets.json", json_tickets)
    write_xml(OUTPUT_DIR / "sample_tickets.xml", xml_tickets)

    invalid = build_invalid_records(5)
    write_csv(
        OUTPUT_DIR / "invalid_sample_tickets.csv",
        [
            {
                "customer_id": r.get("customer_id", ""),
                "customer_email": r.get("customer_email", ""),
                "customer_name": r.get("customer_name", ""),
                "subject": r.get("subject", ""),
                "description": r.get("description", ""),
                "category": r.get("category", ""),
                "priority": r.get("priority", ""),
                "status": "new",
                "tags": [],
                "assigned_to": None,
                "metadata": {"source": "api", "browser": "", "device_type": ""},
            }
            for r in invalid
        ],
    )
    write_json(
        OUTPUT_DIR / "invalid_sample_tickets.json",
        [{**r, "status": "new"} for r in invalid],
    )
    write_xml(
        OUTPUT_DIR / "invalid_sample_tickets.xml",
        [
            {
                **r,
                "category": r.get("category", "other"),
                "priority": r.get("priority", "medium"),
                "status": "new",
                "tags": [],
                "assigned_to": None,
                "metadata": {"source": "api"},
            }
            for r in invalid
        ],
    )

    print(f"Wrote sample data to {OUTPUT_DIR}")
    print(f"  sample_tickets.csv:  {len(csv_tickets)} tickets")
    print(f"  sample_tickets.json: {len(json_tickets)} tickets")
    print(f"  sample_tickets.xml:  {len(xml_tickets)} tickets")
    print(f"  invalid_sample_tickets.{{csv,json,xml}}: {len(invalid)} records each")


if __name__ == "__main__":
    main()
