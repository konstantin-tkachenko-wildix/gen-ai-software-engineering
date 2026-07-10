"""Thread-safe in-memory repository for tickets.

A simple dict-backed store is enough for this assignment's scope and keeps the
implementation dependency-free. A `threading.Lock` guards every mutation so the
concurrency tests (Task 6) exercise real thread-safety, not just an illusion of it.
"""

from __future__ import annotations

import threading
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from src.models.ticket import Ticket, TicketCategory, TicketPriority, TicketStatus, utcnow


class TicketStore:
    def __init__(self) -> None:
        self._tickets: Dict[UUID, Ticket] = {}
        self._lock = threading.Lock()

    def clear(self) -> None:
        with self._lock:
            self._tickets.clear()

    def create(self, ticket: Ticket) -> Ticket:
        with self._lock:
            self._tickets[ticket.id] = ticket
            return ticket

    def get(self, ticket_id: UUID) -> Optional[Ticket]:
        with self._lock:
            return self._tickets.get(ticket_id)

    def list(
        self,
        *,
        category: Optional[TicketCategory] = None,
        priority: Optional[TicketPriority] = None,
        status: Optional[TicketStatus] = None,
        customer_id: Optional[str] = None,
        assigned_to: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Ticket], int]:
        with self._lock:
            tickets = list(self._tickets.values())

        if category is not None:
            tickets = [t for t in tickets if t.category == category]
        if priority is not None:
            tickets = [t for t in tickets if t.priority == priority]
        if status is not None:
            tickets = [t for t in tickets if t.status == status]
        if customer_id is not None:
            tickets = [t for t in tickets if t.customer_id == customer_id]
        if assigned_to is not None:
            tickets = [t for t in tickets if t.assigned_to == assigned_to]

        tickets.sort(key=lambda t: t.created_at, reverse=True)
        total = len(tickets)

        start = max(page - 1, 0) * page_size
        end = start + page_size
        return tickets[start:end], total

    def update(self, ticket_id: UUID, updated: Ticket) -> Ticket:
        with self._lock:
            updated.updated_at = utcnow()
            self._tickets[ticket_id] = updated
            return updated

    def delete(self, ticket_id: UUID) -> bool:
        with self._lock:
            return self._tickets.pop(ticket_id, None) is not None

    def __len__(self) -> int:
        with self._lock:
            return len(self._tickets)


# Module-level singleton used by the routers; tests reset it via `store.clear()`.
store = TicketStore()
