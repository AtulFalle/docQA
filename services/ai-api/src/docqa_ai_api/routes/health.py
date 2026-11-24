"""Liveness and readiness probes."""

import asyncio

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from docqa_ai_api.schemas import LivenessResponse, ReadinessResponse
from docqa_core.logging import get_logger

router = APIRouter(tags=["health"])
READY_TIMEOUT_S = 2.0


@router.get("/healthz", summary="Liveness probe")
async def healthz() -> LivenessResponse:
    """Liveness probe."""
    return LivenessResponse(status="ok")


@router.get(
    "/readyz",
    summary="Readiness probe",
    response_model=ReadinessResponse,
    responses={503: {"model": ReadinessResponse, "description": "A dependency is down"}},
)
async def readyz(request: Request) -> JSONResponse:
    """Readiness probe: 200 if the database answers, else 503."""
    try:
        async with asyncio.timeout(READY_TIMEOUT_S):
            async with request.app.state.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
    except (OSError, TimeoutError, SQLAlchemyError) as exc:
        get_logger(__name__).warning("readyz.failed", error=type(exc).__name__)
        body = ReadinessResponse(status="unavailable", checks={"database": "error"})
        return JSONResponse(status_code=503, content=body.model_dump(exclude_none=True))
    body = ReadinessResponse(status="ready")
    return JSONResponse(status_code=200, content=body.model_dump(exclude_none=True))
