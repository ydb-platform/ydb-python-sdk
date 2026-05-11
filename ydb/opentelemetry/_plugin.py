"""OpenTelemetry bridge for YDB."""

from opentelemetry import context as otel_context
from opentelemetry import metrics
from opentelemetry import trace
from opentelemetry.propagate import inject
from opentelemetry.trace import StatusCode
from opentelemetry.metrics import Observation

from ydb import issues
from ydb.issues import StatusCode as YdbStatusCode
from ydb.opentelemetry.metrics import _metrics_registry, create_metrics_operation
from ydb.opentelemetry.tracing import _registry as _tracing_registry

# YDB client transport StatusCode values (401xxx band) -> OTel error.type transport_error.
_TRANSPORT_STATUSES = frozenset(
    {
        YdbStatusCode.CONNECTION_LOST,
        YdbStatusCode.CONNECTION_FAILURE,
        YdbStatusCode.DEADLINE_EXCEEDED,
        YdbStatusCode.CLIENT_INTERNAL_ERROR,
        YdbStatusCode.UNIMPLEMENTED,
    }
)

_tracer = None
_meter = None
_enabled = False

_KIND_MAP = {
    "client": trace.SpanKind.CLIENT,
    "internal": trace.SpanKind.INTERNAL,
}


def _otel_metadata_hook():
    """Inject W3C Trace Context into outgoing gRPC metadata using the active OTel context."""
    headers = {}
    inject(headers)
    return list(headers.items())


def _set_error_on_span(span, exception):
    if isinstance(exception, issues.Error) and exception.status is not None:
        span.set_attribute("db.response.status_code", exception.status.name)
        error_type = "transport_error" if exception.status in _TRANSPORT_STATUSES else "ydb_error"
    else:
        error_type = type(exception).__qualname__

    span.set_attribute("error.type", error_type)
    span.set_status(StatusCode.ERROR, str(exception))
    span.record_exception(exception)


class _AttachContext:
    """Make a span the active OTel context for a ``with`` block, without ending it.

    Used around the initial gRPC call of a streaming RPC: the span outlives the
    ``with`` block — the result iterator owns ``end()``. For non-streaming RPCs
    use ``with create_ydb_span(...)`` directly.
    """

    def __init__(self, raw_span):
        self._raw = raw_span
        self._token = None

    def __enter__(self):
        ctx = trace.set_span_in_context(self._raw)
        self._token = otel_context.attach(ctx)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._token is not None:
            otel_context.detach(self._token)
            self._token = None
        return False


class TracingSpan:
    """Wrapper around an OTel span.

    As context manager: ``__enter__`` attaches the OTel context (so child spans
    nest correctly and ``inject()`` sees this span when building gRPC metadata)
    and ``__exit__`` detaches and ends the span. Used by Commit / Rollback /
    RunWithRetry / Try and similar single-shot operations.

    For ExecuteQuery streams the span outlives the ``with`` block: call
    :meth:`attach_context` around the initial gRPC call only, and let the result
    iterator own ``end()``.
    """

    def __init__(self, span, name, attributes):
        self._span = span
        self._otel_context_token = None
        self._metrics_operation = create_metrics_operation(name, attributes)

    def set_error(self, exception):
        _set_error_on_span(self._span, exception)
        self._metrics_operation.set_error(exception)

    def set_attribute(self, key, value):
        self._span.set_attribute(key, value)
        self._metrics_operation.set_attribute(key, value)

    def end(self):
        self._span.end()
        self._metrics_operation.end()

    def attach_context(self):
        return _AttachContext(self._span)

    def __enter__(self):
        ctx = trace.set_span_in_context(self._span)
        self._otel_context_token = otel_context.attach(ctx)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._otel_context_token is not None:
            otel_context.detach(self._otel_context_token)
            self._otel_context_token = None
        if exc_val is not None:
            self.set_error(exc_val)
        self.end()
        return False


def _create_span(name, attributes=None, kind=None):
    attrs = attributes or {}
    span = _tracer.start_span(
        name,
        kind=_KIND_MAP.get(kind, trace.SpanKind.CLIENT),
        attributes=attrs,
    )
    return TracingSpan(span, name, attrs)


def _enable_tracing(tracer=None):
    global _enabled, _tracer

    if _enabled:
        return

    _tracer = tracer if tracer is not None else trace.get_tracer("ydb.sdk")
    _enabled = True
    _tracing_registry.set_metadata_hook(_otel_metadata_hook)
    _tracing_registry.set_create_span(_create_span)


def _disable_tracing():
    """Clear hooks and tracer; after this, :func:`~ydb.opentelemetry.enable_tracing` may be called again."""
    global _enabled, _tracer

    _tracing_registry.set_create_span(None)
    _tracing_registry.set_metadata_hook(None)
    _enabled = False
    _tracer = None


def _create_query_session_count_callback():
    """Create callback for observable query session count metric."""

    def observe_query_session_count(_):
        values = _metrics_registry.get_query_session_count_values()
        return [Observation(value, attributes=dict(attrs)) for attrs, value in values.items()]

    return observe_query_session_count


def _enable_metrics(meter_provider):
    global _meter

    if _meter is not None:
        return

    if meter_provider is None:
        _meter = metrics.get_meter("ydb.sdk")
    elif hasattr(meter_provider, "get_meter"):
        _meter = meter_provider.get_meter("ydb.sdk")
    else:
        raise TypeError("meter_provider must be an OpenTelemetry MeterProvider")

    _metrics_registry.set_meter(_meter, _create_query_session_count_callback())


def _disable_metrics():
    global _meter

    _metrics_registry.clear()
    if _meter is not None:
        _meter = None
