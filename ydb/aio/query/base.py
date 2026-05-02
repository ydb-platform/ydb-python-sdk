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
            # Normal stream termination is not an error and must not invalidate
            # the session.
            self._finish_span()
            raise
        except BaseException as e:
            # BaseException (not Exception) because asyncio.CancelledError
            # inherits from BaseException in Python 3.8+. A stream interrupted
            # by a cancel must also be reported to _on_error so the session can
            # be invalidated; otherwise the next caller that picks this session
            # out of the pool races the undrained stream and the server can
            # reply with SessionBusy.
            if self._on_error:
                self._on_error(e)
            self._finish_span(e)
            raise

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
        # See sync iterator: GC may run in a different ContextVar context, where
        # ``reset(token)`` would raise ValueError. End the span only.
        if self._span is not None:
            self._span.end()
            self._span = None
        self._grpc_propagation_token = None

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        #  To close stream on YDB it is necessary to scroll through it to the end.
        # Errors that happen during the cleanup drain have already been reported
        # to _on_error inside _next, so swallow them here — re-raising from
        # __aexit__ would mask whatever exception is already propagating out of
        # the `async with` body and would leave callers (e.g. the tx __aexit__)
        # unable to run their own cleanup (rollback).
        try:
            async for _ in self:
                pass
        except BaseException:
            pass
        self._finish_span()
