"""End-to-end integration tests exercising multiple components together:
full ticket lifecycles, bulk import + classification, concurrency, and
combined filtering (Task 6).
"""

from concurrent.futures import ThreadPoolExecutor

from tests.conftest import fixture_path


def test_full_ticket_lifecycle(client):
    """create -> auto-classify -> update (assign + progress) -> resolve -> delete."""
    payload = {
        "customer_id": "cust-lifecycle",
        "customer_email": "lifecycle@example.com",
        "customer_name": "Lifecycle Tester",
        "subject": "Can't access my account, this is critical",
        "description": "I am locked out after resetting my password and need urgent help.",
    }
    created = client.post("/tickets", json=payload).json()
    assert created["status"] == "new"
    assert created["category"] == "other"  # not yet classified

    classified = client.post(f"/tickets/{created['id']}/auto-classify").json()
    assert classified["category"] == "account_access"
    assert classified["priority"] == "urgent"

    in_progress = client.put(
        f"/tickets/{created['id']}", json={"status": "in_progress", "assigned_to": "agent-42"}
    ).json()
    assert in_progress["status"] == "in_progress"
    assert in_progress["assigned_to"] == "agent-42"

    resolved = client.put(
        f"/tickets/{created['id']}",
        json={"status": "resolved", "resolved_at": "2026-01-01T00:00:00Z"},
    ).json()
    assert resolved["status"] == "resolved"
    assert resolved["resolved_at"] is not None

    delete_response = client.delete(f"/tickets/{created['id']}")
    assert delete_response.status_code == 204
    assert client.get(f"/tickets/{created['id']}").status_code == 404


def test_bulk_import_with_auto_classification_verification(client):
    """Bulk-import a CSV file with auto_classify=true and verify every created
    ticket actually received a non-default classification result."""
    with fixture_path("valid_tickets.csv").open("rb") as f:
        response = client.post(
            "/tickets/import?auto_classify=true",
            files={"file": ("valid_tickets.csv", f, "text/csv")},
        )
    assert response.status_code == 200
    summary = response.json()
    assert summary["successful"] == 5

    for ticket_id in summary["created_ids"]:
        ticket = client.get(f"/tickets/{ticket_id}").json()
        assert ticket["classification"] is not None
        assert 0.0 <= ticket["classification"]["confidence"] <= 1.0
        assert ticket["classification"]["manually_overridden"] is False


def test_concurrent_ticket_creation(client):
    """20+ simultaneous ticket creation requests should all succeed with unique
    IDs and the in-memory store should end up with exactly that many tickets."""
    request_count = 25

    def _create(index: int):
        payload = {
            "customer_id": f"cust-concurrent-{index}",
            "customer_email": f"concurrent{index}@example.com",
            "customer_name": f"Concurrent User {index}",
            "subject": f"Concurrent request number {index}",
            "description": "Testing that concurrent ticket creation is thread-safe end to end.",
        }
        return client.post("/tickets", json=payload)

    with ThreadPoolExecutor(max_workers=10) as executor:
        responses = list(executor.map(_create, range(request_count)))

    assert all(r.status_code == 201 for r in responses)
    ids = {r.json()["id"] for r in responses}
    assert len(ids) == request_count

    listing = client.get("/tickets", params={"page_size": 200}).json()
    assert listing["total"] == request_count


def test_combined_category_and_priority_filtering(client):
    def _create(**overrides):
        payload = {
            "customer_id": "cust-filter",
            "customer_email": "filter@example.com",
            "customer_name": "Filter Tester",
            "subject": "Filter test ticket",
            "description": "This ticket exists purely to exercise combined filtering.",
        }
        payload.update(overrides)
        return client.post("/tickets", json=payload)

    _create(category="billing_question", priority="high")
    _create(category="billing_question", priority="low")
    _create(category="bug_report", priority="high")

    response = client.get(
        "/tickets", params={"category": "billing_question", "priority": "high"}
    )
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["category"] == "billing_question"
    assert body["items"][0]["priority"] == "high"


def test_bulk_import_then_filter_and_delete_workflow(client):
    """Combined workflow: import a batch, filter down to a subset, then delete
    every ticket in that subset and confirm the store reflects the deletions."""
    with fixture_path("valid_tickets.csv").open("rb") as f:
        summary = client.post(
            "/tickets/import", files={"file": ("valid_tickets.csv", f, "text/csv")}
        ).json()
    assert summary["successful"] == 5

    filtered = client.get("/tickets", params={"category": "billing_question"}).json()
    assert filtered["total"] == 1

    for ticket in filtered["items"]:
        assert client.delete(f"/tickets/{ticket['id']}").status_code == 204

    remaining = client.get("/tickets", params={"page_size": 200}).json()
    assert remaining["total"] == 4
    assert all(t["category"] != "billing_question" for t in remaining["items"])
