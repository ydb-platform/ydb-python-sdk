def enable_tracing(tracer=None):
    """Enable OpenTelemetry trace context propagation and span creation for all YDB gRPC calls.

    Args:
        tracer: Optional OTel tracer to use. If not provided, the default tracer from the global tracer provider will be used.
    """
    try:
        from ydb.opentelemetry._plugin import _enable_tracing
    except ImportError:
        raise ImportError(
            "OpenTelemetry packages are required for tracing support. "
            "Install them with: pip install ydb[opentelemetry]"
        ) from None

    _enable_tracing(tracer)


__all__ = ["enable_tracing"]
