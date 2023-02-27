import asyncio
import time
import typing

from .._grpc.grpcwrapper.common_utils import IToProto, IGrpcWrapperAsyncIO


class StreamMock(IGrpcWrapperAsyncIO):
    from_server: asyncio.Queue
    from_client: asyncio.Queue
    _closed: bool

    def __init__(self):
        self.from_server = asyncio.Queue()
        self.from_client = asyncio.Queue()
        self._closed = False

    async def receive(self) -> typing.Any:
        if self._closed:
            raise Exception("read from closed StreamMock")

        item = await self.from_server.get()
        if item is None:
            raise StopAsyncIteration()
        if isinstance(item, Exception):
            raise item
        return item

    def write(self, wrap_message: IToProto):
        if self._closed:
            raise Exception("write to closed StreamMock")
        self.from_client.put_nowait(wrap_message)

    def close(self):
        if self._closed:
            return

        self._closed = True
        self.from_server.put_nowait(None)


async def wait_condition(f: typing.Callable[[], bool], timeout=1):
    start = time.monotonic()
    counter = 0
    while (time.monotonic() - start < timeout) or counter < 1000:
        counter += 1
        if f():
            return
        await asyncio.sleep(0)

    raise Exception("Bad condition in test")


async def wait_for_fast(fut):
    return await asyncio.wait_for(fut, 1)
