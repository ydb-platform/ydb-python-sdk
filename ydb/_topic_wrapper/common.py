import abc
import asyncio
import queue
import typing
from dataclasses import dataclass
from enum import Enum

from google.protobuf.message import Message

import ydb.aio

# Workaround for good autocomplete in IDE and universal import at runtime
if False:
    from ydb._grpc.v4.protos import ydb_status_codes_pb2, ydb_issue_message_pb2, ydb_topic_pb2
else:
    # noinspection PyUnresolvedReferences
    from ydb._grpc.common.protos import ydb_status_codes_pb2, ydb_issue_message_pb2, ydb_topic_pb2


class Codec(Enum):
    CODEC_UNSPECIFIED = 0
    CODEC_RAW = 1
    CODEC_GZIP = 2
    CODEC_LZOP = 3
    CODEC_ZSTD = 4


@dataclass
class OffsetsRange:
    start: int
    end: int


class IToProto(abc.ABC):

    @abc.abstractmethod
    def to_proto(self) -> Message:
        pass


class UnknownGrpcMessageError(ydb.Error):
    pass


class IFromProto(abc.ABC):
    @staticmethod
    @abc.abstractmethod
    def from_proto(msg: Message) -> typing.Any:
        pass


class QueueToIteratorAsyncIO:
    __slots__ = ("_queue",)

    def __init__(self, q: asyncio.Queue):
        self._queue = q

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return await self._queue.get()
        except asyncio.QueueEmpty:
            raise StopAsyncIteration()


class AsyncQueueToSyncIteratorAsyncIO:
    __slots__ = (
        "_loop",
        "_queue",
    )
    _queue: asyncio.Queue

    def __init__(self, q: asyncio.Queue):
        self._loop = asyncio.get_running_loop()
        self._queue = q

    def __iter__(self):
        return self

    def __next__(self):
        try:
            res = asyncio.run_coroutine_threadsafe(self._queue.get(), self._loop).result()
            return res
        except asyncio.QueueEmpty:
            raise StopIteration()


class SyncIteratorToAsyncIterator:

    def __init__(self, sync_iterator: typing.Iterator):
        self._sync_iterator = sync_iterator

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            res = await asyncio.to_thread(self._sync_iterator.__next__)
            return res
        except StopAsyncIteration:
            raise StopIteration()


class IteratorToQueueAsyncIO:
    __slots__ = ("_iterator",)

    def __init__(self, iterator: typing.AsyncIterator[typing.Any]):
        self._iterator = iterator

    async def get(self) -> typing.Any:
        try:
            return anext(self._iterator)
        except StopAsyncIteration:
            raise asyncio.QueueEmpty()


class IGrpcWrapperAsyncIO(abc.ABC):
    @abc.abstractmethod
    async def receive(self) -> typing.Any: ...

    @abc.abstractmethod
    def write(self, wrap_message: IToProto): ...


SupportedDriverType = typing.Union[ydb.Driver, ydb.aio.Driver]


class GrpcWrapperAsyncIO(IGrpcWrapperAsyncIO):
    from_client_grpc: asyncio.Queue
    from_server_grpc: typing.AsyncIterator
    convert_server_grpc_to_wrapper: typing.Callable[[typing.Any], typing.Any]

    def __init__(self, convert_server_grpc_to_wrapper):
        self.from_client_grpc = asyncio.Queue()
        self.convert_server_grpc_to_wrapper = convert_server_grpc_to_wrapper

    async def start(self, driver: SupportedDriverType, stub, method):
        if asyncio.iscoroutinefunction(driver.__call__):
            await self._start_asyncio_driver(driver, stub, method)
        else:
            await self._start_sync_driver(driver, stub, method)

    async def _start_asyncio_driver(self, driver: ydb.aio.Driver, stub, method):
        requests_iterator = QueueToIteratorAsyncIO(self.from_client_grpc)
        stream_call = await driver(
            requests_iterator,
            stub,
            method,
        )
        self.from_server_grpc = stream_call.__aiter__()

    async def _start_sync_driver(self, driver: ydb.Driver, stub, method):
        requests_iterator = AsyncQueueToSyncIteratorAsyncIO(self.from_client_grpc)
        stream_call = await asyncio.to_thread(driver,
                                              requests_iterator,
                                              stub,
                                              method,
                                              )
        self.from_server_grpc = SyncIteratorToAsyncIterator(stream_call.__iter__())

    async def receive(self) -> typing.Any:
        # todo handle grpc exceptions and convert it to internal exceptions
        grpc_item = await self.from_server_grpc.__anext__()
        return self.convert_server_grpc_to_wrapper(grpc_item)

    def write(self, wrap_message: IToProto):
        self.from_client_grpc.put_nowait(wrap_message.to_proto())


@dataclass(init=False)
class ServerStatus(IFromProto):
    __slots__ = ("status", "_issues")

    def __init__(self,
                 status: ydb_status_codes_pb2.StatusIds.StatusCode,
                 issues: typing.Iterable[ydb_issue_message_pb2.IssueMessage]):
        self.status = status
        self._issues = issues

    def __str__(self):
        return self.__repr__()

    @staticmethod
    def from_proto(msg: Message) -> "ServerStatus":
        return ServerStatus(
            msg.status
        )

    def is_success(self) -> bool:
        return self.status == ydb_status_codes_pb2.StatusIds.SUCCESS

    @classmethod
    def issue_to_str(cls, issue: ydb_issue_message_pb2.IssueMessage):
        res = """code: %s message: "%s" """ % (issue.issue_code, issue.message)
        if len(issue.issues) > 0:
            d = ", "
            res += d + d.join(str(sub_issue) for sub_issue in issue.issues)
        return res


@dataclass
class UpdateTokenRequest(IToProto):
    token: str

    def to_proto(self) -> Message:
        res = ydb_topic_pb2.UpdateTokenRequest()
        res.token = self.token
        return res


@dataclass
class UpdateTokenResponse(IFromProto):
    @staticmethod
    def from_proto(msg: ydb_topic_pb2.UpdateTokenResponse) -> typing.Any:
        return UpdateTokenResponse()
