"""Tests for format detection and the /tickets/import endpoint's file-level
error handling (unsupported format, malformed whole file) — as opposed to the
per-format parser tests in test_import_csv/json/xml.py.
"""

import pytest

from src.exceptions import UnsupportedImportFormatError
from src.services.import_service import detect_format


def test_detect_format_by_extension():
    assert detect_format("tickets.csv", None) == "csv"
    assert detect_format("tickets.JSON", None) == "json"
    assert detect_format("tickets.xml", None) == "xml"


def test_detect_format_by_content_type_when_extension_missing():
    assert detect_format(None, "text/csv") == "csv"
    assert detect_format("tickets", "application/json; charset=utf-8") == "json"
    assert detect_format(None, "application/xml") == "xml"


def test_detect_format_unsupported_raises():
    with pytest.raises(UnsupportedImportFormatError):
        detect_format("notes.txt", "text/plain")


def test_import_endpoint_rejects_unsupported_file_type(client):
    response = client.post(
        "/tickets/import", files={"file": ("notes.txt", b"hello world", "text/plain")}
    )
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["error"]


def test_import_endpoint_rejects_malformed_whole_file(client):
    response = client.post(
        "/tickets/import",
        files={"file": ("tickets.json", b"{not valid json", "application/json")},
    )
    assert response.status_code == 400
    assert "error" in response.json()
