"""Tests for the JSON importer: parser function and the import endpoint."""

import pytest

from src.exceptions import FileParsingError
from src.importers.json_importer import parse_json
from tests.conftest import fixture_bytes, fixture_path


def test_parse_json_object_with_tickets_key():
    records = parse_json(fixture_bytes("valid_tickets.json"))
    assert len(records) == 2
    assert records[0]["customer_id"] == "cust-301"
    assert records[0]["metadata"]["browser"] == "Edge"


def test_parse_json_array_format():
    records = parse_json(b'[{"customer_id": "x", "customer_email": "a@b.com"}]')
    assert len(records) == 1
    assert records[0]["customer_id"] == "x"


def test_parse_json_malformed_raises():
    with pytest.raises(FileParsingError):
        parse_json(fixture_bytes("malformed.json"))


def test_parse_json_invalid_utf8_raises():
    with pytest.raises(FileParsingError):
        parse_json(b"\xff\xfe\x00invalid-utf8\x80\x81")


def test_parse_json_empty_file_raises():
    with pytest.raises(FileParsingError):
        parse_json(fixture_bytes("empty.json"))


def test_parse_json_non_list_non_tickets_object_raises():
    with pytest.raises(FileParsingError):
        parse_json(b'{"foo": "bar"}')


def test_parse_json_array_with_non_object_item_raises():
    with pytest.raises(FileParsingError):
        parse_json(b'["oops"]')


def test_import_json_endpoint_reports_summary(client):
    with fixture_path("valid_tickets.json").open("rb") as f:
        response = client.post(
            "/tickets/import", files={"file": ("valid_tickets.json", f, "application/json")}
        )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["successful"] == 2
    assert body["failed"] == 0


def test_import_json_endpoint_partial_failures(client):
    with fixture_path("invalid_tickets.json").open("rb") as f:
        response = client.post(
            "/tickets/import", files={"file": ("invalid_tickets.json", f, "application/json")}
        )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["successful"] == 0
    assert body["failed"] == 2
