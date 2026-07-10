"""Shared helpers used by all three format-specific importers.

Each importer (`csv_importer`, `json_importer`, `xml_importer`) parses its raw
file format into a list of plain dicts. Before those dicts are validated against
`TicketCreate`, they're passed through `normalize_record` so that format quirks
(flat `metadata_*` columns in CSV, tags as a delimited string, empty-string
"nulls") are reconciled into the shape the Pydantic schema expects.
"""

from __future__ import annotations

from typing import Any, Dict

METADATA_FIELDS = ("source", "browser", "device_type")
TAG_DELIMITERS = (";", ",")


def _split_tags(raw: str) -> list:
    for delimiter in TAG_DELIMITERS:
        if delimiter in raw:
            return [t.strip() for t in raw.split(delimiter) if t.strip()]
    return [raw.strip()] if raw.strip() else []


def normalize_record(raw: Dict[str, Any]) -> Dict[str, Any]:
    record: Dict[str, Any] = dict(raw)

    tags = record.get("tags")
    if isinstance(tags, str):
        record["tags"] = _split_tags(tags)
    elif tags is None:
        record["tags"] = []

    metadata = record.get("metadata")
    if not isinstance(metadata, dict):
        flat_metadata: Dict[str, Any] = {}
        for field in METADATA_FIELDS:
            flat_key = f"metadata_{field}"
            value = record.pop(flat_key, None)
            if value not in (None, ""):
                flat_metadata[field] = value
        if flat_metadata:
            record["metadata"] = flat_metadata
        else:
            record.pop("metadata", None)
    else:
        for field in METADATA_FIELDS:
            record.pop(f"metadata_{field}", None)

    for key in ("assigned_to", "category", "priority", "status", "customer_id"):
        if record.get(key) == "":
            record[key] = None

    return record
