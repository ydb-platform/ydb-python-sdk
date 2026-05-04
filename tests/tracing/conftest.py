"""Shared fixtures for OpenTelemetry tracing tests.

Sets up an in-memory TracerProvider so that spans created by the SDK
can be collected and inspected without any external backend.
"""

import pytest

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

_provider = TracerProvider()
_exporter = InMemorySpanExporter()
_provider.add_span_processor(SimpleSpanProcessor(_exporter))
trace.set_tracer_provider(_provider)


@pytest.fixture()
def otel_setup():
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


class FakeDriverConfig:
    def __init__(self, endpoint="test_endpoint:1337", database="/test_database"):
        self.endpoint = endpoint
        self.database = database
        self.query_client_settings = None
        self.tracer = None
