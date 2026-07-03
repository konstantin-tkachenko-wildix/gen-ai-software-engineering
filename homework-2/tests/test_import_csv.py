"""Tests for the CSV importer: both the parser function directly and the
POST /tickets/import endpoint end-to-end.
"""

import pytest

from src.exceptions import FileParsingError
from src.importers.csv_importer import parse_csv
from tests.conftest import fixture_bytes, fixture_path


def test_parse_csv_valid_records():
    records = parse_csv(fixture_bytes("valid_tickets.csv"))
    assert len(records) == 5
    assert records[0]["customer_id"] == "cust-101"
    assert records[0]["customer_email"] == "alice@example.com"


def test_parse_csv_tags_split_into_list():
    records = parse_csv(fixture_bytes("valid_tickets.csv"))
    assert records[0]["tags"] == ["login", "urgent"]
    assert records[3]["tags"] == []


def test_parse_csv_metadata_columns_combined():
    records = parse_csv(fixture_bytes("valid_tickets.csv"))
    assert records[0]["metadata"] == {
        "source": "web_form",
        "browser": "Chrome",
        "device_type": "desktop",
    }
    # row with only metadata_source populated
    assert records[2]["metadata"] == {"source": "email"}


def test_parse_csv_empty_file_raises():
    with pytest.raises(FileParsingError):
        parse_csv(fixture_bytes("empty.csv"))


def test_parse_csv_invalid_utf8_raises():
    with pytest.raises(FileParsingError):
        parse_csv(b"\xff\xfe\x00invalid-utf8\x80\x81")


def test_import_csv_endpoint_reports_summary(client):
    with fixture_path("valid_tickets.csv").open("rb") as f:
        response = client.post(
            "/tickets/import", files={"file": ("valid_tickets.csv", f, "text/csv")}
        )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 5
    assert body["successful"] == 5
    assert body["failed"] == 0
    assert len(body["created_ids"]) == 5


def test_import_csv_endpoint_partial_failures(client):
    with fixture_path("invalid_tickets.csv").open("rb") as f:
        response = client.post(
            "/tickets/import", files={"file": ("invalid_tickets.csv", f, "text/csv")}
        )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["successful"] == 0
    assert body["failed"] == 3
    assert len(body["errors"]) >= 3
