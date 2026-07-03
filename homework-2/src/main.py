"""FastAPI application entrypoint.

Run with: `uvicorn src.main:app --reload` from the `homework-2/` directory.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src.exceptions import TicketNotFoundError
from src.routers.tickets import router as tickets_router

app = FastAPI(
    title="Intelligent Customer Support System",
    description="Multi-format ticket import, auto-classification, and management API.",
    version="1.0.0",
)

app.include_router(tickets_router)


@app.get("/health", tags=["health"])
def health_check() -> dict:
    return {"status": "ok"}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return 400 (not FastAPI's default 422) with field-level details, per the
    homework's requirement to use 400 for invalid input.
    """
    details = [
        {
            "field": ".".join(str(part) for part in err["loc"] if part != "body"),
            "message": err["msg"],
        }
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Validation failed", "details": details},
    )


@app.exception_handler(TicketNotFoundError)
async def ticket_not_found_handler(request: Request, exc: TicketNotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": str(exc)},
    )


# Front-end (vanilla HTML/CSS/JS). Mounted last so that it acts as a catch-all
# only for paths not already matched by the API routes/handlers above (e.g.
# /tickets, /health) — Starlette checks routes in registration order.
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="frontend")
