import asyncio
import time
import typing

from .._grpc.grpcwrapper.common_utils import IToProto, IGrpcWrapperAsyncIO


class StreamMock(IGrpcWrapperAsyncIO):
    from_server: asyncio.Queue
    from_client: asyncio.Queue

    def __init__(self):
        self.from_server = asyncio.Queue()
        self.from_client = asyncio.Queue()

    async def receive(self) -> typing.Any:
        item = await self.from_server.get()
        if isinstance(item, Exception):
            raise item
        return item

    def write(self, wrap_message: IToProto):
        self.from_client.put_nowait(wrap_message)


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
