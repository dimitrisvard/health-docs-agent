"""OpenTelemetry tracing — a safe no-op when OTel isn't installed or configured.

`span(...)` wraps an agent turn (or any block) in a span when a tracer is available, and
degrades to a plain context manager otherwise, so the loop and tests never hard-depend on
OpenTelemetry. `configure_tracing(app)` wires an OTLP exporter when an endpoint is set and
instruments FastAPI for per-request spans.
"""
from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

try:
    from opentelemetry import trace as _otel_trace

    _TRACER: Any = _otel_trace.get_tracer("health-docs-agent")
except Exception:  # opentelemetry not installed
    _TRACER = None


@contextmanager
def span(name: str, **attributes: Any) -> Iterator[Any]:
    """Start a span if tracing is available; otherwise a no-op context."""
    if _TRACER is None:
        yield None
        return
    with _TRACER.start_as_current_span(name) as current:
        for key, value in attributes.items():
            try:
                current.set_attribute(key, value)
            except Exception:
                pass
        yield current


def configure_tracing(app: Any = None) -> None:
    """Best-effort: set up an OTLP exporter when configured and instrument FastAPI.

    Never raises — tracing must not block startup if a dependency or endpoint is missing.
    """
    try:
        endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
        if endpoint:
            from opentelemetry import trace
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            provider = TracerProvider(resource=Resource.create({"service.name": "health-docs-agent"}))
            provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
            trace.set_tracer_provider(provider)
        if app is not None:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

            FastAPIInstrumentor.instrument_app(app)
    except Exception:
        pass
