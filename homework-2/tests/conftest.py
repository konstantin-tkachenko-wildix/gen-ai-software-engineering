"""Shared pytest fixtures for the whole test suite."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.services import classification_service
from src.storage.ticket_store import store

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def _reset_state():
    """Ensure every test starts with an empty ticket store and classification log."""
    store.clear()
    classification_service.reset_log()
    yield
    store.clear()
    classification_service.reset_log()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def valid_ticket_payload() -> dict:
    return {
        "customer_id": "cust-001",
        "customer_email": "customer@example.com",
        "customer_name": "Test Customer",
        "subject": "Cannot log in to my account",
        "description": "I am unable to log in even after resetting my password twice.",
        "metadata": {"source": "web_form", "browser": "Chrome", "device_type": "desktop"},
    }


def fixture_path(name: str) -> Path:
    return FIXTURES_DIR / name


def fixture_bytes(name: str) -> bytes:
    return fixture_path(name).read_bytes()
