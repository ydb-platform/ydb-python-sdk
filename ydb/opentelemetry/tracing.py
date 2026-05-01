"""OpenTelemetry helpers and registry (PR #786 review).

- **ContextVar ``_OTEL_SPAN_FOR_GRPC``:** holds the SDK span used for W3C ``inject`` on
  gRPC metadata without keeping ``context.attach`` for the whole ExecuteQuery stream
  (review: vgvoleg). Bound from ``push_otel_span_for_grpc`` until the result iterator
  finishes (full execute lifecycle for propagation).

- **``create_ydb_span`` early return:** avoids building attribute dicts when tracing is
  off so the path stays no-op (review: vgvoleg — docs promise zero-cost when disabled).

- **``_split_endpoint``:** strips ``grpc://`` / ``grpcs://`` and supports ``[ipv6]:port``
  so ``server.address`` matches semantic conventions (review: vgvoleg).
"""

import contextvars
from typing import Any, Optional, Tuple

_OTEL_SPAN_FOR_GRPC: contextvars.ContextVar[Optional[Any]] = contextvars.ContextVar(
    "_OTEL_SPAN_FOR_GRPC",
    default=None,
)


def get_active_grpc_otel_span():
    """OpenTelemetry SDK span used for W3C inject on the next gRPC metadata build, if any."""
    return _OTEL_SPAN_FOR_GRPC.get()


def push_otel_span_for_grpc(wrapped_span) -> Optional[contextvars.Token]:
    """Bind ``wrapped_span`` (TracingSpan from _plugin) for the next gRPC metadata build.

    Returns a token for :func:`pop_otel_span_for_grpc`, or ``None`` if nothing was pushed.
    """
    if wrapped_span is None:
        return None
    raw = getattr(wrapped_span, "_span", None)
    if raw is None:
        return None
    return _OTEL_SPAN_FOR_GRPC.set(raw)


def pop_otel_span_for_grpc(token: Optional[contextvars.Token]) -> None:
    if token is not None:
        _OTEL_SPAN_FOR_GRPC.reset(token)


class _NoopSpan:
    """Returned by create_ydb_span when tracing is disabled."""

    def set_error(self, exception):
        pass

    def set_attribute(self, key, value):
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

    By default everything is no-op until :func:`~ydb.opentelemetry.enable_tracing` is called.
    """

    def __init__(self):
        self._metadata_hook = None
        self._create_span_func = None

    def is_active(self) -> bool:
        return self._create_span_func is not None

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


def _split_endpoint(endpoint: Optional[str]) -> Tuple[str, int]:
    """Split ``host:port`` for OTel ``server.*`` attributes (no ``grpc://`` prefix; IPv6-safe)."""
    ep = endpoint or ""
    if ep.startswith("grpcs://"):
        ep = ep[len("grpcs://") :]
    elif ep.startswith("grpc://"):
        ep = ep[len("grpc://") :]

    if ep.startswith("["):
        close = ep.find("]")
        if close != -1 and len(ep) > close + 1 and ep[close + 1] == ":":
            host = ep[: close + 1]
            port_s = ep[close + 2 :]
            return host, int(port_s) if port_s.isdigit() else 0

    host, _, port_s = ep.rpartition(":")
    return host, int(port_s) if port_s.isdigit() else 0


def _build_ydb_attrs(driver_config, node_id=None, peer=None):
    host, port = _split_endpoint(getattr(driver_config, "endpoint", None))
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
        attrs["ydb.node.id"] = node_id or 0
    return attrs


def create_ydb_span(name, driver_config, node_id=None, kind=None, peer=None):
    """Create a span pre-filled with standard YDB attributes.

    ``peer`` is a ``(address, port, location)`` tuple pulled from the endpoint
    map for the specific node serving the call; missing fields are skipped.
    Can be used as a context manager or manually.
    """
    # Review (vgvoleg): skip _build_ydb_attrs when hooks are unset (zero-cost when disabled).
    if not _registry.is_active():
        return _NOOP_SPAN
    attrs = _build_ydb_attrs(driver_config, node_id, peer)
    return _registry.create_span(name, attributes=attrs, kind=kind)


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
