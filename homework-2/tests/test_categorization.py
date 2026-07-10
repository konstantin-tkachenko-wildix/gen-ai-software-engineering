"""Tests for the rule-based classifier (Task 2) and its API surface."""

from src.classification.classifier import classify_ticket
from src.models.ticket import TicketCategory, TicketPriority


def test_classify_account_access_keywords():
    outcome = classify_ticket(
        "Cannot log in", "I forgot my password and can't sign in to my account."
    )
    assert outcome.category == TicketCategory.ACCOUNT_ACCESS
    assert "password" in outcome.keywords_found


def test_classify_technical_issue_keywords():
    outcome = classify_ticket(
        "App keeps freezing", "The app hangs and throws an exception whenever I open it."
    )
    assert outcome.category == TicketCategory.TECHNICAL_ISSUE


def test_classify_billing_question_keywords():
    outcome = classify_ticket(
        "Question about my invoice", "I was charged twice and would like a refund on my billing."
    )
    assert outcome.category == TicketCategory.BILLING_QUESTION


def test_classify_feature_request_keywords():
    outcome = classify_ticket(
        "Feature request", "It would be great if you could add support for dark mode."
    )
    assert outcome.category == TicketCategory.FEATURE_REQUEST


def test_classify_bug_report_keywords():
    outcome = classify_ticket(
        "Save button broken",
        "Steps to reproduce: open settings, click save, the expected behavior does not occur.",
    )
    assert outcome.category == TicketCategory.BUG_REPORT


def test_classify_defaults_to_other_when_no_keywords():
    outcome = classify_ticket(
        "General inquiry", "Just wanted to say hello and ask about your company history."
    )
    assert outcome.category == TicketCategory.OTHER
    assert outcome.keywords_found == [] or all(
        kw not in outcome.keywords_found for kw in ("bug", "error")
    )


def test_priority_urgent_keywords():
    outcome = classify_ticket(
        "Production down", "This is critical, our production down and we can't access anything."
    )
    assert outcome.priority == TicketPriority.URGENT


def test_priority_high_keywords():
    outcome = classify_ticket(
        "Important request", "This is blocking our team, please handle asap."
    )
    assert outcome.priority == TicketPriority.HIGH


def test_priority_low_keywords():
    outcome = classify_ticket(
        "Minor cosmetic issue", "This is just a small suggestion, a minor cosmetic tweak."
    )
    assert outcome.priority == TicketPriority.LOW


def test_priority_defaults_to_medium():
    outcome = classify_ticket(
        "General inquiry", "Just wanted to say hello and ask about your company history."
    )
    assert outcome.priority == TicketPriority.MEDIUM


def test_confidence_score_within_bounds():
    outcome = classify_ticket(
        "Cannot log in, critical", "Password reset needed urgently, this is critical."
    )
    assert 0.0 <= outcome.confidence <= 1.0


def test_reasoning_and_keywords_present_for_matches():
    outcome = classify_ticket("Refund needed", "I need a refund for my last billing charge.")
    assert outcome.reasoning
    assert len(outcome.keywords_found) > 0


def test_auto_classify_endpoint_updates_ticket_and_logs_decision(client, valid_ticket_payload):
    from src.services import classification_service

    valid_ticket_payload["subject"] = "Can't log in, it's critical"
    created = client.post("/tickets", json=valid_ticket_payload).json()

    response = client.post(f"/tickets/{created['id']}/auto-classify")
    assert response.status_code == 200
    body = response.json()
    assert body["category"] == "account_access"
    assert body["priority"] == "urgent"
    assert body["classification"]["manually_overridden"] is False
    assert len(classification_service.classification_log) == 1


def test_manual_override_via_put_marks_manually_overridden(client, valid_ticket_payload):
    created = client.post("/tickets", json=valid_ticket_payload).json()
    client.post(f"/tickets/{created['id']}/auto-classify")

    response = client.put(
        f"/tickets/{created['id']}", json={"category": "other", "priority": "low"}
    )
    body = response.json()
    assert body["category"] == "other"
    assert body["priority"] == "low"
    assert body["classification"]["manually_overridden"] is True


def test_auto_classify_flag_on_create(client, valid_ticket_payload):
    valid_ticket_payload["description"] = "This is a minor cosmetic suggestion for the UI."
    response = client.post("/tickets?auto_classify=true", json=valid_ticket_payload)
    body = response.json()
    assert response.status_code == 201
    assert body["priority"] == "low"
    assert body["classification"] is not None
