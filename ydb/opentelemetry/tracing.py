from contextlib import contextmanager


@contextmanager
def _noop_span(name, attributes=None, kind=None):
    yield None


class OtelTracingRegistry:
    """Singleton registry for OpenTelemetry tracing.

    Holds the span factory and metadata hook.
    By default everything is no-op until :func:`enable_tracing` is called
    from :mod:`ydb.opentelemetry`.
    """

    def __init__(self):
        self._metadata_hook = None
        self._span_factory = _noop_span

    def create_span(self, name, attributes=None, kind=None):
        """Create a tracing span (context manager)."""
        return self._span_factory(name, attributes, kind=kind)

    def get_trace_metadata(self):
        """Return tracing metadata (e.g. W3C traceparent) for gRPC calls."""
        if self._metadata_hook is not None:
            return self._metadata_hook()
        return []

    def set_metadata_hook(self, hook):
        """Set a hook that returns tracing metadata for gRPC calls.

        *hook* must be a callable returning a list of ``(key, value)`` tuples.
        """
        self._metadata_hook = hook

    def set_span_factory(self, factory):
        """Set a span factory for tracing SDK operations.

        *factory* must be a context-manager factory:
        ``factory(name, attributes, kind) -> context manager yielding span``.
        """
        self._span_factory = factory


_registry = OtelTracingRegistry()



def create_span(name, attributes=None, kind=None):
    """Create a tracing span via the global registry."""
    return _registry.create_span(name, attributes, kind)


def get_trace_metadata():
    """Return tracing metadata for gRPC calls."""
    return _registry.get_trace_metadata()


def create_ydb_span(name, driver_config, session_id=None, node_id=None, tx_id=None, kind=None):
    """Create a span pre-filled with standard YDB attributes.

    :param name: Span name (e.g. ``"ydb.ExecuteQuery"``).
    :param driver_config: :class:`ydb.DriverConfig` instance.
    :param session_id: Optional session ID.
    :param node_id: Optional node ID.
    :param tx_id: Optional transaction ID.
    :param kind: Optional span kind (``"client"`` or ``"internal"``).
    """
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
    return _registry.create_span(name, attributes=attrs, kind=kind)
