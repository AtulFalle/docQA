"""Versioned API routes."""

from fastapi import APIRouter, Request

from docqa_core import __version__

router = APIRouter(prefix="/v1", tags=["v1"])


@router.get("/info")
async def info(request: Request) -> dict[str, str]:
    """Return service name, version and environment."""
    settings = request.app.state.settings
    return {"service": settings.service_name, "version": __version__, "env": settings.env}
