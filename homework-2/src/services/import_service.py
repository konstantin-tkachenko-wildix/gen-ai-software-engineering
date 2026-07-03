"""Bulk import orchestration: detect format, parse, validate each record, and
persist the valid ones — without ever failing the whole request just because
one record in the file is bad.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from src.exceptions import FileParsingError, UnsupportedImportFormatError
from src.importers.csv_importer import parse_csv
from src.importers.json_importer import parse_json
from src.importers.xml_importer import parse_xml
from src.models.ticket import TicketCreate
from src.services import classification_service
from src.services.ticket_service import build_ticket
from src.storage.ticket_store import store

PARSERS = {
    "csv": parse_csv,
    "json": parse_json,
    "xml": parse_xml,
}

CONTENT_TYPE_HINTS = {
    "csv": "csv",
    "json": "json",
    "xml": "xml",
}


def detect_format(filename: Optional[str], content_type: Optional[str]) -> str:
    if filename and "." in filename:
        ext = filename.rsplit(".", 1)[-1].lower()
        if ext in PARSERS:
            return ext

    if content_type:
        lowered = content_type.lower()
        for hint, fmt in CONTENT_TYPE_HINTS.items():
            if hint in lowered:
                return fmt

    raise UnsupportedImportFormatError(filename or "uploaded file")


def import_tickets(
    content: bytes,
    filename: Optional[str],
    content_type: Optional[str],
    *,
    auto_classify: bool = False,
) -> Dict[str, Any]:
    """Parse and import a ticket file. Raises FileParsingError/UnsupportedImportFormatError
    only when the *whole file* can't be processed; per-record problems are returned
    in the summary's `errors` list instead of raising.

    When `auto_classify` is set, every successfully created ticket is immediately
    run through the rule-based classifier (Task 2), mirroring the optional
    auto-classify flag on `POST /tickets`.
    """
    fmt = detect_format(filename, content_type)
    records = PARSERS[fmt](content)

    errors: List[Dict[str, Any]] = []
    created_ids: List[str] = []

    for index, raw_record in enumerate(records):
        try:
            ticket_create = TicketCreate(**raw_record)
        except ValidationError as exc:
            for err in exc.errors():
                field = ".".join(str(part) for part in err["loc"]) or None
                errors.append({"index": index, "field": field, "message": err["msg"]})
            continue

        ticket = build_ticket(ticket_create)
        ticket = store.create(ticket)
        if auto_classify:
            ticket = classification_service.classify_and_apply(ticket)
        created_ids.append(str(ticket.id))

    total = len(records)
    return {
        "total": total,
        "successful": len(created_ids),
        "failed": total - len(created_ids),
        "errors": errors,
        "created_ids": created_ids,
    }
