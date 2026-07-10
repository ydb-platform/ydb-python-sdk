"""Unit tests for the vendor-neutral ``ydb.observability`` tracing entrypoints.

These tests use a hand-rolled TracingProvider (no OpenTelemetry involvement)
to verify that:

* ``enable_tracing(provider)`` accepts an arbitrary implementation of the
  ``TracingProvider`` protocol,
* a second ``enable_tracing`` call replaces (resets) the previous provider,
* ``disable_tracing()`` returns the SDK to the Noop provider,
* the SDK produces spans through whichever provider is currently installed,
* ``get_trace_metadata`` is empty until a provider is enabled.
"""

from typing import Any, Dict, List, Optional, Tuple

import pytest

from ydb.observability import (
    NoopSpan,
    NoopTracingProvider,
    Span,
    SpanName,
    TracingProvider,
    disable_tracing,
    enable_tracing,
    get_active_provider,
)
from ydb.observability.tracing import (
    _registry,
    create_span,
    create_ydb_span,
    get_trace_metadata,
)

from .conftest import FakeDriverConfig


class RecordingSpan:
    """Minimal Span implementation that records every call."""

    def __init__(self, name: str, attributes: Optional[dict], kind: Optional[str], sink: List[Dict[str, Any]]):
        self.name = name
        self.attributes: Dict[str, Any] = dict(attributes or {})
        self.kind = kind
        self.ended = False
        self.errors: List[BaseException] = []
        self._sink = sink

    def set_error(self, exception):
        self.errors.append(exception)

    def set_attribute(self, key, value):
        self.attributes[key] = value

    def end(self):
        self.ended = True
        self._sink.append(
            {
                "name": self.name,
                "attributes": dict(self.attributes),
                "kind": self.kind,
                "ended": True,
                "errors": list(self.errors),
            }
        )

    def attach_context(self, end_on_exit: bool = True):
        span = self

        class _Ctx:
            def __enter__(self_inner):
                return span

            def __exit__(self_inner, exc_type, exc_val, exc_tb):
                if exc_val is not None:
                    span.set_error(exc_val)
                    span.end()
                elif end_on_exit:
                    span.end()
                return False

        return _Ctx()


class RecordingProvider:
    """Custom TracingProvider used across the tests."""

    def __init__(self, metadata: Optional[List[Tuple[str, str]]] = None):
        self.spans: List[RecordingSpan] = []
        self.finished: List[Dict[str, Any]] = []
        self._metadata = metadata or []

    def create_span(self, name, attributes=None, kind=None) -> Span:
        span = RecordingSpan(name, attributes, kind, self.finished)
        self.spans.append(span)
        return span

    def get_trace_metadata(self):
        return list(self._metadata)


@pytest.fixture(autouse=True)
def _reset_registry():
    """Guarantee a clean Noop state around every test in this module."""
    disable_tracing()
    yield
    disable_tracing()


class TestDefaultsAreNoop:
    def test_registry_starts_inactive(self):
        assert _registry.is_active() is False
        assert get_active_provider() is None

    def test_create_ydb_span_is_noop_when_disabled(self):
        span = create_ydb_span(SpanName.EXECUTE_QUERY, FakeDriverConfig())
        assert isinstance(span, NoopSpan)
        # NoopSpan methods must be safely callable
        span.set_attribute("x", 1)
        span.set_error(RuntimeError("boom"))
        span.end()

    def test_get_trace_metadata_is_empty_when_disabled(self):
        assert get_trace_metadata() == []


class TestEnableTracingWithCustomProvider:
    def test_custom_provider_receives_spans(self):
        provider = RecordingProvider()
        enable_tracing(provider)

        assert _registry.is_active() is True
        assert get_active_provider() is provider

        with create_ydb_span(SpanName.EXECUTE_QUERY, FakeDriverConfig()).attach_context() as span:
            span.set_attribute("custom.attr", "hello")

        assert len(provider.spans) == 1
        recorded = provider.spans[0]
        assert recorded.name == SpanName.EXECUTE_QUERY
        assert recorded.attributes["db.system.name"] == "ydb"
        assert recorded.attributes["custom.attr"] == "hello"
        assert recorded.ended is True

    def test_custom_provider_metadata_is_returned(self):
        provider = RecordingProvider(metadata=[("traceparent", "abc")])
        enable_tracing(provider)

        assert get_trace_metadata() == [("traceparent", "abc")]

    def test_internal_span_helper_uses_active_provider(self):
        provider = RecordingProvider()
        enable_tracing(provider)

        with create_span(SpanName.RUN_WITH_RETRY):
            pass

        assert len(provider.spans) == 1
        assert provider.spans[0].name == SpanName.RUN_WITH_RETRY
        assert provider.spans[0].kind == "internal"


