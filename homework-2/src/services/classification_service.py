"""Applies auto-classification results to a ticket and keeps an in-memory
audit log of every classification decision (Task 2: "Log all decisions").
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from uuid import UUID

from src.classification.classifier import classify_ticket
from src.models.ticket import ClassificationResult, Ticket, utcnow
from src.storage.ticket_store import store


@dataclass
class ClassificationLogEntry:
    ticket_id: UUID
    result: ClassificationResult
    timestamp: datetime = field(default_factory=utcnow)


classification_log: List[ClassificationLogEntry] = []


def classify_and_apply(ticket: Ticket) -> Ticket:
    """Run the rule-based classifier against a ticket, persist the result, and log it."""
    outcome = classify_ticket(ticket.subject, ticket.description)

    classification = ClassificationResult(
        category=outcome.category,
        priority=outcome.priority,
        confidence=outcome.confidence,
        reasoning=outcome.reasoning,
        keywords_found=outcome.keywords_found,
        manually_overridden=False,
    )

    updated = ticket.model_copy(
        update={
            "category": outcome.category,
            "priority": outcome.priority,
            "classification": classification,
        }
    )
    saved = store.update(ticket.id, updated)

    classification_log.append(ClassificationLogEntry(ticket_id=ticket.id, result=classification))
    return saved


def reset_log() -> None:
    classification_log.clear()
