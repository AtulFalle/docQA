"""Structured logging (structlog) with stdlib integration and OTel trace correlation.

Every log line is JSON with the same correlation fields across services:
``service``, ``env``, ``request_id``, ``trace_id``, ``span_id`` and, when known,
``tenant_id``, ``user_id``, ``workflow_id`` and ``workflow_run_id``.
Use ``log_context`` / ``bind_log_context`` to attach request- or job-scoped fields
instead of passing them to every call.
"""

import logging
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import structlog
from opentelemetry import trace

_STDOUT_HANDLER_FLAG = "_docqa_stdout"


class _State:
    """Static fields added to every record (set by ``configure_logging``)."""

    def __init__(self) -> None:
        self.static: dict[str, str] = {}


_state = _State()


def add_otel_context(
    _logger: Any, _method_name: str, event_dict: structlog.typing.EventDict
) -> structlog.typing.EventDict:
    """Add trace_id / span_id (hex) of the current span when it is valid."""
    ctx = trace.get_current_span().get_span_context()
    if ctx.is_valid:
        event_dict["trace_id"] = format(ctx.trace_id, "032x")
        event_dict["span_id"] = format(ctx.span_id, "016x")
    return event_dict


def add_static_fields(
    _logger: Any, _method_name: str, event_dict: structlog.typing.EventDict
) -> structlog.typing.EventDict:
    """Add ``service`` and ``env`` without overriding values set by the caller."""
    for key, value in _state.static.items():
        event_dict.setdefault(key, value)
    return event_dict


def _shared_processors() -> list[structlog.typing.Processor]:
    return [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        add_static_fields,
        add_otel_context,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]


def build_formatter(*, json: bool = True) -> logging.Formatter:
    """Return the formatter used for stdout; also used for the OTLP log body."""
    renderer: structlog.typing.Processor = (
        structlog.processors.JSONRenderer()
        if json
        else structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty())
    )
    return structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=_shared_processors(),
        processors=[structlog.stdlib.ProcessorFormatter.remove_processors_meta, renderer],
    )


def configure_logging(
    level: str = "INFO",
    *,
    json: bool = True,
    service: str | None = None,
    environment: str | None = None,
) -> None:
    """Configure structlog and route stdlib logging through it. Safe to call repeatedly.

    Only the stdout handler installed here is replaced; other root handlers (such as
    the OTLP log handler from ``docqa_core.telemetry``) are kept.
    """
    _state.static = {k: v for k, v in (("service", service), ("env", environment)) if v is not None}
    structlog.configure(
        processors=[*_shared_processors(), structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=False,
    )
    # Create the handler at call time so it binds to the current sys.stdout (capsys-friendly).
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(build_formatter(json=json))
    setattr(handler, _STDOUT_HANDLER_FLAG, True)
    root = logging.getLogger()
    for old in [h for h in root.handlers if getattr(h, _STDOUT_HANDLER_FLAG, False)]:
        root.removeHandler(old)
    root.addHandler(handler)
    root.setLevel(level.upper())


def add_root_handler(handler: logging.Handler) -> None:
    """Add an extra handler (for example the OTLP exporter) to the root logger."""
    logging.getLogger().addHandler(handler)


def remove_root_handler(handler: logging.Handler) -> None:
    """Remove a handler added with ``add_root_handler``."""
    logging.getLogger().removeHandler(handler)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a structlog logger bound to ``name``."""
    logger: structlog.stdlib.BoundLogger = structlog.stdlib.get_logger(name)
    return logger


def bind_log_context(**fields: object) -> None:
    """Attach fields to every log line in the current context (request, task or activity)."""
    structlog.contextvars.bind_contextvars(**fields)


def clear_log_context() -> None:
    """Remove all fields bound with ``bind_log_context`` in the current context."""
    structlog.contextvars.clear_contextvars()


@contextmanager
def log_context(**fields: object) -> Iterator[None]:
    """Attach fields to every log line inside the ``with`` block, then restore."""
    with structlog.contextvars.bound_contextvars(**fields):
        yield
