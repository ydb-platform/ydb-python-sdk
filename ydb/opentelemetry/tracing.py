"""Internal SDK tracing helpers and telemetry facade."""

import enum

from ydb.opentelemetry._endpoint import split_endpoint
from ydb.opentelemetry.metrics import _build_ydb_metrics_attrs, create_metrics_operation, is_metrics_enabled


class SpanName(str, enum.Enum):
    """Canonical span names used across the YDB SDK."""

    CREATE_SESSION = "ydb.CreateSession"
    EXECUTE_QUERY = "ydb.ExecuteQuery"
    BEGIN_TRANSACTION = "ydb.BeginTransaction"
    COMMIT = "ydb.Commit"
    ROLLBACK = "ydb.Rollback"
    DRIVER_INITIALIZE = "ydb.Driver.Initialize"
    RUN_WITH_RETRY = "ydb.RunWithRetry"
    TRY = "ydb.Try"


class _NoopCtx:
    __slots__ = ("_span",)

    def __init__(self, span):
        self._span = span

    def __enter__(self):
        return self._span

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


class _NoopSpan:
    """Span-compatible object used when tracing is disabled."""

    def set_error(self, exception):
        pass

    def set_attribute(self, key, value):
        pass

    def end(self):
        pass

    def attach_context(self, end_on_exit=True):
        return _NoopCtx(self)


_NOOP_SPAN = _NoopSpan()


class _TelemetryContext:
    """Attach tracing context and metrics lifecycle for one SDK operation."""

    def __init__(self, telemetry, span_context, metrics_context):
        self._telemetry = telemetry
        self._span_context = span_context
        self._metrics_context = metrics_context

    def __enter__(self):
        self._metrics_context.__enter__()
        self._span_context.__enter__()
        return self._telemetry

    def __exit__(self, exc_type, exc_val, exc_tb):
        span_result = self._span_context.__exit__(exc_type, exc_val, exc_tb)
        metrics_result = self._metrics_context.__exit__(exc_type, exc_val, exc_tb)
        return bool(span_result or metrics_result)


class _TelemetryOperation:
    """Span-like facade that forwards lifecycle events to tracing and metrics."""

    def __init__(self, span, metrics):
        self._span = span
        self._metrics = metrics

    def set_error(self, exception):
        self._span.set_error(exception)
        self._metrics.set_error(exception)

    def set_attribute(self, key, value):
        self._span.set_attribute(key, value)
        self._metrics.set_attribute(key, value)

    def end(self):
        self._span.end()
        self._metrics.end()

    def attach_context(self, end_on_exit=True):
        return _TelemetryContext(
            self,
            self._span.attach_context(end_on_exit=end_on_exit),
            self._metrics.attach_context(end_on_exit=end_on_exit),
        )


class OtelTracingRegistry:
    """Singleton registry for OpenTelemetry tracing.

    By default everything is no-op until :func:`~ydb.opentelemetry.enable_tracing` is called.
    """

    def __init__(self):
        self._metadata_hook = None
        self._create_span_func = None

    def is_active(self) -> bool:
        return self._create_span_func is not None

    def create_span(self, name, attributes=None, kind=None):
        if self._create_span_func is None:
            return _NOOP_SPAN
        return self._create_span_func(name, attributes, kind=kind)

    def get_trace_metadata(self):
        if self._metadata_hook is not None:
            return self._metadata_hook()
        return []

    def set_metadata_hook(self, hook):
        self._metadata_hook = hook

    def set_create_span(self, func):
        self._create_span_func = func


_registry = OtelTracingRegistry()


def get_trace_metadata():
    """Return tracing metadata for gRPC calls."""
    return _registry.get_trace_metadata()


def _build_ydb_tracing_attrs(driver_config, node_id=None, peer=None):
    host, port = split_endpoint(getattr(driver_config, "endpoint", None))
    attrs = {
        "db.system.name": "ydb",
        "db.namespace": getattr(driver_config, "database", None) or "",
        "server.address": host,
        "server.port": port,
    }
    if peer is not None:
        address, port_, location = peer
        if address is not None:
            attrs["network.peer.address"] = address
        if port_ is not None:
            attrs["network.peer.port"] = int(port_)
        if location:
            attrs["ydb.node.dc"] = location
    if node_id is not None:
        attrs["ydb.node.id"] = node_id
    return attrs


def create_span(name, attributes=None, kind="internal"):
    """Create a span with no YDB-specific attributes (used for SDK-internal operations)."""
    return _registry.create_span(name, attributes=attributes, kind=kind).attach_context()


def create_ydb_span(name, driver_config, node_id=None, kind=None, peer=None):
    """Create telemetry for one user-visible YDB client operation.

    Tracing receives full operation context, including peer/node details. Metrics
    receive only the stable labels defined for client operation metrics.
    """
    metrics_attrs = _build_ydb_metrics_attrs(driver_config) if is_metrics_enabled() else None
    tracing_attrs = _build_ydb_tracing_attrs(driver_config, node_id, peer)
    metrics = create_metrics_operation(name, metrics_attrs)
    return _TelemetryOperation(_registry.create_span(name, attributes=tracing_attrs, kind=kind), metrics)


def set_peer_attributes(span, peer):
    """Fill in network.peer.* and ydb.node.dc on an existing span once the peer is known."""
    if peer is None:
        return
    address, port, location = peer
    if address is not None:
        span.set_attribute("network.peer.address", address)
    if port is not None:
        span.set_attribute("network.peer.port", int(port))
    if location:
        span.set_attribute("ydb.node.dc", location)


def span_finish_callback(span):
    """Return an on_finish callable that ends *span* when a streaming result iterator completes."""

    def _finish(exception=None):
        if exception is not None:
            span.set_error(exception)
        span.end()

    return _finish
