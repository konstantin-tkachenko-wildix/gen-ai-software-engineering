# Homework 2: Intelligent Customer Support System

## 📋 Summary

Python/FastAPI backend + vanilla HTML/CSS/JS front-end for a customer support ticket system. Tickets can be created individually or bulk-imported from **CSV/JSON/XML** (per-record validation, one bad row never fails the batch). A deterministic rule-based classifier auto-assigns category/priority with confidence, reasoning, and matched keywords, runnable on create/import or on demand, with manual-override tracking. Storage is an in-memory, thread-safe store. The built-in web UI (served by FastAPI at `/`, no build step) covers listing/filtering, create/edit forms, ticket detail + classification view, auto-classify, and bulk import.

`TASKS.md` was updated mid-implementation to add the front-end requirement — this was folded into the existing plan as new phases rather than restarted.

**89 tests, 99.19% coverage** (required: >85%).

## ✅ Tasks Completed

- ✅ **Task 1: Multi-Format Ticket Import API** — full CRUD + filtering/pagination, CSV/JSON/XML import with per-record errors summary
- ✅ **Task 2: Auto-Classification** — confidence/reasoning/keywords, manual override tracking, decision log
- ✅ **Task 3: AI-Generated Test Suite** — 89 tests, 99.19% coverage
- ✅ **Task 4: Multi-Level Documentation** — README, API_REFERENCE, ARCHITECTURE, TESTING_GUIDE, HOWTORUN (Mermaid diagrams)
- ✅ **Task 5: Front-End Application** *(added mid-project)* — vanilla JS SPA, responsive, backed live by the API
- ✅ **Task 6: Integration & Performance Tests** *(renumbered from Task 5)* — lifecycle, concurrency, filtering, timing benchmarks

## 🤖 AI Tools Used — Cursor (Claude, Sonnet 5)

Planned and built phase-by-phase (Context-Model-Prompt framework), one phase per `TASKS.md` task:

- **Planning**: agent asked clarifying questions (FastAPI vs Flask, in-memory vs SQLite) before writing code (`prompt-2.png`)
- **Coverage gaps**: asked "what's missing for 100%?" — agent distinguished realistically-testable gaps from unreachable defensive code before closing the ones worth closing
- **Mid-project spec change**: when `TASKS.md` added the front-end requirement, had the agent diff the change, update the plan, and ask me to pick the tech stack/serving strategy before coding (`prompt-3.png`)
- **Front-end verification**: agent drove the running app via browser automation (import data, open modals, resize to mobile) to capture real screenshots itself
- Verified myself: ran the full suite after every phase, exercised the API via Swagger/curl, clicked through the live UI

## ⚠️ Challenges Encountered & How They Were Addressed

**FastAPI `AssertionError` on 204 responses** — `DELETE` implicitly tried to serialize a body; fixed with `response_model=None`.

**Classifier picked the wrong category on ties** (e.g. `technical_issue` over `bug_report`) — added weighted scoring so multi-word keyword phrases outrank generic single words.

**`ModuleNotFoundError: No module named 'src'`** — added an empty root `conftest.py` so pytest adds `homework-2/` to `sys.path` regardless of invocation cwd.

**Static file mount shadowing API routes** — Starlette resolves routes in registration order, so `StaticFiles` is mounted at `/` *after* the API router; verified with a dedicated test.

**Windows-only run instructions** — `HOWTORUN.md`/`README.md` originally had PowerShell-only commands; added matching macOS/Linux equivalents for every step.

## ▶️ How to Verify

```bash
cd homework-2
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1   |   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

python -m pytest                       # 89 tests, ~99% coverage
python -m uvicorn src.main:app --reload
# API: http://127.0.0.1:8000  Swagger: /docs  Web UI: /

curl -X POST "http://127.0.0.1:8000/tickets/import?auto_classify=true" -F "file=@demo/sample_tickets.csv;type=text/csv"
```

Open `http://127.0.0.1:8000/` to browse/filter tickets, view classification, and try bulk import from the UI. Full details in [`homework-2/HOWTORUN.md`](HOWTORUN.md).

## 📸 Screenshots

**AI workflow:**

![Framework/storage decisions](https://raw.githubusercontent.com/konstantin-tkachenko-wildix/gen-ai-software-engineering/homework-2-submission/homework-2/docs/screenshots/prompt-2.png)

![Verifying the upstream TASKS.md spec change](https://raw.githubusercontent.com/konstantin-tkachenko-wildix/gen-ai-software-engineering/homework-2-submission/homework-2/docs/screenshots/prompt-3.png)

![Building the submit-homework-pr skill used for this PR](https://raw.githubusercontent.com/konstantin-tkachenko-wildix/gen-ai-software-engineering/homework-2-submission/homework-2/docs/screenshots/prompt-1.png)

**Running application:**

![Ticket list with imported/classified tickets](https://raw.githubusercontent.com/konstantin-tkachenko-wildix/gen-ai-software-engineering/homework-2-submission/homework-2/docs/screenshots/ui.png)

![Ticket detail view with classification result](https://raw.githubusercontent.com/konstantin-tkachenko-wildix/gen-ai-software-engineering/homework-2-submission/homework-2/docs/screenshots/ui-2.png)

![Filtered ticket list (priority=High, status=New)](https://raw.githubusercontent.com/konstantin-tkachenko-wildix/gen-ai-software-engineering/homework-2-submission/homework-2/docs/screenshots/ui-3.png)

**Test coverage:**

![99% test coverage report](https://raw.githubusercontent.com/konstantin-tkachenko-wildix/gen-ai-software-engineering/homework-2-submission/homework-2/docs/screenshots/test_coverage.png)

## 💡 Key Architecture Decisions

- **FastAPI + Pydantic v2** — free validation, easy testing, auto-generated OpenAPI docs
- **In-memory, thread-safe store** over a database — zero setup, fast tests; trade-off is data loss on restart (service layer only depends on the store interface, so swapping in a real DB is contained)
- **Rule-based classification, not an LLM** — `TASKS.md` gives exact keyword rules, so a deterministic matcher is free, fast, fully testable; multi-word phrases weighted higher to break ties
- **400 instead of FastAPI's default 422** for validation errors, per the assignment's spec
- **Vanilla JS front-end served by FastAPI itself** — no Node/npm build, no CORS, single process; static mount registered after API routes so it never shadows them
