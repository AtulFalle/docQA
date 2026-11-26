import json
import logging

from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import InMemoryLogRecordExporter, SimpleLogRecordProcessor
from opentelemetry.sdk.trace import TracerProvider

from docqa_core.logging import configure_logging, get_logger, log_context
from docqa_core.telemetry import OtlpLogHandler


def _handler() -> tuple[OtlpLogHandler, InMemoryLogRecordExporter]:
    exporter = InMemoryLogRecordExporter()  # type: ignore[no-untyped-call]
    provider = LoggerProvider()
    provider.add_log_record_processor(SimpleLogRecordProcessor(exporter))
    return OtlpLogHandler(provider), exporter


def test_otlp_handler_exports_json_body_with_correlation() -> None:
    configure_logging(service="svc", environment="test")
    handler, exporter = _handler()
    root = logging.getLogger()
    root.addHandler(handler)
    tracer = TracerProvider().get_tracer("test")
    try:
        with tracer.start_as_current_span("op") as span, log_context(request_id="r1"):
            get_logger("t").warning("thing.happened", detail=1)
            trace_id = span.get_span_context().trace_id
    finally:
        root.removeHandler(handler)

    [data] = exporter.get_finished_logs()
    record = data.log_record
    body = json.loads(str(record.body))
    assert body["event"] == "thing.happened"
    assert body["service"] == "svc"
    assert body["trace_id"] == format(trace_id, "032x")
    assert record.attributes is not None
    assert record.attributes["request_id"] == "r1"
    assert record.severity_text == "WARNING"
    assert record.trace_id == trace_id


def test_otlp_handler_skips_otel_internal_logs() -> None:
    handler, exporter = _handler()
    logger = logging.getLogger("opentelemetry.exporter.test")
    logger.addHandler(handler)
    try:
        logger.error("export failed")
    finally:
        logger.removeHandler(handler)
    assert exporter.get_finished_logs() == ()
