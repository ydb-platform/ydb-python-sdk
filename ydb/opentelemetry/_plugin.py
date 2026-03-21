from contextlib import contextmanager

_MIN_OTEL_VERSION = "1.0.0"

_tracer = None
_enabled = False


def _check_dependencies():
    try:
        from opentelemetry.version import __version__ as otel_version
    except ImportError:
        raise ImportError(
            "OpenTelemetry packages are required for tracing support. "
            "Install them with: pip install ydb[tracing]"
        ) from None

    from packaging.version import Version

    if Version(otel_version) < Version(_MIN_OTEL_VERSION):
        raise ImportError(
            f"OpenTelemetry >= {_MIN_OTEL_VERSION} is required, "
            f"but {otel_version} is installed. "
            "Upgrade with: pip install ydb[tracing]"
        )


def _otel_metadata_hook():
    """Injects W3C Trace Context (traceparent/tracestate) into gRPC metadata."""
    from opentelemetry.propagate import inject

    headers = {}
    inject(headers)
    return list(headers.items())


@contextmanager
def _otel_span(name, attributes=None, kind=None):
    from opentelemetry import trace

    kind_map = {
        "client": trace.SpanKind.CLIENT,
        "internal": trace.SpanKind.INTERNAL,
    }
    otel_kind = kind_map.get(kind, trace.SpanKind.CLIENT)
    with _tracer.start_as_current_span(
        name,
        kind=otel_kind,
        attributes=attributes or {},
    ) as span:
        try:
            yield span
        except Exception as e:
            _otel_set_error(span, e)
            raise


def _otel_set_error(span, exception):
    """Records an exception on the span and sets ERROR status."""
    if span is None:
        return

    from opentelemetry.trace import StatusCode
    from ydb import issues

    attrs = {}
    if isinstance(exception, issues.Error):
        status_code = getattr(exception, "status", None)
        if status_code is not None:
            attrs["db.response.status_code"] = str(status_code)
            attrs["error.type"] = status_code.name
        else:
            attrs["error.type"] = type(exception).__qualname__
    else:
        attrs["error.type"] = type(exception).__qualname__

    span.set_attributes(attrs)
    span.set_status(StatusCode.ERROR, str(exception))
    span.record_exception(exception)


def _enable_tracing():
    global _enabled, _tracer

    if _enabled:
        return

    _check_dependencies()

    from opentelemetry import trace
    from ydb.opentelemetry.tracing import _registry

    _tracer = trace.get_tracer("ydb.sdk")
    _enabled = True
    _registry.set_metadata_hook(_otel_metadata_hook)
    _registry.set_span_factory(_otel_span)
