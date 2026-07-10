"""Unit tests for the Pydantic `TicketCreate` schema's own validation rules,
independent of the HTTP layer.
"""

import pytest
from pydantic import ValidationError

from src.models.ticket import TicketCategory, TicketCreate, TicketStatus


def _base_payload(**overrides) -> dict:
    payload = {
        "customer_id": "cust-1",
        "customer_email": "person@example.com",
        "customer_name": "Person One",
        "subject": "A valid subject line",
        "description": "This description is definitely long enough to be valid.",
    }
    payload.update(overrides)
    return payload


def test_create_minimal_ticket_valid():
    ticket = TicketCreate(**_base_payload())
    assert ticket.customer_email == "person@example.com"
    assert ticket.category is None
    assert ticket.priority is None


def test_missing_required_field_raises():
    payload = _base_payload()
    del payload["customer_email"]
    with pytest.raises(ValidationError):
        TicketCreate(**payload)


def test_invalid_email_format_raises():
    with pytest.raises(ValidationError):
        TicketCreate(**_base_payload(customer_email="not-an-email"))


def test_subject_too_short_raises():
    with pytest.raises(ValidationError):
        TicketCreate(**_base_payload(subject=""))


def test_subject_too_long_raises():
    with pytest.raises(ValidationError):
        TicketCreate(**_base_payload(subject="x" * 201))


def test_description_too_short_raises():
    with pytest.raises(ValidationError):
        TicketCreate(**_base_payload(description="too short"))


def test_description_too_long_raises():
    with pytest.raises(ValidationError):
        TicketCreate(**_base_payload(description="x" * 2001))


def test_invalid_category_value_raises():
    with pytest.raises(ValidationError):
        TicketCreate(**_base_payload(category="not_a_real_category"))


def test_default_status_and_metadata_applied():
    ticket = TicketCreate(**_base_payload())
    assert ticket.status == TicketStatus.NEW
    assert ticket.metadata.source is not None
    assert ticket.tags == []


def test_valid_category_and_priority_accepted():
    ticket = TicketCreate(**_base_payload(category="billing_question", priority="high"))
    assert ticket.category == TicketCategory.BILLING_QUESTION
    assert ticket.priority.value == "high"
