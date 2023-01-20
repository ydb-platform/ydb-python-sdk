import asyncio
import concurrent.futures
import datetime
import enum
import time
from dataclasses import dataclass
from enum import Enum
from typing import List, Union, TextIO, BinaryIO, Optional, Callable, Mapping, Any, Dict

import typing

import ydb.aio
from .._topic_wrapper.common import IToProto, Codec
from .._topic_wrapper.writer import StreamWriteMessage


class Writer:
    @property
    def last_seqno(self) -> int:
        raise NotImplemented()

    def __init__(self, db: ydb.Driver):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        pass

    MessageType = typing.Union["PublicMessage", "Message.SimpleMessageSourceType"]

    def write(self, message: Union[MessageType, List[MessageType]], *args: Optional[MessageType],
              timeout: [float, None] = None):
        """
        send one or number of messages to server.
        it fast put message to internal buffer, without wait message result
        return None

        message will send independent of wait/no wait result

        timeout - time for waiting for put message into internal queue.
            if 0 or negative - non block calls
            if None or not set - infinite wait
            It will raise TimeoutError() exception if it can't put message to internal queue by limits during timeout.
        """
        raise NotImplementedError()

    def async_write_with_ack(self, message: Union[MessageType, List[MessageType]], *args: Optional[MessageType],
                             timeout: [float, None] = None) -> concurrent.futures.Future:
        """
        send one or number of messages to server.
        return feature, which can be waited for check send result: ack/duplicate/error

        Usually it is fast method, but can wait if internal buffer is full.

        timeout - time for waiting for put message into internal queue.
            The method can be blocked up to timeout seconds before return future.

            if 0 or negative - non block calls
            if None or not set - infinite wait
            It will raise TimeoutError() exception if it can't put message to internal queue by limits during timeout.
        """
        raise NotImplementedError()

    def write_with_ack(self, message: Union[MessageType, List[MessageType]], *args: Optional[MessageType],
                       buffer_timeout: [float, None] = None) -> Union[
        "MessageWriteStatus", List["MessageWriteStatus"]]:
        """
        IT IS SLOWLY WAY. IT IS BAD CHOISE IN MOST CASES.
        It is recommended to use write with optionally flush or async_write_with_ack and receive acks by wait future.

        send one or number of messages to server.
        blocked until receive server ack for the message/messages.

        message will send independent of wait/no wait result

        buffer_timeout - time for send message to server and receive ack.
            if 0 or negative - non block calls
            if None or not set - infinite wait
            It will raise TimeoutError() exception if it isn't receive ack in timeout
        """
        raise NotImplementedError()

    def async_flush(self):
        """
        Force send all messages from internal buffer and wait acks from server for all
        messages.

        flush starts of flush process, and return Future for wait result.
        messages will be flushed independent of future waiting.
        """
        raise NotImplementedError()

    def flush(self, timeout: Union[float, None] = None) -> concurrent.futures.Future:
        """
        Force send all messages from internal buffer and wait acks from server for all
        messages.

        timeout - time for waiting for send all messages and receive server ack.
            if 0 or negative - non block calls
            if None or not set - infinite wait
            It will raise TimeoutError() exception if it isn't receive ack in timeout
        """
        raise NotImplementedError()

    def async_wait_init(self) -> concurrent.futures.Future:
        """
        Return feature, which done when underling connection established
        """
        raise NotImplementedError()

    def wait_init(self, timeout: Union[float, None] = None):
        """
        Wait until underling connection established

        timeout - time for waiting for send all messages and receive server ack.
            if 0 or negative - non block calls
            if None or not set - infinite wait
            It will raise TimeoutError() exception if it isn't receive ack in timeout
        """
        raise NotImplementedError()


@dataclass
class PublicWriterSettings:
    topic: str
    producer_and_message_group_id: str
    session_metadata: Optional[Dict[str, str]] = None
    encoders: Union[Mapping[int, Callable[[bytes], bytes]], None] = None
    serializer: Union[Callable[[Any], bytes], None] = None
    send_buffer_count: Union[int, None] = 10000
    send_buffer_bytes: Union[int, None] = 100 * 1024 * 1024
    partition_id: Optional[int] = None
    codec: Union[int, None] = None
    codec_autoselect: bool = True
    auto_seqno: bool = True
    auto_created_at: bool = True
    get_last_seqno: bool = False
    retry_policy: Union["RetryPolicy", None] = None
    update_token_interval: Union[int, float] = 3600


