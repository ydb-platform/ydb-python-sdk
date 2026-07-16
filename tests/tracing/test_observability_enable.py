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
    _build_ydb_attrs,
    _registry,
    _split_endpoint,
    create_span,
    create_ydb_span,
    get_trace_metadata,
    set_peer_attributes,
    span_finish_callback,
)

from ydb.ydb_version import VERSION

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


class TestPublicOtelProviderExport:
    """``OtelTracingProvider`` is part of the public ``ydb.opentelemetry`` namespace."""

    def test_provider_is_exported_from_package_root(self):
        pytest.importorskip("opentelemetry")

        import ydb.opentelemetry as otel
        from ydb.opentelemetry.plugin import OtelTracingProvider

        assert otel.OtelTracingProvider is OtelTracingProvider
        assert "OtelTracingProvider" in otel.__all__

    def test_exported_provider_plugs_into_vendor_neutral_enable(self):
        pytest.importorskip("opentelemetry")

        from ydb.opentelemetry import OtelTracingProvider

        try:
            enable_tracing(OtelTracingProvider())
            assert isinstance(get_active_provider(), OtelTracingProvider)
        finally:
            disable_tracing()

    def test_unknown_attribute_still_raises(self):
        import ydb.opentelemetry as otel

        with pytest.raises(AttributeError):
            otel.does_not_exist


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


class _BuildInfoCfg:
    database = None
    credentials = None


class TestSdkBuildInfoHeader:
    """Enabling tracing advertises a ``ydb-sdk-tracing`` token in x-ydb-sdk-build-info."""

    def test_tokens_reflect_active_provider(self):
        from ydb.observability import sdk_build_info_tokens

        assert sdk_build_info_tokens() == []
        enable_tracing(RecordingProvider())
        assert sdk_build_info_tokens() == ["ydb-sdk-tracing/0.1.0"]
        disable_tracing()
        assert sdk_build_info_tokens() == []

    def test_header_gains_tracing_token_when_enabled(self):
        from ydb.connection import _construct_metadata

        def build_info():
            return dict(_construct_metadata(_BuildInfoCfg(), None))["x-ydb-sdk-build-info"]

        assert "ydb-sdk-tracing" not in build_info()

        enable_tracing(RecordingProvider())
        header = build_info()
        disable_tracing()

        assert header == f"ydb-python-sdk/{VERSION};ydb-sdk-tracing/0.1.0"

    def test_tracing_token_precedes_driver_additional_headers(self):
        from ydb.connection import _construct_metadata

        class _Cfg(_BuildInfoCfg):
            _additional_sdk_headers = ("lib1/1.0",)

        enable_tracing(RecordingProvider())
        header = dict(_construct_metadata(_Cfg(), None))["x-ydb-sdk-build-info"]
        disable_tracing()

        # native SDK, then SDK-owned tracing token, then custom driver headers
        assert header == f"ydb-python-sdk/{VERSION};ydb-sdk-tracing/0.1.0;lib1/1.0"

    async def test_header_async_parity(self):
        from ydb.aio.connection import _construct_metadata

        enable_tracing(RecordingProvider())
        header = dict(await _construct_metadata(_BuildInfoCfg(), None))["x-ydb-sdk-build-info"]
        disable_tracing()

        assert header == f"ydb-python-sdk/{VERSION};ydb-sdk-tracing/0.1.0"


class TestSplitEndpoint:
    """Cover every branch of the endpoint parser."""

    @pytest.mark.parametrize(
        "endpoint,expected",
        [
            # ``grpcs://`` scheme is stripped before parsing.
            ("grpcs://secure.example.com:2136", ("secure.example.com", 2136)),
            # ``grpc://`` scheme is stripped before parsing.
            ("grpc://plain.example.com:2136", ("plain.example.com", 2136)),
            # Bare host:port with no scheme.
            ("host.example.com:2136", ("host.example.com", 2136)),
            # Bracketed IPv6 with port — the fast path.
            ("[::1]:2136", ("[::1]", 2136)),
            ("[fe80::1]:8080", ("[fe80::1]", 8080)),
            # A leading ``[`` with no closing ``]:`` falls through to rpartition.
            ("[malformed", ("[malformed", 0)),
            # No colon at all → whole string is host, port is 0.
            ("no_colon_at_all", ("no_colon_at_all", 0)),
            # Non-numeric port defaults to 0.
            ("host:not_a_port", ("host", 0)),
            # ``None`` is normalized to an empty string.
            (None, ("", 0)),
        ],
    )
    def test_parses(self, endpoint, expected):
        assert _split_endpoint(endpoint) == expected


