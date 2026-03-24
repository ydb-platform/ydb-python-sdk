def enable_tracing():
    """Enable OpenTelemetry trace context propagation and span creation for all YDB gRPC calls."""
    try:
        from ydb.opentelemetry._plugin import _enable_tracing
    except ImportError:
        raise ImportError(
            "OpenTelemetry packages are required for tracing support. " "Install them with: pip install ydb[tracing]"
        ) from None

    _enable_tracing()


__all__ = ["enable_tracing"]
