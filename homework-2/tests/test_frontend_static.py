"""Tests for the static front-end mount added in Task 5.

These verify FastAPI serves the vanilla HTML/CSS/JS front-end correctly, and
crucially that the catch-all static mount at "/" does NOT shadow the existing
API routes (/health, /tickets, ...).
"""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_root_serves_index_html(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Support Ticket Manager" in response.text


def test_static_javascript_asset_is_served(client: TestClient) -> None:
    response = client.get("/app.js")
    assert response.status_code == 200
    assert "javascript" in response.headers["content-type"]


def test_static_css_asset_is_served(client: TestClient) -> None:
    response = client.get("/styles.css")
    assert response.status_code == 200
    assert "css" in response.headers["content-type"]


def test_unknown_static_path_returns_404(client: TestClient) -> None:
    response = client.get("/does-not-exist.txt")
    assert response.status_code == 404


def test_health_endpoint_still_resolves_over_static_mount(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_tickets_endpoint_still_resolves_over_static_mount(client: TestClient) -> None:
    response = client.get("/tickets")
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert "total" in body