class TestBuildYdbAttrsPeerOptionals:
    """Peer tuple may carry ``None`` in any position — each field is optional."""

    def test_peer_with_only_address(self):
        cfg = FakeDriverConfig()
        attrs = _build_ydb_attrs(cfg, peer=("only.host", None, None))
        assert attrs["network.peer.address"] == "only.host"
        assert "network.peer.port" not in attrs
        assert "ydb.node.dc" not in attrs

    def test_peer_with_only_port(self):
        cfg = FakeDriverConfig()
        attrs = _build_ydb_attrs(cfg, peer=(None, 2137, None))
        assert "network.peer.address" not in attrs
        assert attrs["network.peer.port"] == 2137
        assert "ydb.node.dc" not in attrs

    def test_peer_with_only_location(self):
        cfg = FakeDriverConfig()
        attrs = _build_ydb_attrs(cfg, peer=(None, None, "dc-north"))
        assert "network.peer.address" not in attrs
        assert "network.peer.port" not in attrs
        assert attrs["ydb.node.dc"] == "dc-north"

    def test_peer_with_empty_location(self):
        cfg = FakeDriverConfig()
        attrs = _build_ydb_attrs(cfg, peer=("h", 1, ""))
        assert "ydb.node.dc" not in attrs


class TestSetPeerAttributes:
    """Direct unit tests for ``set_peer_attributes``."""

    def _recording_span(self):
        recorded: Dict[str, Any] = {}

        class _Span:
            def set_attribute(self, key, value):
                recorded[key] = value

        return _Span(), recorded

    def test_peer_none_is_noop(self):
        span, recorded = self._recording_span()
        set_peer_attributes(span, None)
        assert recorded == {}

    def test_full_peer_records_all_three(self):
        span, recorded = self._recording_span()
        set_peer_attributes(span, ("node-1.example", 2136, "dc-a"))
        assert recorded == {
            "network.peer.address": "node-1.example",
            "network.peer.port": 2136,
            "ydb.node.dc": "dc-a",
        }

    def test_partial_peer_skips_missing_fields(self):
        span, recorded = self._recording_span()
        set_peer_attributes(span, (None, None, ""))
        assert recorded == {}

    def test_port_coerced_to_int(self):
        span, recorded = self._recording_span()
        set_peer_attributes(span, ("h", "2137", "dc"))
        assert recorded["network.peer.port"] == 2137


class TestSpanFinishCallback:
    """``span_finish_callback`` wires stream completion into span lifecycle."""

    def test_finish_ends_span_on_success(self):
        calls: List[str] = []

        class _Span:
            def set_error(self, exc):
                calls.append(f"error:{exc}")

            def end(self):
                calls.append("end")

        span_finish_callback(_Span())()
        assert calls == ["end"]

    def test_finish_records_error_then_ends_span(self):
        calls: List[str] = []
        exc = RuntimeError("stream broke")

        class _Span:
            def set_error(self, e):
                calls.append(f"error:{e}")

            def end(self):
                calls.append("end")

        span_finish_callback(_Span())(exc)
        assert calls == [f"error:{exc}", "end"]


