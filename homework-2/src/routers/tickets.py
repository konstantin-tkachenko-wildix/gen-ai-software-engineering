"""HTTP layer for the /tickets resource. Kept thin: request/response wiring only,
business logic lives in `src.services`.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, File, Query, UploadFile, status
from fastapi.responses import JSONResponse

from src.exceptions import FileParsingError, UnsupportedImportFormatError
from src.models.ticket import (
    Ticket,
    TicketCategory,
    TicketCreate,
    TicketPriority,
    TicketStatus,
    TicketUpdate,
)
from src.services import classification_service, import_service, ticket_service

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=Ticket, status_code=status.HTTP_201_CREATED)
def create_ticket(
    payload: TicketCreate,
    auto_classify: bool = Query(
        default=False, description="Run auto-classification immediately after creation"
    ),
) -> Ticket:
    ticket = ticket_service.create_ticket(payload)
    if auto_classify:
        ticket = classification_service.classify_and_apply(ticket)
    return ticket


@router.post("/import")
async def import_tickets(
    file: UploadFile = File(...),
    auto_classify: bool = Query(
        default=False, description="Auto-classify every successfully imported ticket"
    ),
) -> JSONResponse:
    content = await file.read()
    try:
        summary = import_service.import_tickets(
            content, file.filename, file.content_type, auto_classify=auto_classify
        )
    except (UnsupportedImportFormatError, FileParsingError) as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": str(exc)},
        )
    return JSONResponse(status_code=status.HTTP_200_OK, content=summary)


@router.get("")
def list_tickets(
    category: Optional[TicketCategory] = None,
    priority: Optional[TicketPriority] = None,
    status_filter: Optional[TicketStatus] = Query(default=None, alias="status"),
    customer_id: Optional[str] = None,
    assigned_to: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
) -> dict:
    items, total = ticket_service.list_tickets(
        category=category,
        priority=priority,
        status=status_filter,
        customer_id=customer_id,
        assigned_to=assigned_to,
        page=page,
        page_size=page_size,
    )
    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.get("/{ticket_id}", response_model=Ticket)
def get_ticket(ticket_id: UUID) -> Ticket:
    return ticket_service.get_ticket_or_404(ticket_id)


@router.post("/{ticket_id}/auto-classify", response_model=Ticket)
def auto_classify_ticket(ticket_id: UUID) -> Ticket:
    ticket = ticket_service.get_ticket_or_404(ticket_id)
    return classification_service.classify_and_apply(ticket)


@router.put("/{ticket_id}", response_model=Ticket)
def update_ticket(ticket_id: UUID, payload: TicketUpdate) -> Ticket:
    ticket = ticket_service.get_ticket_or_404(ticket_id)
    return ticket_service.apply_update(ticket, payload)


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_ticket(ticket_id: UUID) -> None:
    ticket_service.get_ticket_or_404(ticket_id)
    ticket_service.delete_ticket(ticket_id)
