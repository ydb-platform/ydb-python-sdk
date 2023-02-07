import datetime
from dataclasses import dataclass, field
from typing import List, Union, Dict

from ydb._topic_wrapper.common import (
    OffsetsRange,
    IToProto,
    UpdateTokenRequest,
    UpdateTokenResponse,
    IFromProto,
    ServerStatus,
)
from google.protobuf.duration_pb2 import Duration as ProtoDuration

# Workaround for good autocomplete in IDE and universal import at runtime
# noinspection PyUnreachableCode
if False:
    from ydb._grpc.v4.protos import ydb_topic_pb2
else:
    from ydb._grpc.common.protos import ydb_topic_pb2


class StreamReadMessage:
    @dataclass
    class PartitionSession(IFromProto):
        partition_session_id: int
        path: str
        partition_id: int

        @staticmethod
        def from_proto(
            msg: ydb_topic_pb2.StreamReadMessage.PartitionSession,
        ) -> "StreamReadMessage.PartitionSession":
            return StreamReadMessage.PartitionSession(
                partition_session_id=msg.partition_session_id,
                path=msg.path,
                partition_id=msg.partition_id,
            )

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

            def to_proto(
                self,
            ) -> ydb_topic_pb2.StreamReadMessage.InitRequest.TopicReadSettings:
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
        def from_proto(
            msg: ydb_topic_pb2.StreamReadMessage.InitResponse,
        ) -> "StreamReadMessage.InitResponse":
            return StreamReadMessage.InitResponse(session_id=msg.session_id)

    @dataclass
    class ReadRequest(IToProto):
        bytes_size: int

        def to_proto(self) -> ydb_topic_pb2.StreamReadMessage.ReadRequest:
            res = ydb_topic_pb2.StreamReadMessage.ReadRequest()
            res.bytes_size = self.bytes_size
            return res

    @dataclass
    class ReadResponse(IFromProto):
        partition_data: List["StreamReadMessage.ReadResponse.PartitionData"]
        bytes_size: int

        @staticmethod
        def from_proto(
            msg: ydb_topic_pb2.StreamReadMessage.ReadResponse,
        ) -> "StreamReadMessage.ReadResponse":
            partition_data = []
            for proto_partition_data in msg.partition_data:
                partition_data.append(
                    StreamReadMessage.ReadResponse.PartitionData.from_proto(
                        proto_partition_data
                    )
                )
            return StreamReadMessage.ReadResponse(
                partition_data=partition_data,
                bytes_size=msg.bytes_size,
            )

        @dataclass
        class MessageData(IFromProto):
            offset: int
            seq_no: int
            created_at: datetime.datetime
            data: bytes
            uncompresed_size: int
            message_group_id: str

            @staticmethod
            def from_proto(
                msg: ydb_topic_pb2.StreamReadMessage.ReadResponse.MessageData,
            ) -> "StreamReadMessage.ReadResponse.MessageData":
                return StreamReadMessage.ReadResponse.MessageData(
                    offset=msg.offset,
                    seq_no=msg.seq_no,
                    created_at=msg.created_at.ToDatetime(),
                    data=msg.data,
                    uncompresed_size=msg.uncompressed_size,
                    message_group_id=msg.message_group_id,
                )

        @dataclass
        class Batch(IFromProto):
            message_data: List["StreamReadMessage.ReadResponse.MessageData"]
            producer_id: str
            write_session_meta: Dict[str, str]
            codec: int
            written_at: datetime.datetime

            @staticmethod
            def from_proto(
                msg: ydb_topic_pb2.StreamReadMessage.ReadResponse.Batch,
            ) -> "StreamReadMessage.ReadResponse.Batch":
                message_data = []
                for message in msg.message_data:
                    message_data.append(
                        StreamReadMessage.ReadResponse.MessageData.from_proto(message)
                    )
                return StreamReadMessage.ReadResponse.Batch(
                    message_data=message_data,
                    producer_id=msg.producer_id,
                    write_session_meta=dict(msg.write_session_meta),
                    codec=msg.codec,
                    written_at=msg.written_at.ToDatetime(),
                )

        @dataclass
        class PartitionData(IFromProto):
            partition_session_id: int
            batches: List["StreamReadMessage.ReadResponse.Batch"]

            @staticmethod
            def from_proto(
                msg: ydb_topic_pb2.StreamReadMessage.ReadResponse.PartitionData,
            ) -> "StreamReadMessage.ReadResponse.PartitionData":
                batches = []
                for proto_batch in msg.batches:
                    batches.append(
                        StreamReadMessage.ReadResponse.Batch.from_proto(proto_batch)
                    )
                return StreamReadMessage.ReadResponse.PartitionData(
                    partition_session_id=msg.partition_session_id,
                    batches=batches,
                )

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
    class StartPartitionSessionRequest(IFromProto):
        partition_session: "StreamReadMessage.PartitionSession"
        committed_offset: int
        partition_offsets: OffsetsRange

        @staticmethod
        def from_proto(
            msg: ydb_topic_pb2.StreamReadMessage.StartPartitionSessionRequest,
        ) -> "StreamReadMessage.StartPartitionSessionRequest":
            return StreamReadMessage.StartPartitionSessionRequest(
                partition_session=StreamReadMessage.PartitionSession.from_proto(
                    msg.partition_session
                ),
                committed_offset=msg.committed_offset,
                partition_offsets=OffsetsRange.from_proto(msg.partition_offsets),
            )

    @dataclass
    class StartPartitionSessionResponse(IToProto):
        partition_session_id: int
        read_offset: int
        commit_offset: int

        def to_proto(
            self,
        ) -> ydb_topic_pb2.StreamReadMessage.StartPartitionSessionResponse:
            res = ydb_topic_pb2.StreamReadMessage.StartPartitionSessionResponse()
            res.partition_session_id = self.partition_session_id
            res.read_offset = self.read_offset
            res.commit_offset = self.commit_offset
            return res

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
            if isinstance(self.client_message, StreamReadMessage.ReadRequest):
                res.read_request.CopyFrom(self.client_message.to_proto())
            elif isinstance(self.client_message, StreamReadMessage.InitRequest):
                res.init_request.CopyFrom(self.client_message.to_proto())
            elif isinstance(
                self.client_message, StreamReadMessage.StartPartitionSessionResponse
            ):
                res.start_partition_session_response.CopyFrom(
                    self.client_message.to_proto()
                )
            else:
                raise NotImplementedError()
            return res

    @dataclass
    class FromServer(IFromProto):
        server_message: "ReaderMessagesFromServerToClient"
        server_status: ServerStatus

        @staticmethod
        def from_proto(
            msg: ydb_topic_pb2.StreamReadMessage.FromServer,
        ) -> "StreamReadMessage.FromServer":
            mess_type = msg.WhichOneof("server_message")
            server_status = ServerStatus.from_proto(msg)
            if mess_type == "read_response":
                return StreamReadMessage.FromServer(
                    server_status=server_status,
                    server_message=StreamReadMessage.ReadResponse.from_proto(
                        msg.read_response
                    ),
                )
            elif mess_type == "init_response":
                return StreamReadMessage.FromServer(
                    server_status=server_status,
                    server_message=StreamReadMessage.InitResponse.from_proto(
                        msg.init_response
                    ),
                )
            elif mess_type == "start_partition_session_request":
                return StreamReadMessage.FromServer(
                    server_status=server_status,
                    server_message=StreamReadMessage.StartPartitionSessionRequest.from_proto(
                        msg.start_partition_session_request
                    ),
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
