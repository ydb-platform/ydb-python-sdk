from .. import _utilities


class AsyncResponseContextIterator(_utilities.AsyncResponseIterator):
    async def __aenter__(self) -> "AsyncResponseContextIterator":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        async for _ in self:
            pass
