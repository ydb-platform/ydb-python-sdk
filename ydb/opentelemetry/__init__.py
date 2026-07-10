"""Public OpenTelemetry entrypoints for YDB.

For vendor-neutral tracing (custom providers, Noop, interfaces) see
:mod:`ydb.observability`. This module is a convenience wrapper that constructs
an OpenTelemetry-backed provider and installs it via
:func:`ydb.observability.enable_tracing`.
"""


def enable_tracing(tracer=None):
    """Enable OpenTelemetry trace context propagation and span creation for all YDB gRPC calls.

    Any previously installed tracing provider (custom or OTel) is replaced —
    calling this a second time is safe and simply swaps the tracer.

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


__all__ = ["disable_tracing", "enable_tracing"]
