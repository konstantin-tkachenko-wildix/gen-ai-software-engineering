"""Tests for the XML importer: parser function and the import endpoint."""

import pytest

from src.exceptions import FileParsingError
from src.importers.xml_importer import parse_xml
from tests.conftest import fixture_bytes, fixture_path


def test_parse_xml_valid_records():
    records = parse_xml(fixture_bytes("valid_tickets.xml"))
    assert len(records) == 2
    assert records[0]["customer_id"] == "cust-501"
    assert records[0]["metadata"] == {"source": "email"}


def test_parse_xml_multiple_tags_parsed_as_list():
    records = parse_xml(fixture_bytes("valid_tickets.xml"))
    assert records[1]["tags"] == ["bug", "urgent"]
    assert records[0]["tags"] == ["billing"]


def test_parse_xml_malformed_raises():
    with pytest.raises(FileParsingError):
        parse_xml(fixture_bytes("malformed.xml"))


def test_parse_xml_invalid_utf8_raises():
    with pytest.raises(FileParsingError):
        parse_xml(b"\xff\xfe\x00invalid-utf8\x80\x81")


def test_parse_xml_empty_file_raises():
    with pytest.raises(FileParsingError):
        parse_xml(fixture_bytes("empty.xml"))


def test_parse_xml_flatten_edge_cases():
    records = parse_xml(fixture_bytes("xml_flatten_edge_cases.xml"))
    assert len(records) == 2

    first, second = records
    # <ticket id="1"> attribute is skipped; <customer_name lang="en">Alice</customer_name>
    # (mixed content with an attribute) resolves to its text; <tags>billing;urgent</tags>
    # as a plain string is split into a list; <assigned_to/> (self-closing/None) becomes None.
    assert first["customer_name"] == "Alice"
    assert first["tags"] == ["billing", "urgent"]
    assert first["assigned_to"] is None

    # <tags/> (empty self-closing element) becomes an empty list.
    assert second["tags"] == []


def test_parse_xml_missing_ticket_element_raises():
    with pytest.raises(FileParsingError):
        parse_xml(fixture_bytes("xml_no_ticket_element.xml"))


def test_parse_xml_ticket_content_as_plain_text_raises():
    with pytest.raises(FileParsingError):
        parse_xml(fixture_bytes("xml_ticket_as_text.xml"))


def test_parse_xml_entries_not_dict_raises():
    with pytest.raises(FileParsingError):
        parse_xml(fixture_bytes("xml_entries_not_dict.xml"))


def test_import_xml_endpoint_reports_summary(client):
    with fixture_path("valid_tickets.xml").open("rb") as f:
        response = client.post(
            "/tickets/import", files={"file": ("valid_tickets.xml", f, "application/xml")}
        )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["successful"] == 2
    assert body["failed"] == 0


def test_import_xml_endpoint_partial_failures(client):
    with fixture_path("invalid_tickets.xml").open("rb") as f:
        response = client.post(
            "/tickets/import", files={"file": ("invalid_tickets.xml", f, "application/xml")}
        )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["successful"] == 0
    assert body["failed"] == 1
