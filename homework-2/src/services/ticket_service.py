"""Business logic for creating, reading, updating and deleting tickets.

Kept separate from the router so it can be reused by the bulk import service
(Task 1) and the auto-classification endpoint (Task 2) without duplicating logic.
"""

from __future__ import annotations

from typing import List, Optional, Tuple
from uuid import UUID

from src.exceptions import TicketNotFoundError
from src.models.ticket import (
    ClassificationResult,
    Ticket,
    TicketCategory,
    TicketCreate,
    TicketPriority,
    TicketStatus,
    TicketUpdate,
)
from src.storage.ticket_store import store

MANUAL_OVERRIDE_FIELDS = {"category", "priority"}


def build_ticket(data: TicketCreate) -> Ticket:
    """Convert a validated `TicketCreate` payload into a full `Ticket`, applying defaults."""
    payload = data.model_dump()
    payload["category"] = payload.get("category") or TicketCategory.OTHER
    payload["priority"] = payload.get("priority") or TicketPriority.MEDIUM
    return Ticket(**payload)


def create_ticket(data: TicketCreate) -> Ticket:
    ticket = build_ticket(data)
    return store.create(ticket)


def list_tickets(
    *,
    category: Optional[TicketCategory] = None,
    priority: Optional[TicketPriority] = None,
    status: Optional[TicketStatus] = None,
    customer_id: Optional[str] = None,
    assigned_to: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> Tuple[List[Ticket], int]:
    return store.list(
        category=category,
        priority=priority,
        status=status,
        customer_id=customer_id,
        assigned_to=assigned_to,
        page=page,
        page_size=page_size,
    )


def get_ticket_or_404(ticket_id: UUID) -> Ticket:
    ticket = store.get(ticket_id)
    if ticket is None:
        raise TicketNotFoundError(str(ticket_id))
    return ticket


def apply_update(ticket: Ticket, data: TicketUpdate) -> Ticket:
    """Apply a partial update. If the caller explicitly sets `category` and/or
    `priority`, treat it as a manual classification override (Task 2 requirement)
    and record it on the ticket's `classification` field for auditability.
    """
    update_fields = data.model_dump(exclude_unset=True)
    updated = ticket.model_copy(update=update_fields)

    if MANUAL_OVERRIDE_FIELDS & update_fields.keys():
        updated = updated.model_copy(
            update={
                "classification": ClassificationResult(
                    category=updated.category,
                    priority=updated.priority,
                    confidence=1.0,
                    reasoning="Manually overridden via PUT /tickets/{id}.",
                    keywords_found=[],
                    manually_overridden=True,
                )
            }
        )

    return store.update(ticket.id, updated)


def delete_ticket(ticket_id: UUID) -> bool:
    return store.delete(ticket_id)
