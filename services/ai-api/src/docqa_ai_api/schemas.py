"""Response bodies of the ai-api. They define its OpenAPI contract with the backend."""

from typing import Literal

from pydantic import BaseModel, Field


class LivenessResponse(BaseModel):
    """The process is up."""

    status: Literal["ok"]


class ReadinessResponse(BaseModel):
    """Whether the service can take traffic; `checks` lists failed dependencies."""

    status: Literal["ready", "unavailable"]
    checks: dict[str, Literal["error"]] | None = Field(
        default=None, description="Present when not ready, e.g. {'database': 'error'}."
    )


class ServiceInfo(BaseModel):
    """Service name, version and environment."""

    service: str
    version: str
    env: str
