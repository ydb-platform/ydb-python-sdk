from opentelemetry import context, trace
from opentelemetry.propagate import inject
from opentelemetry.trace import StatusCode

from ydb import issues
from ydb.opentelemetry.tracing import _registry

_tracer = None
_enabled = False

_KIND_MAP = {
    "client": trace.SpanKind.CLIENT,
    "internal": trace.SpanKind.INTERNAL,
}


def _otel_metadata_hook():
    """Injects W3C Trace Context (traceparent/tracestate) into gRPC metadata."""
    headers = {}
    inject(headers)
    return list(headers.items())


def _set_error_on_span(span, exception):
    if isinstance(exception, issues.Error) and exception.status is not None:
        error_type = exception.status.name
        span.set_attribute("db.response.status_code", error_type)
    else:
        error_type = type(exception).__qualname__

    span.set_attribute("error.type", error_type)
    span.set_status(StatusCode.ERROR, str(exception))
    span.record_exception(exception)


class TracingSpan:
    """Wrapper around an OTel span that manages context lifecycle.

    Can be used as a context manager or manually
    """

    def __init__(self, span, token):
        self._span = span
        self._token = token

    def set_error(self, exception):
        _set_error_on_span(self._span, exception)

    def end(self):
        self._span.end()
        if self._token is not None:
            context.detach(self._token)
            self._token = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is not None:
            self.set_error(exc_val)
        self.end()
        return False


def _create_span(name, attributes=None, kind=None):
    # Can be used as a context manager or manually
    span = _tracer.start_span(
        name,
        kind=_KIND_MAP.get(kind, trace.SpanKind.CLIENT),
        attributes=attributes or {},
    )
    ctx = trace.set_span_in_context(span)
    token = context.attach(ctx)
    return TracingSpan(span, token)


def _enable_tracing():
    global _enabled, _tracer

    if _enabled:
        return

    _tracer = trace.get_tracer("ydb.sdk")
    _enabled = True
    _registry.set_metadata_hook(_otel_metadata_hook)
    _registry.set_create_span(_create_span)
