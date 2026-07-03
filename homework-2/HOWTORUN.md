# How to Run

Step-by-step guide to set up, run, and test the Intelligent Customer Support
System locally. Commands are given for both **Windows (PowerShell)** and
**macOS/Linux (bash/zsh)** — pick the block for your platform.

## Prerequisites

- Python 3.11+ (developed and tested with Python 3.13)
- Windows: PowerShell. macOS/Linux: bash or zsh.

## 1. Set Up the Environment

**Windows (PowerShell):**

```powershell
cd homework-2
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> If `Activate.ps1` is blocked by execution policy, you can skip activation
> and call the venv's Python directly, e.g. `.\.venv\Scripts\python.exe ...`
> for every command below instead of `python ...`.

**macOS / Linux (bash/zsh):**

```bash
cd homework-2
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Run the API Server

**Windows:**

```powershell
.\.venv\Scripts\python.exe -m uvicorn src.main:app --reload
```

**macOS / Linux:**

```bash
python -m uvicorn src.main:app --reload
```

- API base URL: `http://127.0.0.1:8000`
- Interactive Swagger docs: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`
- **Web UI: `http://127.0.0.1:8000/`**

Press `Ctrl+C` to stop the server.

## 3. Using the Web UI

Open `http://127.0.0.1:8000/` in a browser (no separate front-end server or
build step needed — it's served directly by the same FastAPI process). From
there you can:

- Browse and filter tickets by category, priority, status, or customer ID
- Click **+ New Ticket** to create one via a validated form
- Click a row (or **View**) to see full details, including the
  classification result (category, priority, confidence, reasoning, keywords)
  and metadata
- Click **Classify** to run auto-classification on an existing ticket
- Click **⇪ Bulk Import** to upload a `.csv`/`.json`/`.xml` file (e.g. one of
  the files in `demo/`) and see the import summary
- Resize the window (or use a mobile device) to see the responsive layout

## 4. Try the API Directly

Create a ticket:

**Windows (PowerShell):**

```powershell
curl -X POST http://127.0.0.1:8000/tickets `
  -H "Content-Type: application/json" `
  -d '{\"customer_id\":\"cust-1\",\"customer_email\":\"jane@example.com\",\"customer_name\":\"Jane Doe\",\"subject\":\"Cannot log in\",\"description\":\"I forgot my password and cannot access my account.\"}'
```

**macOS / Linux:**

```bash
curl -X POST http://127.0.0.1:8000/tickets \
  -H "Content-Type: application/json" \
  -d '{"customer_id":"cust-1","customer_email":"jane@example.com","customer_name":"Jane Doe","subject":"Cannot log in","description":"I forgot my password and cannot access my account."}'
```

Bulk-import the provided sample data (same command on all platforms — run
from the `homework-2/` directory):

```bash
curl -X POST "http://127.0.0.1:8000/tickets/import?auto_classify=true" -F "file=@demo/sample_tickets.csv;type=text/csv"
curl -X POST "http://127.0.0.1:8000/tickets/import?auto_classify=true" -F "file=@demo/sample_tickets.json;type=application/json"
curl -X POST "http://127.0.0.1:8000/tickets/import?auto_classify=true" -F "file=@demo/sample_tickets.xml;type=application/xml"
```

Try the negative-test (invalid) sample data to see per-record validation errors:

```bash
curl -X POST http://127.0.0.1:8000/tickets/import -F "file=@demo/invalid_sample_tickets.csv;type=text/csv"
```

List and filter tickets:

```bash
curl "http://127.0.0.1:8000/tickets?category=billing_question&priority=high"
```

See [API_REFERENCE.md](API_REFERENCE.md) for the full endpoint list with
request/response examples.

## 5. Run the Test Suite

**Windows:**

```powershell
.\.venv\Scripts\python.exe -m pytest
```

**macOS / Linux:**

```bash
python -m pytest
```

This runs all 89 tests and enforces >85% coverage (currently ~99%). To view
the detailed HTML coverage report:

```powershell
start htmlcov\index.html          # Windows
```

```bash
open htmlcov/index.html           # macOS
xdg-open htmlcov/index.html       # Linux
```

See [TESTING_GUIDE.md](TESTING_GUIDE.md) for more (running individual test
files, the manual testing checklist, performance benchmarks).

## 6. Regenerate Sample Data (optional)

The `demo/` sample data files are checked into the repo, but can be
regenerated deterministically:

**Windows:**

```powershell
.\.venv\Scripts\python.exe scripts\generate_sample_data.py
```

**macOS / Linux:**

```bash
python scripts/generate_sample_data.py
```

## Troubleshooting

- **`ModuleNotFoundError: No module named 'src'`** — make sure you're running
  commands from the `homework-2/` directory (not the repo root or `src/`),
  and that you're using the venv's Python (activated venv, or the full path
  `.\.venv\Scripts\python.exe` on Windows / `.venv/bin/python` on macOS/Linux).
- **Port already in use** — pass a different port:
  `uvicorn src.main:app --reload --port 8001`.
- **`Activate.ps1` cannot be loaded because running scripts is disabled**
  (Windows only) — either run
  `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first, or
  skip activation and call `.\.venv\Scripts\python.exe` directly as noted above.
- **`python: command not found` (macOS/Linux)** — use `python3` instead of
  `python` (some systems only alias `python` after the venv is activated).
