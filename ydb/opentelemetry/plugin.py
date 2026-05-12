"""OpenTelemetry bridge for YDB."""

from opentelemetry import context as otel_context
from opentelemetry import trace
from opentelemetry.metrics import Observation
from opentelemetry import metrics
from opentelemetry.propagate import inject
from opentelemetry.trace import StatusCode

from ydb import issues
from ydb.issues import StatusCode as YdbStatusCode
from ydb.opentelemetry import metrics

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
_tracing_enabled = False
_meter = None

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
    """Make a span the active OTel context for a ``with`` block.

    When ``end_on_exit=True`` (default) the span is ended on exit — used for
    single-shot RPCs. When ``end_on_exit=False`` the span is only ended on
    exception — used for streaming RPCs where the result iterator owns ``end()``.
    """

    def __init__(self, span, end_on_exit):
        self._span = span
        self._end_on_exit = end_on_exit
        self._token = None

    def __enter__(self):
        ctx = trace.set_span_in_context(self._span._span)
        self._token = otel_context.attach(ctx)
        return self._span

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._token is not None:
            otel_context.detach(self._token)
            self._token = None
        if exc_val is not None:
            self._span.set_error(exc_val)
            self._span.end()
        elif self._end_on_exit:
            self._span.end()
        return False


class TracingSpan:
    """Wrapper around an OTel span.

    Use :meth:`attach_context` as a context manager around any RPC call.
    The default (``end_on_exit=True``) is for single-shot operations; pass
    ``end_on_exit=False`` for streaming RPCs where the result iterator owns
    ``end()``.
    """

    def __init__(self, span):
        self._span = span

    def set_error(self, exception):
        _set_error_on_span(self._span, exception)

    def set_attribute(self, key, value):
        self._span.set_attribute(key, value)

    def end(self):
        self._span.end()

    def attach_context(self, end_on_exit=True):
        return _AttachContext(self, end_on_exit)


def _create_span(name, attributes=None, kind=None):
    span = _tracer.start_span(
        name,
        kind=_KIND_MAP.get(kind, trace.SpanKind.CLIENT),
        attributes=attributes or {},
    )
    return TracingSpan(span)


def _enable_tracing(tracer=None):
    global _tracing_enabled, _tracer

    if _tracing_enabled:
        return

    _tracer = tracer if tracer is not None else trace.get_tracer("ydb.sdk")
    _tracing_enabled = True
    _tracing_registry.set_metadata_hook(_otel_metadata_hook)
    _tracing_registry.set_create_span(_create_span)


def _disable_tracing():
    """Clear hooks and tracer; after this, :func:`~ydb.opentelemetry.enable_tracing` may be called again."""
    global _tracing_enabled, _tracer

    _tracing_registry.set_create_span(None)
    _tracing_registry.set_metadata_hook(None)
    _tracing_enabled = False
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
