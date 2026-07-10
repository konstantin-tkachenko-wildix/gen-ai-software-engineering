"""End-to-end tests for the /tickets CRUD endpoints via FastAPI's TestClient."""

from src.storage.ticket_store import store


def _create(client, **overrides):
    payload = {
        "customer_id": "cust-1",
        "customer_email": "person@example.com",
        "customer_name": "Person One",
        "subject": "A valid subject line",
        "description": "This description is definitely long enough to be valid.",
    }
    payload.update(overrides)
    return client.post("/tickets", json=payload)


def test_create_ticket_success(client, valid_ticket_payload):
    response = client.post("/tickets", json=valid_ticket_payload)
    assert response.status_code == 201
    body = response.json()
    assert body["customer_email"] == valid_ticket_payload["customer_email"]
    assert body["status"] == "new"
    assert body["category"] == "other"
    assert body["priority"] == "medium"
    assert "id" in body


def test_create_ticket_validation_error_returns_400(client, valid_ticket_payload):
    valid_ticket_payload["customer_email"] = "not-an-email"
    response = client.post("/tickets", json=valid_ticket_payload)
    assert response.status_code == 400
    assert "details" in response.json()


def test_get_ticket_success(client, valid_ticket_payload):
    created = client.post("/tickets", json=valid_ticket_payload).json()
    response = client.get(f"/tickets/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_nonexistent_ticket_returns_404(client):
    response = client.get("/tickets/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert "error" in response.json()


def test_list_tickets_empty(client):
    response = client.get("/tickets")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 0
    assert body["items"] == []


def test_list_tickets_after_creation(client, valid_ticket_payload):
    _create(client)
    _create(client, customer_id="cust-2", customer_email="other@example.com")
    response = client.get("/tickets")
    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_list_tickets_filter_by_category(client):
    _create(client, category="billing_question")
    _create(client, customer_id="cust-2", customer_email="other@example.com", category="bug_report")
    response = client.get("/tickets", params={"category": "billing_question"})
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["category"] == "billing_question"


def test_list_tickets_filter_by_status(client):
    _create(client, status="resolved")
    _create(client, customer_id="cust-2", customer_email="other@example.com")
    response = client.get("/tickets", params={"status": "resolved"})
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["status"] == "resolved"


def test_update_ticket_success(client, valid_ticket_payload):
    created = client.post("/tickets", json=valid_ticket_payload).json()
    response = client.put(
        f"/tickets/{created['id']}", json={"status": "in_progress", "assigned_to": "agent-1"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "in_progress"
    assert body["assigned_to"] == "agent-1"


def test_update_nonexistent_ticket_returns_404(client):
    response = client.put(
        "/tickets/00000000-0000-0000-0000-000000000000", json={"status": "closed"}
    )
    assert response.status_code == 404


def test_delete_ticket_success_then_get_returns_404(client, valid_ticket_payload):
    created = client.post("/tickets", json=valid_ticket_payload).json()
    delete_response = client.delete(f"/tickets/{created['id']}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/tickets/{created['id']}")
    assert get_response.status_code == 404


def test_health_check_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_tickets_filter_by_priority(client):
    _create(client, priority="urgent")
    _create(client, customer_id="cust-2", customer_email="other@example.com", priority="low")
    response = client.get("/tickets", params={"priority": "urgent"})
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["priority"] == "urgent"


def test_list_tickets_filter_by_customer_id(client):
    _create(client, customer_id="cust-alpha")
    _create(client, customer_id="cust-beta", customer_email="other@example.com")
    response = client.get("/tickets", params={"customer_id": "cust-alpha"})
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["customer_id"] == "cust-alpha"


def test_list_tickets_filter_by_assigned_to(client):
    created = _create(client).json()
    client.put(f"/tickets/{created['id']}", json={"assigned_to": "agent-9"})
    _create(client, customer_id="cust-2", customer_email="other@example.com")

    response = client.get("/tickets", params={"assigned_to": "agent-9"})
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["assigned_to"] == "agent-9"


def test_ticket_store_len_matches_created_count(client):
    assert len(store) == 0
    _create(client)
    _create(client, customer_id="cust-2", customer_email="other@example.com")
    assert len(store) == 2
