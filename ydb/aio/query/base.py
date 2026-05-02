from .. import _utilities


class AsyncResponseContextIterator(_utilities.AsyncResponseIterator):
    """Async ExecuteQuery result stream; ends the attached OTel span when consumed."""

    def __init__(self, it, wrapper, on_error=None, span=None):
        super().__init__(it, wrapper)
        self._on_error = on_error
        self._span = span

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
        if self._span is not None:
            if exception is not None:
                self._span.set_error(exception)
            self._span.end()
            self._span = None

    def __del__(self):
        if self._span is not None:
            self._span.end()
            self._span = None

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
