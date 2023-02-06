import abc
import concurrent.futures
import enum
import io
import datetime
from dataclasses import dataclass
from typing import (
    Union,
    Optional,
    List,
    Mapping,
    Callable,
    Iterable,
    AsyncIterable,
    AsyncContextManager,
    Any, Dict,
)

from ydb import RetrySettings
from ydb._topic_wrapper.common import OffsetsRange, TokenGetterFuncType
from ydb._topic_wrapper.reader import StreamReadMessage


class Selector:
    path: str
    partitions: Union[None, int, List[int]]
    read_from_timestamp_ms: Optional[int]
    max_time_lag_ms: Optional[int]

    def __init__(self, path, *, partitions: Union[None, int, List[int]] = None):
        self.path = path
        self.partitions = partitions


class ReaderAsyncIO(object):
    async def __aenter__(self):
        raise NotImplementedError()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        raise NotImplementedError()

    async def sessions_stat(self) -> List["SessionStat"]:
        """
        Receive stat from the server

        use asyncio.wait_for for wait with timeout.
        """
        raise NotImplementedError()

    def messages(
        self, *, timeout: Union[float, None] = None
    ) -> AsyncIterable["PublicMessage"]:
        """
        Block until receive new message

        if no new messages in timeout seconds: stop iteration by raise StopAsyncIteration
        """
        raise NotImplementedError()

    async def receive_message(self) -> Union["PublicMessage", None]:
        """
        Block until receive new message

        use asyncio.wait_for for wait with timeout.
        """
        raise NotImplementedError()

    def batches(
        self,
        *,
        max_messages: Union[int, None] = None,
        max_bytes: Union[int, None] = None,
        timeout: Union[float, None] = None,
    ) -> AsyncIterable["PublicBatch"]:
        """
        Block until receive new batch.
        All messages in a batch from same partition.

        if no new message in timeout seconds (default - infinite): stop iterations by raise StopIteration
        """
        raise NotImplementedError()

    async def receive_batch(
        self, *, max_messages: Union[int, None] = None, max_bytes: Union[int, None]
    ) -> Union["PublicBatch", None]:
        """
        Get one messages batch from reader.
        All messages in a batch from same partition.

        use asyncio.wait_for for wait with timeout.
        """
        raise NotImplementedError()

    async def commit_on_exit(self, mess: "ICommittable") -> AsyncContextManager:
        """
        commit the mess match/message if exit from context manager without exceptions

        reader will close if exit from context manager with exception
        """
        raise NotImplementedError()

    def commit(self, mess: "ICommittable"):
        """
        Write commit message to a buffer.

        For the method no way check the commit result
        (for example if lost connection - commits will not re-send and committed messages will receive again)
        """
        raise NotImplementedError()

    async def commit_with_ack(
        self, mess: "ICommittable"
    ) -> Union["CommitResult", List["CommitResult"]]:
        """
        write commit message to a buffer and wait ack from the server.

        use asyncio.wait_for for wait with timeout.
        """
        raise NotImplementedError()

    async def flush(self):
        """
        force send all commit messages from internal buffers to server and wait acks for all of them.

        use asyncio.wait_for for wait with timeout.
        """
        raise NotImplementedError()

    async def close(self):
        raise NotImplementedError()


