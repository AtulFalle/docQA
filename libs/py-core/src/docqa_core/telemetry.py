"""OpenTelemetry tracing setup."""

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from docqa_core import __version__


class _State:
    """Holder for the installed tracer provider (keeps setup idempotent)."""

    provider: TracerProvider | None = None


_state = _State()


def setup_telemetry(
    service_name: str,
    *,
    enabled: bool,
    otlp_endpoint: str,
    environment: str = "local",
) -> TracerProvider | None:
    """Install a global tracer provider exporting via OTLP/gRPC. No-op when disabled."""
    if not enabled:
        return None
    if _state.provider is not None:
        return _state.provider
    resource = Resource.create(
        {
            "service.name": service_name,
            "deployment.environment": environment,
            "service.version": __version__,
        }
    )
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True))
    )
    trace.set_tracer_provider(provider)
    _state.provider = provider
    return provider


def get_tracer(name: str) -> trace.Tracer:
    """Return a tracer for ``name`` from the global provider."""
    return trace.get_tracer(name)


def shutdown_telemetry() -> None:
    """Flush and shut down the provider installed by ``setup_telemetry`` (if any)."""
    if _state.provider is not None:
        _state.provider.shutdown()
        _state.provider = None
