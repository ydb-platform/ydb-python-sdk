import asyncio
import gc
import weakref

import pytest
import ydb


class Payload:
    def __init__(self):
        self.data = b"x" * 1024 * 1024


class BadRequestError(Exception):
    pass


class CException(Exception):
    # Simulate an exception that might not participate well in GC
    pass


@pytest.mark.asyncio
async def test_retry_operation_memory_leak():
    weak_refs = []

    async def my_coro():
        payload = Payload()
        weak_refs.append(weakref.ref(payload))

        # We simulate a reference cycle without relying on Pydantic's Rust-based errors.
        # By chaining exceptions, we build a traceback that points back to this frame.
        try:
            raise CException("inner")
        except CException as e:
            raise BadRequestError("bad request") from e

    try:
        await ydb.aio.retry_operation(my_coro)
    except BadRequestError:
        pass

    # Run the event loop briefly and trigger garbage collection
    for _ in range(3):
        await asyncio.sleep(0)
        gc.collect()

    # The payload should be garbage collected because the reference cycle
    # involving the generator yielded result, the traceback, and the local frame
    # was explicitly broken by setting result.exc = None in the retry implementation.
    assert not any(w() is not None for w in weak_refs)
