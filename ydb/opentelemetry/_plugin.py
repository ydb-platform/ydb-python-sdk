"""OpenTelemetry bridge for YDB (PR #786 review follow-ups).

Review themes addressed here:

- **error.type vs YDB status:** map ``issues.Error.status`` to ``transport_error`` vs
  ``ydb_error`` using the client transport status band (``_TRANSPORT_STATUSES``), not the
  status name as ``error.type`` (review: KirillKurdyukov).

- **No long-lived ``context.attach`` on streaming execute:** attaching for the whole
  result iterator + detaching from ``__del__`` or another task caused OTel warnings
  (review: vgvoleg). ``ExecuteQuery`` uses ``tracing.push_otel_span_for_grpc`` with a
  token cleared in the iterator ``_finish_span``; ``TracingSpan.end()`` never detaches.

- **Explicit ``inject`` context:** when the ContextVar is set, ``inject`` uses
  ``trace.set_span_in_context(otel_span)`` instead of relying on global attach for the
  stream lifetime (review: vgvoleg).

- **Tracer / reset:** ``enable_tracing(tracer=...)`` is idempotent; ``disable_tracing()``
  clears hooks so tracing can be reconfigured (review: vgvoleg / KirillKurdyukov).
"""

from opentelemetry import context as otel_context
from opentelemetry import trace
from opentelemetry.propagate import inject
from opentelemetry.trace import StatusCode

from ydb import issues
from ydb.issues import StatusCode as YdbStatusCode
from ydb.opentelemetry.tracing import _registry, get_active_grpc_otel_span

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
_enabled = False

_KIND_MAP = {
    "client": trace.SpanKind.CLIENT,
    "internal": trace.SpanKind.INTERNAL,
}


def _otel_metadata_hook():
    """Injects W3C Trace Context (traceparent/tracestate) into gRPC metadata.

    When ``get_active_grpc_otel_span()`` is set (ExecuteQuery / with-blocks), inject
    uses that span explicitly so we do not depend on OTel ``context.attach`` for the
    whole stream (PR review: vgvoleg).
    """
    headers = {}
    otel_span = get_active_grpc_otel_span()
    if otel_span is not None:
        inject(headers, context=trace.set_span_in_context(otel_span))
    else:
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


class TracingSpan:
    """Wrapper around an OTel span.

    **With-blocks** (CreateSession, Commit, RunWithRetry, …): ``__enter__`` does a
    *short* ``context.attach`` for the block so child spans (e.g. ``ydb.Try``) get the
    correct parent; ``__exit__`` detaches and ends the span (review: vgvoleg — attach
    must not outlive the block / stream).

    **ExecuteQuery** does not use this context manager: the caller holds
    ``push_otel_span_for_grpc`` until the result iterator finishes (see
    ``SyncResponseContextIterator``); :meth:`end` does not call ``context.detach``.
    """

    def __init__(self, span):
        self._span = span
        self._grpc_propagation_token = None
        self._otel_context_token = None

    def set_error(self, exception):
        _set_error_on_span(self._span, exception)

    def set_attribute(self, key, value):
        self._span.set_attribute(key, value)

    def end(self):
        self._span.end()

    def __enter__(self):
        from ydb.opentelemetry.tracing import push_otel_span_for_grpc

        ctx = trace.set_span_in_context(self._span)
        self._otel_context_token = otel_context.attach(ctx)
        self._grpc_propagation_token = push_otel_span_for_grpc(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        from ydb.opentelemetry.tracing import pop_otel_span_for_grpc

        pop_otel_span_for_grpc(self._grpc_propagation_token)
        self._grpc_propagation_token = None
        if self._otel_context_token is not None:
            otel_context.detach(self._otel_context_token)
            self._otel_context_token = None
        if exc_val is not None:
            self.set_error(exc_val)
        self.end()
        return False


def _create_span(name, attributes=None, kind=None):
    span = _tracer.start_span(
        name,
        kind=_KIND_MAP.get(kind, trace.SpanKind.CLIENT),
        attributes=attributes or {},
    )
    return TracingSpan(span)


def _enable_tracing(tracer=None):
    global _enabled, _tracer

    if _enabled:
        return

    _tracer = tracer if tracer is not None else trace.get_tracer("ydb.sdk")
    _enabled = True
    _registry.set_metadata_hook(_otel_metadata_hook)
    _registry.set_create_span(_create_span)


def _disable_tracing():
    """Clear hooks and tracer; after this, :func:`~ydb.opentelemetry.enable_tracing` may be called again.

    Review (vgvoleg): ``enable_tracing()`` is idempotent; callers need an explicit way
    to reset hooks / pass a new tracer without reaching into private module state.
    """
    global _enabled, _tracer

    _registry.set_create_span(None)
    _registry.set_metadata_hook(None)
    _enabled = False
    _tracer = None
