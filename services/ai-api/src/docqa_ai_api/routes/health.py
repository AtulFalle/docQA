"""Liveness and readiness probes."""

import asyncio

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from docqa_core.logging import get_logger

router = APIRouter(tags=["health"])
READY_TIMEOUT_S = 2.0


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@router.get("/readyz")
async def readyz(request: Request) -> JSONResponse:
    """Readiness probe: 200 if the database answers, else 503."""
    try:
        async with asyncio.timeout(READY_TIMEOUT_S):
            async with request.app.state.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
    except (OSError, TimeoutError, SQLAlchemyError) as exc:
        get_logger(__name__).warning("readyz.failed", error=type(exc).__name__)
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "checks": {"database": "error"}},
        )
    return JSONResponse(status_code=200, content={"status": "ready"})
