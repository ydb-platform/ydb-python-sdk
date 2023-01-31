import asyncio
import typing

from .common import IGrpcWrapperAsyncIO, IToProto


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
