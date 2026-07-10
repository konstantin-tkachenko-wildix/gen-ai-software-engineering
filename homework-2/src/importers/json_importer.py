"""JSON import parser.

Accepts either a top-level JSON array of ticket objects, or an object of the
shape `{"tickets": [...]}`.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from src.exceptions import FileParsingError
from src.importers.common import normalize_record


def parse_json(content: bytes) -> List[Dict[str, Any]]:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise FileParsingError(f"JSON file is not valid UTF-8 text: {exc}") from exc

    if not text.strip():
        raise FileParsingError("JSON file is empty")

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise FileParsingError(f"Malformed JSON file: {exc}") from exc

    if isinstance(data, dict) and "tickets" in data:
        data = data["tickets"]

    if not isinstance(data, list):
        raise FileParsingError(
            "JSON file must contain either a list of tickets or an object with a 'tickets' array"
        )

    records: List[Dict[str, Any]] = []
    for item in data:
        if not isinstance(item, dict):
            raise FileParsingError("Each ticket entry in the JSON file must be an object")
        records.append(normalize_record(item))
    return records
