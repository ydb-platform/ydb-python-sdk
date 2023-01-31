import datetime
import typing
from dataclasses import dataclass, field
from typing import List, Union, Dict

from google.protobuf.message import Message

from ydb._topic_wrapper.common import OffsetsRange, IToProto, UpdateTokenRequest, UpdateTokenResponse, IFromProto
from google.protobuf.duration_pb2 import Duration as ProtoDuration

# Workaround for good autocomplete in IDE and universal import at runtime
if False:
    from ydb._grpc.v4.protos import ydb_topic_pb2
else:
    from ydb._grpc.common.protos import ydb_topic_pb2


class StreamReadMessage:
    @dataclass
    class PartitionSession:
        partition_session_id: int
        path: str
        partition_id: int

    @dataclass
    class InitRequest(IToProto):
        topics_read_settings: List["StreamReadMessage.InitRequest.TopicReadSettings"]
        consumer: str

        def to_proto(self) -> ydb_topic_pb2.StreamReadMessage.InitRequest:
            res = ydb_topic_pb2.StreamReadMessage.InitRequest()
            res.consumer = self.consumer
            for settings in self.topics_read_settings:
                res.topics_read_settings.append(settings.to_proto())
            return res

        @dataclass
        class TopicReadSettings(IToProto):
            path: str
            partition_ids: List[int] = field(default_factory=list)
            max_lag_seconds: Union[datetime.timedelta, None] = None
            read_from: Union[int, float, datetime.datetime, None] = None

            def to_proto(self) -> ydb_topic_pb2.StreamReadMessage.InitRequest.TopicReadSettings:
                res = ydb_topic_pb2.StreamReadMessage.InitRequest.TopicReadSettings()
                res.path = self.path
                res.partition_ids.extend(self.partition_ids)
                if self.max_lag_seconds is not None:
                    res.max_lag = ProtoDuration()
                    res.max_lag.FromTimedelta(self.max_lag_seconds)
                return res

    @dataclass
    class InitResponse(IFromProto):
        session_id: str

        @staticmethod
        def from_proto(msg: ydb_topic_pb2.StreamReadMessage.InitResponse) -> "StreamReadMessage.InitResponse":
            return StreamReadMessage.InitResponse(session_id=msg.session_id)

    @dataclass
    class ReadRequest:
        bytes_size: int

    @dataclass
    class ReadResponse:
        partition_data: List["PartitionData"]
        bytes_size: int

        @dataclass
        class MessageData:
            offset: int
            seq_no: int
            created_at: float  # unix timestamp
            data: bytes
            uncompresed_size: int
            message_group_id: str

        @dataclass
        class Batch:
            message_data: List["StreamReadMessage.ReadResponse.MessageData"]
            producer_id: str
            write_session_meta: Dict[str, str]
            codec: int
            written_at: float  # unix timestamp

        @dataclass
        class PartitionData:
            partition_session_id: int
            batches: List["StreamReadMessage.ReadResponse.Batch"]

    @dataclass
    class CommitOffsetRequest:
        commit_offsets: List["PartitionCommitOffset"]

        @dataclass
        class PartitionCommitOffset:
            partition_session_id: int
            offsets: List[OffsetsRange]

    @dataclass
    class CommitOffsetResponse:
        partitions_committed_offsets: List["PartitionCommittedOffset"]

        @dataclass
        class PartitionCommittedOffset:
            partition_session_id: int
            committed_offset: int

    @dataclass
    class PartitionSessionStatusRequest:
        partition_session_id: int

    @dataclass
    class PartitionSessionStatusResponse:
        partition_session_id: int
        partition_offsets: OffsetsRange
        committed_offset: int
        write_time_high_watermark: float

    @dataclass
    class StartPartitionSessionRequest:
        partition_session: "StreamReadMessage.PartitionSession"
        committed_offset: int
        partition_offsets: OffsetsRange

    @dataclass
    class StartPartitionSessionResponse:
        partition_session_id: int
        read_offset: int
        commit_offset: int

    @dataclass
    class StopPartitionSessionRequest:
        partition_session_id: int
        graceful: bool
        committed_offset: int

    @dataclass
    class StopPartitionSessionResponse:
        partition_session_id: int

    @dataclass
    class FromClient(IToProto):
        client_message: "ReaderMessagesFromClientToServer"

        def __init__(self, client_message: "ReaderMessagesFromClientToServer"):
            self.client_message = client_message

        def to_proto(self) -> ydb_topic_pb2.StreamReadMessage.FromClient:
            res = ydb_topic_pb2.StreamReadMessage.FromClient()
            if isinstance(self.client_message, StreamReadMessage.InitRequest):
                res.init_request.CopyFrom(self.client_message.to_proto())
            else:
                raise NotImplementedError()
            return res

    @dataclass
    class FromServer(IFromProto):
        server_message: "ReaderMessagesFromServerToClient"

        @staticmethod
        def from_proto(msg: ydb_topic_pb2.StreamReadMessage.FromServer) -> "StreamReadMessage.FromServer":
            mess_type = msg.WhichOneof("server_message")
            if mess_type == "init_response":
                return StreamReadMessage.FromServer(
                    server_message=StreamReadMessage.InitResponse.from_proto(msg.init_response),
                )

            # todo replace exception to log
            raise NotImplementedError()


ReaderMessagesFromClientToServer = Union[
    StreamReadMessage.InitRequest,
    StreamReadMessage.ReadRequest,
    StreamReadMessage.CommitOffsetRequest,
    StreamReadMessage.PartitionSessionStatusRequest,
    UpdateTokenRequest,
    StreamReadMessage.StartPartitionSessionResponse,
    StreamReadMessage.StopPartitionSessionResponse,
]

ReaderMessagesFromServerToClient = Union[
    StreamReadMessage.InitResponse,
    StreamReadMessage.ReadResponse,
    StreamReadMessage.CommitOffsetResponse,
    StreamReadMessage.PartitionSessionStatusResponse,
    UpdateTokenResponse,
    StreamReadMessage.StartPartitionSessionRequest,
    StreamReadMessage.StopPartitionSessionRequest,
]
