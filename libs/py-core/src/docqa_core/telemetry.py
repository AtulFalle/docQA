"""OpenTelemetry setup: traces, logs and metrics exported over OTLP/gRPC.

Logs go to stdout (``docqa_core.logging``) and, when telemetry is enabled, also to the
OTLP collector so they can be searched in Loki next to the trace in Tempo.
"""

import logging

from opentelemetry import metrics, trace
from opentelemetry._logs import SeverityNumber, set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from docqa_core import __version__
from docqa_core.logging import add_root_handler, build_formatter, remove_root_handler

# Fields copied from the structlog event into OTLP log attributes (indexed in Loki).
CORRELATION_FIELDS = (
    "request_id",
    "tenant_id",
    "user_id",
    "workflow_id",
    "workflow_run_id",
    "event",
)

_SEVERITY = {
    logging.DEBUG: SeverityNumber.DEBUG,
    logging.INFO: SeverityNumber.INFO,
    logging.WARNING: SeverityNumber.WARN,
    logging.ERROR: SeverityNumber.ERROR,
    logging.CRITICAL: SeverityNumber.FATAL,
}


class OtlpLogHandler(logging.Handler):
    """Send stdlib/structlog records to the OTLP logs pipeline.

    The body is the same JSON line written to stdout; correlation fields are also set as
    attributes. Trace and span IDs come from the active span when the record is emitted.
    """

    def __init__(self, provider: LoggerProvider) -> None:
        super().__init__()
        self._logger = provider.get_logger("docqa")
        self.setFormatter(build_formatter(json=True))

    def emit(self, record: logging.LogRecord) -> None:
        """Convert one record to an OTLP log record."""
        # The exporter logs its own failures; sending those back to it would loop.
        if record.name.startswith("opentelemetry"):
            return
        try:
            attributes: dict[str, str] = {"logger": record.name}
            if isinstance(record.msg, dict):
                for key in CORRELATION_FIELDS:
                    value = record.msg.get(key)
                    if value is not None:
                        attributes[key] = str(value)
            self._logger.emit(
                timestamp=int(record.created * 1e9),
                severity_number=_SEVERITY.get(record.levelno, SeverityNumber.UNSPECIFIED),
                severity_text=record.levelname,
                body=self.format(record),
                attributes=attributes,
            )
        except Exception:  # noqa: BLE001 - logging must never raise into the caller
            self.handleError(record)


class _State:
    """Providers installed by ``setup_telemetry`` (keeps setup idempotent)."""

    def __init__(self) -> None:
        self.tracer: TracerProvider | None = None
        self.logger: LoggerProvider | None = None
        self.meter: MeterProvider | None = None
        self.handler: OtlpLogHandler | None = None


_state = _State()


def setup_telemetry(
    service_name: str,
    *,
    enabled: bool,
    otlp_endpoint: str,
    environment: str = "local",
) -> TracerProvider | None:
    """Install global trace, log and metric providers exporting via OTLP/gRPC.

    No-op when disabled. Call after ``configure_logging`` so the OTLP handler is added
    next to the stdout handler.
    """
    if not enabled:
        return None
    if _state.tracer is not None:
        return _state.tracer
    resource = Resource.create(
        {
            "service.name": service_name,
            "deployment.environment": environment,
            "service.version": __version__,
        }
    )
    tracer = TracerProvider(resource=resource)
    tracer.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True))
    )
    trace.set_tracer_provider(tracer)

    logger = LoggerProvider(resource=resource)
    logger.add_log_record_processor(
        BatchLogRecordProcessor(OTLPLogExporter(endpoint=otlp_endpoint, insecure=True))
    )
    set_logger_provider(logger)
    handler = OtlpLogHandler(logger)
    add_root_handler(handler)

    meter = MeterProvider(
        resource=resource,
        metric_readers=[
            PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True))
        ],
    )
    metrics.set_meter_provider(meter)

    _state.tracer, _state.logger, _state.meter, _state.handler = tracer, logger, meter, handler
    return tracer


def get_tracer(name: str) -> trace.Tracer:
    """Return a tracer for ``name`` from the global provider."""
    return trace.get_tracer(name)


def get_meter(name: str) -> metrics.Meter:
    """Return a meter for ``name`` from the global provider."""
    return metrics.get_meter(name)


def shutdown_telemetry() -> None:
    """Flush and shut down the providers installed by ``setup_telemetry`` (if any)."""
    if _state.handler is not None:
        remove_root_handler(_state.handler)
    for provider in (_state.tracer, _state.logger, _state.meter):
        if provider is not None:
            provider.shutdown()
    _state.tracer = _state.logger = _state.meter = _state.handler = None