class Reader(object):
    def async_sessions_stat(self) -> concurrent.futures.Future:
        """
        Receive stat from the server, return feature.
        """
        raise NotImplementedError()

    async def sessions_stat(self) -> List["SessionStat"]:
        """
        Receive stat from the server

        use async_sessions_stat for set explicit wait timeout
        """
        raise NotImplementedError()

    def messages(self, *, timeout: Union[float, None] = None) -> Iterable["PublicMessage"]:
        """
        todo?

        Block until receive new message
        It has no async_ version for prevent lost messages, use async_wait_message as signal for new batches available.

        if no new message in timeout seconds (default - infinite): stop iterations by raise StopIteration
        if timeout <= 0 - it will fast non block method, get messages from internal buffer only.
        """
        raise NotImplementedError()

    def receive_message(self, *, timeout: Union[float, None] = None) -> "PublicMessage":
        """
        Block until receive new message
        It has no async_ version for prevent lost messages, use async_wait_message as signal for new batches available.

        if no new message in timeout seconds (default - infinite): raise TimeoutError()
        if timeout <= 0 - it will fast non block method, get messages from internal buffer only.
        """
        raise NotImplementedError()

    def async_wait_message(self) -> concurrent.futures.Future:
        """
        Return future, which will completed when the reader has least one message in queue.
        If reader already has message - future will return completed.

        Possible situation when receive signal about message available, but no messages when try to receive a message.
        If message expired between send event and try to retrieve message (for example connection broken).
        """
        raise NotImplementedError()

    def batches(
        self,
        *,
        max_messages: Union[int, None] = None,
        max_bytes: Union[int, None] = None,
        timeout: Union[float, None] = None,
    ) -> Iterable["PublicBatch"]:
        """
        Block until receive new batch.
        It has no async_ version for prevent lost messages, use async_wait_message as signal for new batches available.

        if no new message in timeout seconds (default - infinite): stop iterations by raise StopIteration
        if timeout <= 0 - it will fast non block method, get messages from internal buffer only.
        """
        raise NotImplementedError()

    def receive_batch(
        self,
        *,
        max_messages: Union[int, None] = None,
        max_bytes: Union[int, None],
        timeout: Union[float, None] = None,
    ) -> Union["PublicBatch", None]:
        """
        Get one messages batch from reader
        It has no async_ version for prevent lost messages, use async_wait_message as signal for new batches available.

        if no new message in timeout seconds (default - infinite): raise TimeoutError()
        if timeout <= 0 - it will fast non block method, get messages from internal buffer only.
        """
        raise NotImplementedError()

    def commit(self, mess: "ICommittable"):
        """
        Put commit message to internal buffer.

        For the method no way check the commit result
        (for example if lost connection - commits will not re-send and committed messages will receive again)
        """
        raise NotImplementedError()

    def commit_with_ack(
        self, mess: "ICommittable"
    ) -> Union["CommitResult", List["CommitResult"]]:
        """
        write commit message to a buffer and wait ack from the server.

        if receive in timeout seconds (default - infinite): raise TimeoutError()
        """
        raise NotImplementedError()

    def async_commit_with_ack(
        self, mess: "ICommittable"
    ) -> Union["CommitResult", List["CommitResult"]]:
        """
        write commit message to a buffer and return Future for wait result.
        """
        raise NotImplementedError()

    def async_flush(self) -> concurrent.futures.Future:
        """
        force send all commit messages from internal buffers to server and return Future for wait server acks.
        """
        raise NotImplementedError()

    def flush(self):
        """
        force send all commit messages from internal buffers to server and wait acks for all of them.
        """
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()


@dataclass
class PublicReaderSettings:
    consumer: str
    topic: str
    buffer_size_bytes: int = 50 * 1024 * 1024
    _token_getter: Optional[TokenGetterFuncType] = None
    # on_commit: Callable[["Events.OnCommit"], None] = None
    # on_get_partition_start_offset: Callable[
    #     ["Events.OnPartitionGetStartOffsetRequest"],
    #     "Events.OnPartitionGetStartOffsetResponse",
    # ] = None
    # on_partition_session_start: Callable[["StubEvent"], None] = None
    # on_partition_session_stop: Callable[["StubEvent"], None] = None
    # on_partition_session_close: Callable[["StubEvent"], None] = None  # todo?
    # decoder: Union[Mapping[int, Callable[[bytes], bytes]], None] = None
    # deserializer: Union[Callable[[bytes], Any], None] = None
    # one_attempt_connection_timeout: Union[float, None] = 1
    # connection_timeout: Union[float, None] = None
    # retry_policy: Union["RetryPolicy", None] = None

    def _init_message(self) -> StreamReadMessage.InitRequest:
        return StreamReadMessage.InitRequest(
            topics_read_settings=[
                StreamReadMessage.InitRequest.TopicReadSettings(
                    path=self.topic,
                )
            ],
            consumer=self.consumer,
        )

    def _retry_settings(self)->RetrySettings:
        return RetrySettings(idempotent=True)


class Events:
    class OnCommit:
        topic: str
        offset: int

    class OnPartitionGetStartOffsetRequest:
        topic: str
        partition_id: int

    class OnPartitionGetStartOffsetResponse:
        start_offset: int

    class OnInitPartition:
        pass

    class OnShutdownPatition:
        pass


class RetryPolicy:
    connection_timeout_sec: float
    overload_timeout_sec: float
    retry_access_denied: bool = False


class CommitResult:
    topic: str
    partition: int
    offset: int
    state: "CommitResult.State"
    details: str  # for humans only, content messages may be change in any time

    class State(enum.Enum):
        UNSENT = 1  # commit didn't send to the server
        SENT = 2  # commit was sent to server, but ack hasn't received
        ACKED = 3  # ack from server is received


class SessionStat:
    path: str
    partition_id: str
    partition_offsets: OffsetsRange
    committed_offset: int
    write_time_high_watermark: datetime.datetime
    write_time_high_watermark_timestamp_nano: int


class StubEvent:
    pass
