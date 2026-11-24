"""Versioned API routes."""

from fastapi import APIRouter, Request

from docqa_ai_api.schemas import ServiceInfo
from docqa_core import __version__

router = APIRouter(prefix="/v1", tags=["v1"])


@router.get("/info", summary="Service info")
async def info(request: Request) -> ServiceInfo:
    """Return service name, version and environment."""
    settings = request.app.state.settings
    return ServiceInfo(service=settings.service_name, version=__version__, env=settings.env)
