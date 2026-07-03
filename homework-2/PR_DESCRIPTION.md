# Homework 2: Intelligent Customer Support System

## Summary

A Python/FastAPI backend plus a vanilla HTML/CSS/JS web front-end for a customer support ticket management system. Agents can create tickets one at a time or bulk-import them from **CSV, JSON, or XML** files; each record is validated independently so one bad row never fails a whole import. A deterministic, rule-based classifier auto-categorizes tickets (`account_access`, `technical_issue`, `billing_question`, `feature_request`, `bug_report`, `other`) and assigns a priority (`urgent`, `high`, `medium`, `low`) with a confidence score, human-readable reasoning, and matched keywords — runnable on creation/import or on demand, with manual overrides tracked separately. Storage is an in-memory, thread-safe ticket store (no DB setup required). The built-in web UI (served by FastAPI itself at `/`, no separate build step) lets agents list/filter tickets, create/edit them with client-side validation, view full details (including classification + metadata), trigger auto-classification, and bulk-import files — all backed by the live REST API.

The upstream `TASKS.md` was updated mid-implementation to add the front-end requirement (originally the assignment was API-only); this was folded into the plan as new phases rather than started over.

The project ships with an **89-test pytest suite at 99.19% statement coverage** (required: >85%).

## Tasks Completed

- ✅ **Task 1: Multi-Format Ticket Import API** — full CRUD (`POST/GET/PUT/DELETE /tickets`, `GET /tickets/{id}`) with filtering (category/priority/status/customer_id/assigned_to) + pagination, and `POST /tickets/import` supporting CSV/JSON/XML with per-record validation and a `{total, successful, failed, errors[]}` summary.
- ✅ **Task 2: Auto-Classification** — `POST /tickets/{id}/auto-classify`, optional `auto_classify` flag on create/import, confidence scoring, reasoning, keyword extraction, manual-override tracking, and an in-memory decision log.
- ✅ **Task 3: AI-Generated Test Suite** — 89 tests (unit, API, integration, performance) at 99.19% coverage, well above the 85% requirement.
- ✅ **Task 4: Multi-Level Documentation** — `README.md`, `API_REFERENCE.md`, `ARCHITECTURE.md`, `TESTING_GUIDE.md` (all with Mermaid diagrams), plus `HOWTORUN.md`.
- ✅ **Task 5: Front-End Application** *(added to TASKS.md mid-project)* — vanilla JS/HTML/CSS SPA in `static/`, served by FastAPI at `/`; ticket list/filter/pagination, create/edit forms with client-side validation, detail view with classification/metadata, auto-classify button, bulk import panel, toast feedback, responsive layout (desktop + mobile).
- ✅ **Task 6: Integration & Performance Tests** *(renumbered from Task 5 by the same upstream update)* — full lifecycle, bulk import + classification verification, 25 concurrent creates, combined filtering, plus 5 timing-based performance benchmarks.

## AI Tools Used — Cursor (Claude, Sonnet 5)

Built end-to-end in Cursor using the **Context-Model-Prompt** framework, planned and implemented phase-by-phase (one phase per `TASKS.md` task):

1. **Planning**: Gave the agent `TASKS.md` + root `README.md` and asked it to plan each task as a phase. It asked clarifying questions up front (framework: FastAPI vs Flask; storage: in-memory vs SQLite) before writing any code — see `docs/screenshots/prompt-2.png`.
2. **Implementation**: Worked through phases (scaffolding → import API → classification → tests → docs → integration/performance → sample data) with the agent proposing code, which I reviewed and asked follow-up questions on (e.g. "what's missing for 100% coverage?" — the agent broke down exactly which lines were realistically testable vs. defensive/unreachable code before I decided which gaps to close).
3. **Mid-project spec change**: When the upstream `TASKS.md` was updated to add a front-end requirement, I asked the agent to diff the old/new spec, verify what changed, and update the plan — it correctly identified the new Task 5 (front-end) and the renumbering of the old Task 5 → Task 6, then asked me to choose the front-end tech stack and serving strategy before touching code (see `docs/screenshots/prompt-3.png`).
4. **Front-end build & verification**: The agent built the vanilla JS SPA, then used a browser automation tool to actually drive the running app (import sample data, open the ticket list, open a ticket detail modal, resize to a mobile viewport) and capture the real screenshots in `docs/screenshots/` — I did not need to take these manually.
5. **Meta**: I also had the agent build the `submit-homework-pr` Cursor/Claude skill used to prepare this very PR (`docs/screenshots/prompt-1.png`).

What I verified myself rather than trusting blindly: ran the full test suite locally after every phase, manually exercised the API via `/docs` (Swagger UI) and `curl`, and clicked through the running UI in a browser to confirm filtering, the detail modal, auto-classify, and bulk import all worked against the real backend (not just what the agent claimed).

## Challenges Encountered & How They Were Addressed

