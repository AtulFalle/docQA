"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from docqa_ai_api.middleware import RequestContextMiddleware
from docqa_ai_api.routes import health, v1
from docqa_core import __version__
from docqa_core.config import Settings, get_settings
from docqa_core.db import make_engine
from docqa_core.logging import configure_logging, get_logger
from docqa_core.telemetry import setup_telemetry, shutdown_telemetry


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the FastAPI app, wiring middleware, routers and lifecycle hooks."""
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        configure_logging(
            settings.log_level,
            json=settings.log_json,
            service=settings.service_name,
            environment=settings.env,
        )
        setup_telemetry(
            settings.service_name,
            enabled=settings.otel_enabled,
            otlp_endpoint=settings.otel_exporter_otlp_endpoint,
            environment=settings.env,
        )
        app.state.settings = settings
        app.state.engine = make_engine(settings.database_url)
        get_logger(__name__).info("api.startup", env=settings.env, version=__version__)
        try:
            yield
        finally:
            await app.state.engine.dispose()
            shutdown_telemetry()

    app = FastAPI(title="docQA AI service (internal)", version=__version__, lifespan=lifespan)
    app.add_middleware(RequestContextMiddleware)
    app.include_router(health.router)
    app.include_router(v1.router)

    if settings.otel_enabled:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app)

    return app


app = create_app()