@dataclass
class PublicWriteResult:
    @dataclass(eq=True)
    class Written:
        __slots__ = (
            "offset"
        )
        offset: int

    @dataclass(eq=True)
    class Skipped:
        pass


class WriterSettings(PublicWriterSettings):
    def __init__(self, settings: PublicWriterSettings):
        self.__dict__ = settings.__dict__.copy()

    def create_init_request(self) -> StreamWriteMessage.InitRequest:
        return StreamWriteMessage.InitRequest(
            path=self.topic,
            producer_id=self.producer_and_message_group_id,
            write_session_meta=self.session_metadata,
            partitioning=self.get_partitioning(),
            get_last_seq_no=self.get_last_seqno,
        )

    def get_partitioning(self) -> StreamWriteMessage.PartitioningType:
        if self.partition_id is not None:
            return StreamWriteMessage.PartitioningPartitionID(self.partition_id)
        return StreamWriteMessage.PartitioningMessageGroupID(self.producer_and_message_group_id)


class SendMode(Enum):
    ASYNC = 1
    SYNC = 2


@dataclass
class PublicWriterInitInfo:
    __slots__ = (
        "last_seqno"
    )
    last_seqno: Optional[int]


class PublicMessage:
    seqno: Optional[int]
    created_at: Optional[datetime.datetime]
    data: Union[str, bytes, TextIO, BinaryIO]

    SimpleMessageSourceType = Union[str, bytes, TextIO, BinaryIO]

    def __init__(self,
                 data: SimpleMessageSourceType, *,
                 seqno: Optional[int] = None,
                 created_at: Optional[datetime.datetime] = None,
                 ):
        self.seqno = seqno
        self.created_at = created_at
        self.data = data


class InternalMessage(StreamWriteMessage.WriteRequest.MessageData, IToProto):
    def __init__(self, mess: PublicMessage):
        StreamWriteMessage.WriteRequest.MessageData.__init__(
            self,
            seq_no=mess.seqno,
            created_at=mess.created_at,
            data=mess.data,
            uncompressed_size=len(mess.data),
            partitioning = None,
        )

    def get_bytes(self) -> bytes:
        if self.data is None:
            return bytes()
        if isinstance(self.data, bytes):
            return self.data
        if isinstance(self.data, str):
            return self.data.encode("utf-8")
        raise ValueError("Bad data type")

    def to_message_data(self) -> StreamWriteMessage.WriteRequest.MessageData:
        data = self.get_bytes()
        return StreamWriteMessage.WriteRequest.MessageData(
            seq_no=self.seq_no,
            created_at=self.created_at,
            data=data,
            uncompressed_size=len(data),
            partitioning=None,  # unsupported by server now
        )


class MessageSendResult:
    offset: Union[None, int]
    write_status: "MessageWriteStatus"


class MessageWriteStatus(enum.Enum):
    Written = 1
    AlreadyWritten = 2


class RetryPolicy:
    connection_timeout_sec: float
    overload_timeout_sec: float
    retry_access_denied: bool = False


class TopicWriterError(ydb.Error):
    def __init__(self, message: str):
        super(TopicWriterError, self).__init__(message)


class TopicWriterRepeatableError(TopicWriterError):
    pass


class TopicWriterStopped(TopicWriterError):
    def __init__(self):
        super(TopicWriterStopped, self).__init__("topic writer was stopped by call close")


def default_serializer_message_content(data: Any) -> bytes:
    if data is None:
        return bytes()
    if isinstance(data, bytes):
        return data
    if isinstance(data, bytearray):
        return bytes(data)
    if isinstance(data, str):
        return data.encode(encoding='utf-8')
    raise ValueError("can't serialize type %s to bytes" % type(data))


def messages_to_proto_requests(messages: List[InternalMessage]) -> List[StreamWriteMessage.FromClient]:
    # todo split by proto message size and codec
    res = []
    for msg in messages:
        req = StreamWriteMessage.FromClient(
            StreamWriteMessage.WriteRequest(
                messages=[msg.to_message_data()],
                codec=Codec.CODEC_RAW.value,
            )
        )
        res.append(req)
    return res
