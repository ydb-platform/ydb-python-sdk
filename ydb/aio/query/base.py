from .. import _utilities


class AsyncResponseContextIterator(_utilities.AsyncResponseIterator):
    """Async ExecuteQuery result stream; span + gRPC propagation token (see sync class doc)."""

    def __init__(self, it, wrapper, on_error=None, span=None, grpc_propagation_token=None):
        super().__init__(it, wrapper)
        self._on_error = on_error
        self._span = span
        self._grpc_propagation_token = grpc_propagation_token

    async def __aenter__(self) -> "AsyncResponseContextIterator":
        return self

    async def _next(self):
        try:
            return await super()._next()
        except StopAsyncIteration:
            self._finish_span()
            raise
        except Exception as e:
            if self._on_error:
                self._on_error(e)
            self._finish_span(e)
            raise e

    def _finish_span(self, exception=None):
        # Pop gRPC propagation before ending span (same contract as sync iterator).
        if self._grpc_propagation_token is not None:
            from ydb.opentelemetry.tracing import pop_otel_span_for_grpc

            pop_otel_span_for_grpc(self._grpc_propagation_token)
            self._grpc_propagation_token = None
        if self._span is not None:
            if exception is not None:
                self._span.set_error(exception)
            self._span.end()
            self._span = None

    def __del__(self):
        self._finish_span()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        #  To close stream on YDB it is necessary to scroll through it to the end
        async for _ in self:
            pass
        self._finish_span()
