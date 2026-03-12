"""
OpenTelemetry tracing scaffold for VarunaPoC backend.

Provides a thin wrapper around OpenTelemetry so that the rest of the codebase
can call get_tracer() regardless of whether the OpenTelemetry packages are
actually installed.

When OTEL_ENABLED is not "true" (the default), or when the opentelemetry
packages are absent, all functions degrade gracefully to no-op stubs so there
is zero runtime overhead and zero hard dependency.

Configuration (environment variables):
    OTEL_ENABLED        Set to "true" to activate real tracing (default: false)
    OTEL_EXPORTER_OTLP_ENDPOINT
                        OTLP collector endpoint (default: http://localhost:4317)
    OTEL_SERVICE_NAME   Override service name (default: varuna-backend)

Usage:
    from core.tracing import get_tracer

    tracer = get_tracer(__name__)
    with tracer.start_as_current_span("my-operation") as span:
        span.set_attribute("slide.id", slide_id)
        ...

Setup (called once from main.py):
    from core.tracing import setup_tracing
    setup_tracing(app)
"""

import logging
import os

logger = logging.getLogger(__name__)

_OTEL_ENABLED = os.getenv("OTEL_ENABLED", "false").lower() == "true"
_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "varuna-backend")
_OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

# ---------------------------------------------------------------------------
# No-op stubs — used when opentelemetry is not installed or OTEL_ENABLED=false
# ---------------------------------------------------------------------------


class _NoOpSpan:
    """Minimal no-op span that satisfies context-manager protocol."""

    def set_attribute(self, key: str, value: object) -> None:
        """Accept attribute calls without effect."""

    def add_event(self, name: str, attributes: dict | None = None) -> None:
        """Accept event calls without effect."""

    def set_status(self, status: object) -> None:
        """Accept status calls without effect."""

    def __enter__(self) -> "_NoOpSpan":
        return self

    def __exit__(self, *args: object) -> None:
        pass


class _NoOpTracer:
    """Minimal no-op tracer returned when OpenTelemetry is unavailable."""

    def start_as_current_span(self, name: str, **kwargs: object) -> _NoOpSpan:  # noqa: ARG002
        """Return a no-op span regardless of arguments.

        Args:
            name: Span name (ignored).
            **kwargs: Additional span options (ignored).

        Returns:
            A _NoOpSpan instance that satisfies the context-manager protocol.
        """
        return _NoOpSpan()

    def start_span(self, name: str, **kwargs: object) -> _NoOpSpan:  # noqa: ARG002
        """Return a no-op span.

        Args:
            name: Span name (ignored).
            **kwargs: Additional span options (ignored).

        Returns:
            A _NoOpSpan instance.
        """
        return _NoOpSpan()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def setup_tracing(app: object) -> None:
    """Configure OpenTelemetry TracerProvider and attach FastAPI instrumentation.

    Must be called once after the FastAPI application object is created,
    before the first request is handled.  When OTEL_ENABLED is not "true" or
    when the opentelemetry packages are absent, this function is a no-op.

    Args:
        app: The FastAPI application instance to instrument.

    Technical Notes:
        - Requires: opentelemetry-api, opentelemetry-sdk,
          opentelemetry-instrumentation-fastapi, opentelemetry-exporter-otlp
        - Uses BatchSpanProcessor for low-latency export.
        - OTLP endpoint is read from OTEL_EXPORTER_OTLP_ENDPOINT env var.
        - Service name is read from OTEL_SERVICE_NAME env var (default:
          varuna-backend).
        - If the exporter cannot connect at startup, spans are silently
          dropped — tracing must never break the application.

    Examples:
        >>> from fastapi import FastAPI
        >>> from core.tracing import setup_tracing
        >>> app = FastAPI()
        >>> setup_tracing(app)  # no-op when OTEL_ENABLED != "true"
    """
    if not _OTEL_ENABLED:
        logger.debug("[tracing] OTEL_ENABLED is false — tracing disabled")
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import SERVICE_NAME, Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource(attributes={SERVICE_NAME: _SERVICE_NAME})
        provider = TracerProvider(resource=resource)

        exporter = OTLPSpanExporter(endpoint=_OTLP_ENDPOINT, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))

        trace.set_tracer_provider(provider)

        FastAPIInstrumentor.instrument_app(app)

        logger.info(
            "[tracing] OpenTelemetry enabled — service=%s endpoint=%s",
            _SERVICE_NAME,
            _OTLP_ENDPOINT,
        )

    except ImportError as exc:
        logger.warning(
            "[tracing] OpenTelemetry packages not installed — tracing disabled (%s)", exc
        )
    except Exception as exc:
        # Tracing must never prevent the application from starting.
        logger.warning(
            "[tracing] Failed to initialise OpenTelemetry — continuing without tracing (%s)", exc
        )


def get_tracer(name: str) -> object:
    """Return an OpenTelemetry tracer, or a no-op tracer if unavailable.

    This is the primary entry point for instrumentation in route handlers and
    services.  Callers never need to check whether tracing is enabled.

    Args:
        name: Tracer name, typically the module's __name__.

    Returns:
        A real opentelemetry.trace.Tracer when OTEL_ENABLED=true and the
        packages are installed, otherwise a _NoOpTracer instance whose methods
        are all no-ops.

    Examples:
        >>> tracer = get_tracer(__name__)
        >>> with tracer.start_as_current_span("tile-fetch") as span:
        ...     span.set_attribute("tile.level", 2)
    """
    if not _OTEL_ENABLED:
        return _NoOpTracer()

    try:
        from opentelemetry import trace

        return trace.get_tracer(name)
    except ImportError:
        return _NoOpTracer()
