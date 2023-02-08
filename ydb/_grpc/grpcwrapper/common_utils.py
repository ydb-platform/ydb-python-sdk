import abc
import asyncio
import typing
from dataclasses import dataclass

import grpc
from google.protobuf.message import Message

import ydb.aio

# Workaround for good IDE and universal for runtime
# noinspection PyUnreachableCode
if False:
    from ..v4.protos import ydb_topic_pb2, ydb_issue_message_pb2
else:
    from ..common.protos import ydb_topic_pb2, ydb_issue_message_pb2

from ... import issues, connection


class IFromProto(abc.ABC):
    @staticmethod
    @abc.abstractmethod
    def from_proto(msg: Message) -> typing.Any:
        pass


class IToProto(abc.ABC):
    @abc.abstractmethod
    def to_proto(self) -> Message:
        pass


class UnknownGrpcMessageError(issues.Error):
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
            res = asyncio.run_coroutine_threadsafe(
                self._queue.get(), self._loop
            ).result()
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


class IGrpcWrapperAsyncIO(abc.ABC):
    @abc.abstractmethod
    async def receive(self) -> typing.Any:
        ...

    @abc.abstractmethod
    def write(self, wrap_message: IToProto):
        ...


SupportedDriverType = typing.Union[ydb.Driver, ydb.aio.Driver]


class GrpcWrapperAsyncIO(IGrpcWrapperAsyncIO):
    from_client_grpc: asyncio.Queue
    from_server_grpc: typing.AsyncIterator
    convert_server_grpc_to_wrapper: typing.Callable[[typing.Any], typing.Any]
    _connection_state: str

    def __init__(self, convert_server_grpc_to_wrapper):
        self.from_client_grpc = asyncio.Queue()
        self.convert_server_grpc_to_wrapper = convert_server_grpc_to_wrapper
        self._connection_state = "new"

    async def start(self, driver: SupportedDriverType, stub, method):
        if asyncio.iscoroutinefunction(driver.__call__):
            await self._start_asyncio_driver(driver, stub, method)
        else:
            await self._start_sync_driver(driver, stub, method)
        self._connection_state = "started"

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
        stream_call = await asyncio.to_thread(
            driver,
            requests_iterator,
            stub,
            method,
        )
        self.from_server_grpc = SyncIteratorToAsyncIterator(stream_call.__iter__())

    async def receive(self) -> typing.Any:
        # todo handle grpc exceptions and convert it to internal exceptions
        try:
            grpc_message = await self.from_server_grpc.__anext__()
        except grpc.RpcError as e:
            raise connection._rpc_error_handler(self._connection_state, e)

        issues._process_response(grpc_message)

        if self._connection_state != "has_received_messages":
            self._connection_state = "has_received_messages"

        # print("rekby, grpc, received", grpc_message)
        return self.convert_server_grpc_to_wrapper(grpc_message)

    def write(self, wrap_message: IToProto):
        grpc_message = wrap_message.to_proto()
        # print("rekby, grpc, send", grpc_message)
        self.from_client_grpc.put_nowait(grpc_message)


@dataclass(init=False)
class ServerStatus(IFromProto):
    __slots__ = ("_grpc_status_code", "_issues")

    def __init__(
        self,
        status: issues.StatusCode,
        issues: typing.Iterable[typing.Any],
    ):
        self.status = status
        self.issues = issues

    def __str__(self):
        return self.__repr__()

    @staticmethod
    def from_proto(
        msg: typing.Union[
            ydb_topic_pb2.StreamReadMessage.FromServer,
            ydb_topic_pb2.StreamWriteMessage.FromServer,
        ]
    ) -> "ServerStatus":
        return ServerStatus(msg.status, msg.issues)

    def is_success(self) -> bool:
        return self.status == issues.StatusCode.SUCCESS

    @classmethod
    def issue_to_str(cls, issue: ydb_issue_message_pb2.IssueMessage):
        res = """code: %s message: "%s" """ % (issue.issue_code, issue.message)
        if len(issue.issues) > 0:
            d = ", "
            res += d + d.join(str(sub_issue) for sub_issue in issue.issues)
        return res


def callback_from_asyncio(
    callback: typing.Union[typing.Callable, typing.Coroutine]
) -> [asyncio.Future, asyncio.Task]:
    loop = asyncio.get_running_loop()

    if asyncio.iscoroutinefunction(callback):
        return loop.create_task(callback())
    else:
        return loop.run_in_executor(None, callback)
