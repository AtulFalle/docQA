"""Temporal worker entrypoint."""

import asyncio

from temporalio.client import Client, Interceptor
from temporalio.worker import Worker

from docqa_core.config import Settings, get_settings
from docqa_core.logging import configure_logging, get_logger
from docqa_core.telemetry import setup_telemetry, shutdown_telemetry
from docqa_workers.activities.ingest import ALL_ACTIVITIES
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
    configure_logging(settings.log_level, json=settings.log_json)
    setup_telemetry(
        f"{settings.service_name}-worker",
        enabled=settings.otel_enabled,
        otlp_endpoint=settings.otel_exporter_otlp_endpoint,
        environment=settings.env,
    )
    try:
        asyncio.run(run_worker(settings))
    except KeyboardInterrupt:
        pass
    finally:
        shutdown_telemetry()
