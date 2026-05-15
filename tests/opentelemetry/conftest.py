"""Shared fixtures for OpenTelemetry tracing tests.

Sets up an in-memory TracerProvider so that spans created by the SDK
can be collected and inspected without any external backend.
"""

import pytest

from opentelemetry import trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics import Counter, Histogram, ObservableUpDownCounter, UpDownCounter
from opentelemetry.sdk.metrics.export import AggregationTemporality
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

_provider = TracerProvider()
_exporter = InMemorySpanExporter()
_provider.add_span_processor(SimpleSpanProcessor(_exporter))
trace.set_tracer_provider(_provider)


@pytest.fixture()
def tracing_setup():
    """Enable SDK tracing, yield the exporter, then restore noop defaults.

    Each test gets a clean exporter (cleared before and after).
    """
    _exporter.clear()

    from ydb.opentelemetry import disable_tracing, enable_tracing

    disable_tracing()
    enable_tracing()

    yield _exporter

    # Restore noop state
    disable_tracing()
    _exporter.clear()


@pytest.fixture()
def metrics_setup():
    """Enable SDK metrics with an in-memory reader, then restore noop defaults."""
    from ydb.opentelemetry import disable_metrics, enable_metrics

    reader = InMemoryMetricReader(
        preferred_temporality={
            Counter: AggregationTemporality.CUMULATIVE,
            Histogram: AggregationTemporality.CUMULATIVE,
            ObservableUpDownCounter: AggregationTemporality.CUMULATIVE,
            UpDownCounter: AggregationTemporality.CUMULATIVE,
        }
    )
    provider = MeterProvider(metric_readers=[reader])

    disable_metrics()
    enable_metrics(provider)
    try:
        yield reader
    finally:
        disable_metrics()
        provider.shutdown()


class FakeDriverConfig:
    def __init__(self, endpoint="test_endpoint:1337", database="/test_database"):
        self.endpoint = endpoint
        self.database = database
        self.query_client_settings = None
        self.tracer = None
