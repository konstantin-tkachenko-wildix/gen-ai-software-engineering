"""XML import parser.

Expected shape:

```xml
<tickets>
  <ticket>
    <customer_id>...</customer_id>
    ...
    <tags><tag>urgent</tag><tag>login</tag></tags>
    <metadata>
      <source>web_form</source>
      <browser>Chrome</browser>
      <device_type>desktop</device_type>
    </metadata>
  </ticket>
</tickets>
```
"""

from __future__ import annotations

from typing import Any, Dict, List
from xml.parsers.expat import ExpatError

import xmltodict

from src.exceptions import FileParsingError
from src.importers.common import normalize_record


def _flatten_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    flat: Dict[str, Any] = {}
    for key, value in entry.items():
        if key.startswith("@"):
            continue
        if key == "tags":
            if isinstance(value, dict) and "tag" in value:
                tag_value = value["tag"]
                flat["tags"] = tag_value if isinstance(tag_value, list) else [tag_value]
            elif isinstance(value, str):
                flat["tags"] = value
            else:
                flat["tags"] = []
        elif key == "metadata" and isinstance(value, dict):
            flat["metadata"] = {k: v for k, v in value.items() if not k.startswith("@")}
        elif isinstance(value, dict):
            # xmltodict wraps mixed-content/attributed elements as {"#text": "..."}
            flat[key] = value.get("#text", "")
        elif value is None:
            flat[key] = ""
        else:
            flat[key] = value
    return flat


def parse_xml(content: bytes) -> List[Dict[str, Any]]:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise FileParsingError(f"XML file is not valid UTF-8 text: {exc}") from exc

    if not text.strip():
        raise FileParsingError("XML file is empty")

    try:
        data = xmltodict.parse(text)
    except ExpatError as exc:
        raise FileParsingError(f"Malformed XML file: {exc}") from exc

    if not isinstance(data, dict) or len(data) != 1:
        raise FileParsingError("XML file must have a single root element")

    root = next(iter(data.values()))
    if not isinstance(root, dict) or "ticket" not in root:
        raise FileParsingError("XML file must contain <ticket> elements under its root element")

    ticket_entries = root["ticket"]
    if isinstance(ticket_entries, dict):
        ticket_entries = [ticket_entries]
    if not isinstance(ticket_entries, list):
        raise FileParsingError("Malformed <ticket> entries in XML file")

    records: List[Dict[str, Any]] = []
    for entry in ticket_entries:
        if not isinstance(entry, dict):
            raise FileParsingError("Each <ticket> element must contain ticket fields")
        records.append(normalize_record(_flatten_entry(entry)))
    return records