**FastAPI raised `AssertionError: Status code 204 must not have a response body`**
The `DELETE /tickets/{id}` endpoint implicitly tried to serialize a response model for a 204 status. Fixed by adding `response_model=None` to the route decorator.

**Classifier sometimes preferred the wrong category (e.g. `technical_issue` over `bug_report`)**
Simple keyword-count matching gave ties to generic single-word matches over more specific multi-word phrases (e.g. "steps to reproduce"). Fixed with a `_weighted_score()` function that weights keyword matches by word count, so specific phrases outrank generic ones.

**`ModuleNotFoundError: No module named 'src'` depending on invocation directory**
Added an empty `conftest.py` at the `homework-2/` root — pytest automatically adds the directory containing a `conftest.py` to `sys.path`, making `import src...` reliable regardless of cwd.

**Mid-project spec change (front-end requirement added to `TASKS.md`)**
Rather than bolting the front-end on ad hoc, I had the agent diff the upstream change, update the existing plan with two new phases, and ask me to make the two real architectural decisions (plain JS vs. a framework; separate dev server + CORS vs. FastAPI serving static files) before writing code. This kept the addition consistent with the rest of the plan-driven workflow.

**Ensuring the new static file mount didn't break existing API routes**
Starlette resolves routes in registration order, so the catch-all `StaticFiles` mount at `/` had to be registered *after* `app.include_router(tickets_router)` and the `/health` route. Verified explicitly with `tests/test_frontend_static.py`, which asserts `/health` and `/tickets` still resolve correctly alongside the static mount.

**Windows-only setup instructions**
The first draft of `HOWTORUN.md`/`README.md` only had PowerShell commands. Updated both to include matching macOS/Linux (bash/zsh) command blocks for every step (venv setup, running the server/tests, opening the coverage report).

## How to Verify

```bash
cd homework-2
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1   |   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# Run the test suite (89 tests, ~99% coverage, fails if <85%)
python -m pytest

# Start the server
python -m uvicorn src.main:app --reload
# API:      http://127.0.0.1:8000
# Swagger:  http://127.0.0.1:8000/docs
# Web UI:   http://127.0.0.1:8000/

# Try the sample data via the API
curl -X POST "http://127.0.0.1:8000/tickets/import?auto_classify=true" -F "file=@demo/sample_tickets.csv;type=text/csv"
```

Then open `http://127.0.0.1:8000/` to browse/filter the imported tickets, view a ticket's classification, and try bulk import from the UI. Full details in [`homework-2/HOWTORUN.md`](HOWTORUN.md).

## Screenshots

**AI planning & workflow:**

![Framework/storage decisions](https://raw.githubusercontent.com/konstantin-tkachenko-wildix/gen-ai-software-engineering/homework-2-submission/homework-2/docs/screenshots/prompt-2.png)

![Verifying the upstream TASKS.md update](https://raw.githubusercontent.com/konstantin-tkachenko-wildix/gen-ai-software-engineering/homework-2-submission/homework-2/docs/screenshots/prompt-3.png)

**Running application:**

![Ticket list with imported/classified tickets](https://raw.githubusercontent.com/konstantin-tkachenko-wildix/gen-ai-software-engineering/homework-2-submission/homework-2/docs/screenshots/ui.png)

![Ticket detail view with classification result](https://raw.githubusercontent.com/konstantin-tkachenko-wildix/gen-ai-software-engineering/homework-2-submission/homework-2/docs/screenshots/ui-2.png)

**Test coverage:**

![99% test coverage report](https://raw.githubusercontent.com/konstantin-tkachenko-wildix/gen-ai-software-engineering/homework-2-submission/homework-2/docs/screenshots/test_coverage.png)

Also present in `homework-2/docs/screenshots/`:
- `prompt-1.png` — building the `submit-homework-pr` skill used for this PR
- `ui-3.png` — filtered ticket list (priority=High, status=New)

## Key Architecture Decisions

- **FastAPI + Pydantic v2** — free request/response validation for the ticket schema and enums, `TestClient`/`httpx` make API tests trivial, and auto-generated OpenAPI docs double as living API documentation.
- **In-memory, thread-safe store** (`dict` + `threading.Lock`) instead of a database — zero setup, fast tests, no migrations; trade-off is data loss on restart, documented in `ARCHITECTURE.md`. The service layer only depends on the `TicketStore` interface, so swapping in a real DB later is a contained change.
- **Rule-based classification instead of an LLM call** — `TASKS.md` specifies exact keyword rules, so a deterministic matcher is free, fast, fully unit-testable, and has zero network flakiness; multi-word phrases are weighted higher than single words to break category ties correctly.
- **400 instead of FastAPI's default 422** for validation errors, per the assignment's explicit status-code requirements, via a custom `RequestValidationError` handler.
- **Vanilla JS front-end served by FastAPI itself**, rather than a separate React/Vue app with its own dev server — no Node/npm build step, no CORS configuration, the whole project runs from a single `uvicorn` process. The `StaticFiles` mount is registered after the API routes so it only catches paths the router doesn't already own.