class TestEnableTracingResetsPrevious:
    """Second ``enable_tracing`` must replace the previous provider."""

    def test_double_enable_swaps_provider(self):
        first = RecordingProvider()
        second = RecordingProvider()

        enable_tracing(first)
        with create_ydb_span(SpanName.CREATE_SESSION, FakeDriverConfig()).attach_context():
            pass

        enable_tracing(second)  # reset
        assert get_active_provider() is second

        with create_ydb_span(SpanName.EXECUTE_QUERY, FakeDriverConfig()).attach_context():
            pass

        # The second provider only sees spans emitted after enable()
        assert [s.name for s in first.spans] == [SpanName.CREATE_SESSION]
        assert [s.name for s in second.spans] == [SpanName.EXECUTE_QUERY]

    def test_enable_none_is_disable(self):
        provider = RecordingProvider()
        enable_tracing(provider)
        assert _registry.is_active()

        enable_tracing(None)  # type: ignore[arg-type]
        assert _registry.is_active() is False
        assert get_active_provider() is None

    def test_disable_tracing_reverts_to_noop(self):
        provider = RecordingProvider()
        enable_tracing(provider)
        disable_tracing()

        assert _registry.is_active() is False
        with create_ydb_span(SpanName.EXECUTE_QUERY, FakeDriverConfig()).attach_context():
            pass

        # No spans reached the provider after disable
        assert provider.spans == []


class TestNoopProviderExplicit:
    def test_enabling_noop_provider_still_marks_registry_active(self):
        """A user explicitly picking NoopTracingProvider is a valid choice."""
        enable_tracing(NoopTracingProvider())
        assert _registry.is_active() is True
        # But the produced span is still a NoopSpan — no attributes recorded.
        span = create_ydb_span(SpanName.CREATE_SESSION, FakeDriverConfig())
        assert isinstance(span, NoopSpan)


class TestOtelEnableAlsoResets:
    """The OTel entrypoint must reset any previously enabled provider too."""

    def test_otel_enable_replaces_custom_provider(self):
        pytest.importorskip("opentelemetry")

        from ydb.opentelemetry import disable_tracing as otel_disable
        from ydb.opentelemetry import enable_tracing as otel_enable
        from ydb.opentelemetry.plugin import OtelTracingProvider

        custom = RecordingProvider()
        enable_tracing(custom)
        assert get_active_provider() is custom

        otel_enable()
        active = get_active_provider()
        assert isinstance(active, OtelTracingProvider)

        otel_disable()
        assert _registry.is_active() is False

    def test_second_otel_enable_swaps_the_tracer(self):
        pytest.importorskip("opentelemetry")

        from opentelemetry import trace

        from ydb.opentelemetry import disable_tracing as otel_disable
        from ydb.opentelemetry import enable_tracing as otel_enable

        try:
            otel_enable()
            first = get_active_provider()
            otel_enable(trace.get_tracer("ydb.sdk.custom"))
            second = get_active_provider()
            assert first is not second
        finally:
            otel_disable()


class TestProtocolContract:
    def test_protocol_can_be_satisfied_by_duck_typed_object(self):
        """A user-written provider does not need to inherit anything."""

        class MyProvider:
            def __init__(self):
                self.calls = 0

            def create_span(self, name, attributes=None, kind=None):
                self.calls += 1
                return NoopSpan()

            def get_trace_metadata(self):
                return ()

        provider: TracingProvider = MyProvider()  # runtime duck check
        enable_tracing(provider)

        with create_ydb_span(SpanName.EXECUTE_QUERY, FakeDriverConfig()).attach_context():
            pass

        assert provider.calls == 1
