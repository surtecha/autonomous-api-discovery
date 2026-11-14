"""Allowlisted telemetry. No bodies, origins, paths, headers, or exceptions are exported."""

from __future__ import annotations

import json
import logging
import os
import time
from collections.abc import Iterator
from contextlib import contextmanager
from importlib import import_module
from types import ModuleType


@contextmanager
def stage(name: str, session_id: str = "") -> Iterator[None]:
    started = time.monotonic()
    category = "success"
    metrics: ModuleType | None = None
    trace: ModuleType | None = None
    try:
        metrics = import_module("opentelemetry.metrics")
        trace = import_module("opentelemetry.trace")
    except ImportError:
        metrics = trace = None
    span = trace.get_tracer("api_discovery").start_span(name) if trace else None
    if span:
        span.set_attribute("session.id", session_id)
    try:
        yield
    except Exception:
        category = "failure"
        raise
    finally:
        duration = (time.monotonic() - started) * 1000
        if span:
            span.set_attribute("result.category", category)
            span.set_attribute("duration.ms", duration)
            span.end()
        if metrics:
            meter = metrics.get_meter("api_discovery")
            meter.create_counter("discovery.stage.executions").add(
                1, {"stage": name, "category": category}
            )
            meter.create_histogram("discovery.stage.duration", unit="ms").record(
                duration, {"stage": name}
            )
        logging.getLogger("discovery.audit").info(
            json.dumps(
                {
                    "session_id": session_id,
                    "stage": name,
                    "duration_ms": round(duration, 2),
                    "category": category,
                }
            )
        )


def configure() -> None:
    """Export allowlisted stages to console when explicitly enabled by the operator."""
    from opentelemetry import metrics, trace
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider

    mode = os.environ.get("DISCOVERY_TELEMETRY", "off")
    if mode not in {"off", "console"}:
        raise ValueError("DISCOVERY_TELEMETRY must be off or console")
    resource = Resource({"service.name": "api-discovery-worker"})
    tracer = TracerProvider(resource=resource)
    if mode == "console":
        from opentelemetry.sdk.metrics.export import (
            ConsoleMetricExporter,
            PeriodicExportingMetricReader,
        )
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

        tracer.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
        reader = PeriodicExportingMetricReader(
            ConsoleMetricExporter(), export_interval_millis=30000
        )
        meter = MeterProvider(resource=resource, metric_readers=[reader])
    else:
        meter = MeterProvider(resource=resource)
    trace.set_tracer_provider(tracer)
    metrics.set_meter_provider(meter)
