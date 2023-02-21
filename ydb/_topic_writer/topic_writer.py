from __future__ import annotations

import datetime
import enum
from dataclasses import dataclass
from enum import Enum
from typing import List, Union, TextIO, BinaryIO, Optional, Callable, Mapping, Any, Dict

import typing

import ydb.aio
from .._grpc.grpcwrapper.ydb_topic import Codec, StreamWriteMessage
from .._grpc.grpcwrapper.common_utils import IToProto


@dataclass
class PublicWriterSettings:
    topic: str
    producer_and_message_group_id: str
    session_metadata: Optional[Dict[str, str]] = None
    encoders: Union[Mapping[int, Callable[[bytes], bytes]], None] = None
    serializer: Union[Callable[[Any], bytes], None] = None
    send_buffer_count: Optional[int] = 10000
    send_buffer_bytes: Optional[int] = 100 * 1024 * 1024
    partition_id: Optional[int] = None
    codec: Optional[int] = None
    codec_autoselect: bool = True
    auto_seqno: bool = True
    auto_created_at: bool = True
    get_last_seqno: bool = False
    retry_policy: Optional["RetryPolicy"] = None
    update_token_interval: Union[int, float] = 3600


@dataclass
class PublicWriteResult:
    @dataclass(eq=True)
    class Written:
        __slots__ = "offset"
        offset: int

    @dataclass(eq=True)
    class Skipped:
        pass


PublicWriteResultTypes = Union[PublicWriteResult.Written, PublicWriteResult.Skipped]


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
        return StreamWriteMessage.PartitioningMessageGroupID(
            self.producer_and_message_group_id
        )


class SendMode(Enum):
    ASYNC = 1
    SYNC = 2


@dataclass
class PublicWriterInitInfo:
    __slots__ = "last_seqno"
    last_seqno: Optional[int]


class PublicMessage:
    seqno: Optional[int]
    created_at: Optional[datetime.datetime]
    data: Union[str, bytes, TextIO, BinaryIO]

    SimpleMessageSourceType = Union[str, bytes]

    def __init__(
        self,
        data: SimpleMessageSourceType,
        *,
        seqno: Optional[int] = None,
        created_at: Optional[datetime.datetime] = None,
    ):
        self.seqno = seqno
        self.created_at = created_at
        self.data = data

    def _get_data_bytes(self) -> bytes:
        if isinstance(self.data, bytes):
            return self.data
        if isinstance(self.data, str):
            return self.data.encode()

        raise ValueError("Bad data type: %s" % type(self.data))

    @staticmethod
    def _to_message(data: "MessageType") -> PublicMessage:
        if isinstance(data, PublicMessage):
            return data
        return PublicMessage(data)


MessageType = typing.Union["PublicMessage", "PublicMessage.SimpleMessageSourceType"]


class InternalMessage(StreamWriteMessage.WriteRequest.MessageData, IToProto):
    def __init__(self, mess: PublicMessage):
        StreamWriteMessage.WriteRequest.MessageData.__init__(
            self,
            seq_no=mess.seqno,
            created_at=mess.created_at,
            data=mess._get_data_bytes(),
            uncompressed_size=len(mess.data),
            partitioning=None,
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
        data = self.data
        return StreamWriteMessage.WriteRequest.MessageData(
            seq_no=self.seq_no,
            created_at=self.created_at,
            data=data,
            uncompressed_size=len(data),
            partitioning=None,  # unsupported by server now
        )


class MessageSendResult:
    offset: Optional[int]
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
        super(TopicWriterStopped, self).__init__(
            "topic writer was stopped by call close"
        )


def default_serializer_message_content(data: Any) -> bytes:
    if data is None:
        return bytes()
    if isinstance(data, bytes):
        return data
    if isinstance(data, bytearray):
        return bytes(data)
    if isinstance(data, str):
        return data.encode(encoding="utf-8")
    raise ValueError("can't serialize type %s to bytes" % type(data))


def messages_to_proto_requests(
    messages: List[InternalMessage],
) -> List[StreamWriteMessage.FromClient]:
    # todo split by proto message size and codec
    res = []
    for msg in messages:
        req = StreamWriteMessage.FromClient(
            StreamWriteMessage.WriteRequest(
                messages=[msg.to_message_data()],
                codec=Codec.CODEC_RAW,
            )
        )
        res.append(req)
    return res
