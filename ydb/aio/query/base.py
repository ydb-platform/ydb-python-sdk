from .. import _utilities


class AsyncResponseContextIterator(_utilities.AsyncResponseIterator):
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
            self._finish_span()
            raise
        except Exception as e:
            if self._on_error:
                self._on_error(e)
            self._finish_span(e)
            raise e

    def _finish_span(self, exception=None):
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
