"""Timing-based performance benchmarks (Task 6).

Thresholds are intentionally generous — the goal is to catch gross regressions
(e.g. an accidental O(n^2) loop) on an in-memory store, not to be a strict
micro-benchmark suite. Results printed here (run with `-s`) feed the benchmark
table in TESTING_GUIDE.md.
"""

import time
from concurrent.futures import ThreadPoolExecutor
from statistics import mean

from src.classification.classifier import classify_ticket

TICKET_PAYLOAD = {
    "customer_id": "cust-perf",
    "customer_email": "perf@example.com",
    "customer_name": "Perf Tester",
    "subject": "Performance test ticket",
    "description": "This ticket exists purely to exercise timing-based performance tests.",
}


def _payload(index: int) -> dict:
    payload = dict(TICKET_PAYLOAD)
    payload["customer_id"] = f"cust-perf-{index}"
    payload["customer_email"] = f"perf{index}@example.com"
    return payload


def test_single_ticket_creation_performance(client):
    iterations = 100
    durations = []

    for i in range(iterations):
        start = time.perf_counter()
        response = client.post("/tickets", json=_payload(i))
        durations.append(time.perf_counter() - start)
        assert response.status_code == 201

    avg_ms = mean(durations) * 1000
    print(f"\n[perf] avg single ticket creation: {avg_ms:.3f} ms over {iterations} requests")
    assert avg_ms < 50, f"Ticket creation too slow: {avg_ms:.3f} ms average"


def test_list_1000_tickets_performance(client):
    total_tickets = 1000
    for i in range(total_tickets):
        client.post("/tickets", json=_payload(i))

    start = time.perf_counter()
    response = client.get("/tickets", params={"page_size": 200})
    duration_ms = (time.perf_counter() - start) * 1000

    assert response.status_code == 200
    assert response.json()["total"] == total_tickets
    print(f"\n[perf] GET /tickets with {total_tickets} tickets in store: {duration_ms:.3f} ms")
    assert duration_ms < 500, f"Listing tickets too slow: {duration_ms:.3f} ms"


def test_bulk_import_throughput(client):
    row_count = 200
    header = "customer_id,customer_email,customer_name,subject,description\n"
    rows = "\n".join(
        f"cust-bulk-{i},bulk{i}@example.com,Bulk User {i},Bulk import test subject {i},"
        f"This is a sufficiently long description for bulk import performance testing."
        for i in range(row_count)
    )
    csv_content = header + rows + "\n"

    start = time.perf_counter()
    response = client.post(
        "/tickets/import", files={"file": ("bulk.csv", csv_content, "text/csv")}
    )
    duration = time.perf_counter() - start

    assert response.status_code == 200
    body = response.json()
    assert body["successful"] == row_count

    throughput = row_count / duration if duration > 0 else float("inf")
    print(
        f"\n[perf] bulk import of {row_count} tickets: {duration * 1000:.3f} ms "
        f"({throughput:.0f} tickets/sec)"
    )
    assert duration < 2.0, f"Bulk import too slow: {duration:.3f} s for {row_count} tickets"


def test_classification_latency():
    iterations = 1000
    start = time.perf_counter()
    for _ in range(iterations):
        classify_ticket(
            "Can't log in, this is critical",
            "I reset my password but still cannot access my account, please help urgently.",
        )
    duration = time.perf_counter() - start

    avg_us = (duration / iterations) * 1_000_000
    print(f"\n[perf] avg classify_ticket() latency: {avg_us:.1f} microseconds over {iterations} calls")
    assert avg_us < 1000, f"Classification too slow: {avg_us:.1f} microseconds average"


def test_concurrent_throughput(client):
    request_count = 50

    def _create(index: int):
        return client.post("/tickets", json=_payload(index))

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=10) as executor:
        responses = list(executor.map(_create, range(request_count)))
    duration = time.perf_counter() - start

    assert all(r.status_code == 201 for r in responses)
    throughput = request_count / duration if duration > 0 else float("inf")
    print(
        f"\n[perf] {request_count} concurrent creations (10 workers): {duration * 1000:.3f} ms "
        f"({throughput:.0f} req/sec)"
    )
    assert duration < 5.0, f"Concurrent creation too slow: {duration:.3f} s for {request_count} requests"
