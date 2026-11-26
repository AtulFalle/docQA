"""Temporal worker entrypoint."""

import asyncio
import contextlib

from temporalio.client import Client, Interceptor
from temporalio.worker import Worker

from docqa_core.config import Settings, get_settings
from docqa_core.logging import configure_logging, get_logger
from docqa_core.telemetry import setup_telemetry, shutdown_telemetry
from docqa_workers.activities.ingest import ALL_ACTIVITIES
from docqa_workers.log_context import LogContextInterceptor
from docqa_workers.workflows.ingest import IngestDocumentWorkflow


async def run_worker(settings: Settings) -> None:
    """Connect to Temporal and run the ingestion worker until cancelled."""
    interceptors: list[Interceptor] = []
    if settings.otel_enabled:
        from temporalio.contrib.opentelemetry import TracingInterceptor

        interceptors.append(TracingInterceptor())
    client = await Client.connect(
        settings.temporal_address,
        namespace=settings.temporal_namespace,
        interceptors=interceptors,
    )
    worker = Worker(
        client,
        task_queue=settings.temporal_task_queue,
        workflows=[IngestDocumentWorkflow],
        activities=ALL_ACTIVITIES,
        interceptors=[LogContextInterceptor()],
    )
    get_logger(__name__).info(
        "worker.started",
        task_queue=settings.temporal_task_queue,
        address=settings.temporal_address,
    )
    await worker.run()


def main() -> None:
    """Configure logging/telemetry and run the worker."""
    settings = get_settings()
    service = f"{settings.service_name}-worker"
    configure_logging(
        settings.log_level, json=settings.log_json, service=service, environment=settings.env
    )
    setup_telemetry(
        service,
        enabled=settings.otel_enabled,
        otlp_endpoint=settings.otel_exporter_otlp_endpoint,
        environment=settings.env,
    )
    try:
        # Ctrl+C is the normal way to stop the worker locally; exit cleanly, no traceback.
        with contextlib.suppress(KeyboardInterrupt):
            asyncio.run(run_worker(settings))
    finally:
        shutdown_telemetry()
