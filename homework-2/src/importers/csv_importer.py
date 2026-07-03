"""CSV import parser.

Expected columns (header row required):
customer_id, customer_email, customer_name, subject, description,
category, priority, status, tags, assigned_to,
metadata_source, metadata_browser, metadata_device_type

`tags` may be a `;` or `,` separated string. Unknown/missing columns are left
for Pydantic to reject as validation errors on a per-record basis.
"""

from __future__ import annotations

import csv
import io
from typing import Any, Dict, List

from src.exceptions import FileParsingError
from src.importers.common import normalize_record


def parse_csv(content: bytes) -> List[Dict[str, Any]]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise FileParsingError(f"CSV file is not valid UTF-8 text: {exc}") from exc

    if not text.strip():
        raise FileParsingError("CSV file is empty")

    try:
        reader = csv.DictReader(io.StringIO(text))
        if reader.fieldnames is None:
            raise FileParsingError("CSV file has no header row")
        rows = list(reader)
    except csv.Error as exc:
        raise FileParsingError(f"Malformed CSV file: {exc}") from exc

    records: List[Dict[str, Any]] = []
    for raw_row in rows:
        raw_row.pop(None, None)  # drop any ragged extra columns csv puts under None
        records.append(normalize_record(raw_row))
    return records
