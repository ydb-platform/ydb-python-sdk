def enable_tracing():
    """Enable OpenTelemetry trace context propagation and span creation for all YDB gRPC calls."""
    from ydb.opentelemetry._plugin import _enable_tracing

    _enable_tracing()


__all__ = ["enable_tracing"]
