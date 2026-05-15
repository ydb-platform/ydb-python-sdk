"""Public OpenTelemetry entrypoints for YDB."""


def enable_tracing(tracer=None):
    """Enable OpenTelemetry trace context propagation and span creation for all YDB gRPC calls.

    This call is **idempotent**: if tracing is already enabled, later calls do nothing
    (including passing a different ``tracer``). Call :func:`disable_tracing` first to
    reconfigure or turn instrumentation off.

    Args:
        tracer: Optional OTel tracer to use. If not provided, the default tracer named
            ``ydb.sdk`` from the global tracer provider will be used.
    """
    try:
        from ydb.opentelemetry.plugin import _enable_tracing
    except ImportError:
        raise ImportError(
            "OpenTelemetry packages are required for tracing support. "
            "Install them with: pip install ydb[opentelemetry]"
        ) from None

    _enable_tracing(tracer)


def disable_tracing():
    """Disable YDB OpenTelemetry hooks and allow :func:`enable_tracing` to run again."""
    try:
        from ydb.opentelemetry.plugin import _disable_tracing
    except ImportError:
        return

    _disable_tracing()


def enable_metrics(meter_provider=None):
    """Enable OpenTelemetry metrics collection for YDB SDK client metrics.

    This call is **idempotent**: if metrics are already enabled, later calls do nothing
    (including passing a different ``meter_provider``). Call :func:`disable_metrics`
    first to reconfigure or turn instrumentation off.

    Args:
        meter_provider: Optional OTel meter provider to use. If not provided, the
            default meter named ``ydb.sdk`` from the global meter provider will be used.
    """
    try:
        from ydb.opentelemetry.plugin import _enable_metrics
    except ImportError:
        raise ImportError(
            "OpenTelemetry packages are required for metrics support. "
            "Install them with: pip install ydb[opentelemetry]"
        ) from None

    _enable_metrics(meter_provider)


def disable_metrics():
    """Disable YDB OpenTelemetry metrics collection and allow :func:`enable_metrics` to run again."""
    try:
        from ydb.opentelemetry.plugin import _disable_metrics
    except ImportError:
        return

    _disable_metrics()


__all__ = [
    "disable_tracing",
    "enable_tracing",
    "disable_metrics",
    "enable_metrics",
]
