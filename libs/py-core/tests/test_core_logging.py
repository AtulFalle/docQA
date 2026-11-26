import json
import logging

import pytest
from opentelemetry.sdk.trace import TracerProvider

from docqa_core.logging import configure_logging, get_logger, log_context


def _last_json(out: str) -> dict[str, object]:
    line = [ln for ln in out.splitlines() if ln.strip()][-1]
    parsed: dict[str, object] = json.loads(line)
    return parsed


def test_configure_twice_is_safe(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging()
    configure_logging()
    get_logger("t").info("hello")
    lines = [ln for ln in capsys.readouterr().out.splitlines() if ln.strip()]
    assert len(lines) == 1


def test_json_output_fields(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging(level="INFO", json=True)
    get_logger("t").info("doc.ingested", doc="a")
    record = _last_json(capsys.readouterr().out)
    assert record["event"] == "doc.ingested"
    assert record["level"] == "info"
    assert "timestamp" in record
    assert record["doc"] == "a"
    assert "trace_id" not in record


def test_trace_id_inside_span(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging(json=True)
    tracer = TracerProvider().get_tracer("test")
    with tracer.start_as_current_span("op") as span:
        get_logger("t").info("inside")
        expected = format(span.get_span_context().trace_id, "032x")
    record = _last_json(capsys.readouterr().out)
    assert record["trace_id"] == expected
    assert len(str(record["span_id"])) == 16


def test_static_fields_and_log_context(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging(json=True, service="svc", environment="test")
    with log_context(request_id="r1", tenant_id="t1"):
        get_logger("t").info("inside")
    get_logger("t").info("outside")
    inside, outside = [json.loads(ln) for ln in capsys.readouterr().out.splitlines() if ln.strip()][
        -2:
    ]
    assert (inside["service"], inside["env"]) == ("svc", "test")
    assert (inside["request_id"], inside["tenant_id"]) == ("r1", "t1")
    assert "request_id" not in outside
    configure_logging()


def test_configure_keeps_other_handlers() -> None:
    other = logging.NullHandler()
    logging.getLogger().addHandler(other)
    try:
        configure_logging()
        assert other in logging.getLogger().handlers
    finally:
        logging.getLogger().removeHandler(other)