class TestOpentelemetryTracingShimReexports:
    """``ydb.opentelemetry.tracing`` must expose the same public surface as before the split."""

    def test_shim_reexports_are_identity(self):
        from ydb import observability
        from ydb.observability import tracing as obs_tracing
        from ydb.opentelemetry import tracing as otel_shim

        assert otel_shim.NoopSpan is observability.NoopSpan
        assert otel_shim.NoopTracingProvider is observability.NoopTracingProvider
        assert otel_shim.Span is observability.Span
        assert otel_shim.SpanName is observability.SpanName
        assert otel_shim.TracingProvider is observability.TracingProvider
        assert otel_shim.create_span is obs_tracing.create_span
        assert otel_shim.create_ydb_span is obs_tracing.create_ydb_span
        assert otel_shim.get_trace_metadata is obs_tracing.get_trace_metadata
        assert otel_shim.set_peer_attributes is obs_tracing.set_peer_attributes
        assert otel_shim.span_finish_callback is obs_tracing.span_finish_callback
        assert otel_shim._registry is obs_tracing._registry
        assert otel_shim._build_ydb_attrs is obs_tracing._build_ydb_attrs
        assert otel_shim._split_endpoint is obs_tracing._split_endpoint
        assert otel_shim._NoopCtx is obs_tracing._NoopCtx
        # Legacy private aliases used by very old callers.
        assert otel_shim._NoopSpan is observability.NoopSpan
        assert otel_shim._NOOP_SPAN is observability.NoopTracingProvider._SPAN


class TestOtelEntrypointHandlesMissingPackage:
    """``ydb.opentelemetry.enable_tracing`` must raise a clear error if OTel isn't importable."""

    def test_enable_raises_when_plugin_import_fails(self, monkeypatch):
        import sys

        # Block the plugin import — this is how missing OTel would manifest.
        monkeypatch.setitem(sys.modules, "ydb.opentelemetry.plugin", None)

        from ydb.opentelemetry import enable_tracing as otel_enable

        with pytest.raises(ImportError, match="OpenTelemetry"):
            otel_enable()

    def test_disable_is_noop_when_plugin_import_fails(self, monkeypatch):
        import sys

        monkeypatch.setitem(sys.modules, "ydb.opentelemetry.plugin", None)

        from ydb.opentelemetry import disable_tracing as otel_disable

        # Must not raise — silent fallback is documented behavior.
        otel_disable()


class TestOtelTracingSpanBridge:
    """Cover the ``TracingSpan`` wrapper directly (no SDK glue)."""

    def test_set_attribute_forwards_to_underlying_otel_span(self):
        pytest.importorskip("opentelemetry")

        from ydb.opentelemetry.plugin import TracingSpan

        recorded: Dict[str, Any] = {}

        class _FakeOtelSpan:
            def set_attribute(self, key, value):
                recorded[key] = value

            def end(self):
                recorded["ended"] = True

        wrapped = TracingSpan(_FakeOtelSpan())
        wrapped.set_attribute("db.system.name", "ydb")
        wrapped.end()

        assert recorded == {"db.system.name": "ydb", "ended": True}

    def test_attach_context_exit_without_enter_is_safe(self):
        """Defensive path: ``__exit__`` before a successful ``__enter__``.

        This can happen if ``__enter__`` raises before ``_token`` is assigned;
        we must not detach a ``None`` token, but we should still end the span.
        """
        pytest.importorskip("opentelemetry")

        from ydb.opentelemetry.plugin import TracingSpan, _AttachContext

        ended = {"n": 0}

        class _FakeOtelSpan:
            def end(self):
                ended["n"] += 1

            def set_attribute(self, k, v):
                pass

        ctx = _AttachContext(TracingSpan(_FakeOtelSpan()), end_on_exit=True)
        # ``_token`` stays ``None`` — mimics the "__enter__ never ran" case.
        assert ctx._token is None
        ctx.__exit__(None, None, None)
        assert ended["n"] == 1


class TestNoopContextManager:
    """The Noop provider's ``attach_context`` must be a well-formed context manager."""

    def test_noop_ctx_yields_span_and_swallows_no_exceptions(self):
        span = NoopSpan()
        ctx = span.attach_context()
        with ctx as inner:
            assert inner is span
        # A second entry after exit must still work — noop stays idempotent.
        with span.attach_context() as inner:
            inner.set_attribute("k", "v")
            inner.set_error(RuntimeError("x"))
            inner.end()

    def test_noop_provider_returns_shared_span_and_empty_metadata(self):
        provider = NoopTracingProvider()
        assert provider.create_span("x") is NoopTracingProvider._SPAN
        assert tuple(provider.get_trace_metadata()) == ()
