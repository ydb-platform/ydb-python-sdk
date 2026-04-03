class _NoopSpan:
    """Returned by create_ydb_span when tracing is disabled."""

    def set_error(self, exception):
        pass

    def end(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


_NOOP_SPAN = _NoopSpan()


class OtelTracingRegistry:
    """Singleton registry for OpenTelemetry tracing.

    By default everything is no-op until :func:`enable_tracing` is called.
    """

    def __init__(self):
        self._metadata_hook = None
        self._create_span_func = None

    def create_span(self, name, attributes=None, kind=None):
        """Create a span. Returns a TracingSpan or _NoopSpan."""
        if self._create_span_func is None:
            return _NOOP_SPAN
        return self._create_span_func(name, attributes, kind=kind)

    def get_trace_metadata(self):
        """Return tracing metadata (e.g. W3C traceparent) for gRPC calls."""
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


def _build_ydb_attrs(driver_config, session_id=None, node_id=None, tx_id=None):
    endpoint = getattr(driver_config, "endpoint", None) or ""
    host, _, port = endpoint.rpartition(":")
    attrs = {
        "db.system.name": "ydb",
        "db.namespace": getattr(driver_config, "database", None) or "",
        "server.address": host,
        "server.port": int(port) if port.isdigit() else 0,
    }
    if session_id is not None:
        attrs["ydb.session.id"] = session_id or ""
    if node_id is not None:
        attrs["ydb.node.id"] = node_id or 0
    if tx_id is not None:
        attrs["ydb.tx.id"] = tx_id or ""
    return attrs


def create_ydb_span(name, driver_config, session_id=None, node_id=None, tx_id=None, kind=None):
    """Create a span pre-filled with standard YDB attributes.
    Can be used as a context manager or manually.
    """
    attrs = _build_ydb_attrs(driver_config, session_id, node_id, tx_id)
    return _registry.create_span(name, attributes=attrs, kind=kind)
