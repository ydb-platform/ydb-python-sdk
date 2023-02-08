import datetime
import enum
import typing
from dataclasses import dataclass, field
from enum import IntEnum
from typing import List, Union, Dict

from google.protobuf.duration_pb2 import Duration as ProtoDuration
from google.protobuf.message import Message

# Workaround for good IDE and universal for runtime
# noinspection PyUnreachableCode
if False:
    from ..v4.protos import ydb_topic_pb2
else:
    from ..common.protos import ydb_topic_pb2

from .common_utils import IFromProto, IToProto, ServerStatus, UnknownGrpcMessageError


class Codec(IntEnum):
    CODEC_UNSPECIFIED = 0
    CODEC_RAW = 1
    CODEC_GZIP = 2
    CODEC_LZOP = 3
    CODEC_ZSTD = 4


@dataclass
class OffsetsRange(IFromProto):
    start: int
    end: int

    @staticmethod
    def from_proto(msg: ydb_topic_pb2.OffsetsRange) -> "OffsetsRange":
        return OffsetsRange(
            start=msg.start,
            end=msg.end,
        )


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


########################################################################################################################
#  StreamWrite
########################################################################################################################


class StreamWriteMessage:
    @dataclass()
    class InitRequest(IToProto):
        path: str
        producer_id: str
        write_session_meta: typing.Dict[str, str]
        partitioning: "StreamWriteMessage.PartitioningType"
        get_last_seq_no: bool

        def to_proto(self) -> ydb_topic_pb2.StreamWriteMessage.InitRequest:
            proto = ydb_topic_pb2.StreamWriteMessage.InitRequest()
            proto.path = self.path
            proto.producer_id = self.producer_id

            if self.partitioning is None:
                pass
            elif isinstance(
                self.partitioning, StreamWriteMessage.PartitioningMessageGroupID
            ):
                proto.message_group_id = self.partitioning.message_group_id
            elif isinstance(
                self.partitioning, StreamWriteMessage.PartitioningPartitionID
            ):
                proto.partition_id = self.partitioning.partition_id
            else:
                raise Exception(
                    "Bad partitioning type at StreamWriteMessage.InitRequest"
                )

            if self.write_session_meta:
                for key in self.write_session_meta:
                    proto.write_session_meta[key] = self.write_session_meta[key]

            proto.get_last_seq_no = self.get_last_seq_no
            return proto

    @dataclass
    class InitResponse(IFromProto):
        last_seq_no: Union[int, None]
        session_id: str
        partition_id: int
        supported_codecs: typing.List[int]
        status: ServerStatus = None

        @staticmethod
        def from_proto(
            msg: ydb_topic_pb2.StreamWriteMessage.InitResponse,
        ) -> "StreamWriteMessage.InitResponse":
            codecs = []  # type: typing.List[int]
            if msg.supported_codecs:
                for codec in msg.supported_codecs.codecs:
                    codecs.append(codec)

            return StreamWriteMessage.InitResponse(
                last_seq_no=msg.last_seq_no,
                session_id=msg.session_id,
                partition_id=msg.partition_id,
                supported_codecs=codecs,
            )

    @dataclass
    class WriteRequest(IToProto):
        messages: typing.List["StreamWriteMessage.WriteRequest.MessageData"]
        codec: int

        @dataclass
        class MessageData(IToProto):
            seq_no: int
            created_at: datetime.datetime
            data: bytes
            uncompressed_size: int
            partitioning: "StreamWriteMessage.PartitioningType"

            def to_proto(
                self,
            ) -> ydb_topic_pb2.StreamWriteMessage.WriteRequest.MessageData:
                proto = ydb_topic_pb2.StreamWriteMessage.WriteRequest.MessageData()
                proto.seq_no = self.seq_no
                proto.created_at.FromDatetime(self.created_at)
                proto.data = self.data
                proto.uncompressed_size = self.uncompressed_size

                if self.partitioning is None:
                    pass
                elif isinstance(
                    self.partitioning, StreamWriteMessage.PartitioningPartitionID
                ):
                    proto.partition_id = self.partitioning.partition_id
                elif isinstance(
                    self.partitioning, StreamWriteMessage.PartitioningMessageGroupID
                ):
                    proto.message_group_id = self.partitioning.message_group_id
                else:
                    raise Exception(
                        "Bad partition at StreamWriteMessage.WriteRequest.MessageData"
                    )

                return proto

        def to_proto(self) -> ydb_topic_pb2.StreamWriteMessage.WriteRequest:
            proto = ydb_topic_pb2.StreamWriteMessage.WriteRequest()
            proto.codec = self.codec

            for message in self.messages:
                proto_mess = proto.messages.add()
                proto_mess.CopyFrom(message.to_proto())

            return proto

    @dataclass
    class WriteResponse(IFromProto):
        partition_id: int
        acks: typing.List["StreamWriteMessage.WriteResponse.WriteAck"]
        write_statistics: "StreamWriteMessage.WriteResponse.WriteStatistics"
        status: ServerStatus = field(default=None)

        @staticmethod
        def from_proto(
            msg: ydb_topic_pb2.StreamWriteMessage.WriteResponse,
        ) -> "StreamWriteMessage.WriteResponse":
            acks = []
            for proto_ack in msg.acks:
                ack = StreamWriteMessage.WriteResponse.WriteAck.from_proto(proto_ack)
                acks.append(ack)
            write_statistics = StreamWriteMessage.WriteResponse.WriteStatistics(
                persisting_time=msg.write_statistics.persisting_time.ToTimedelta(),
                min_queue_wait_time=msg.write_statistics.min_queue_wait_time.ToTimedelta(),
                max_queue_wait_time=msg.write_statistics.max_queue_wait_time.ToTimedelta(),
                partition_quota_wait_time=msg.write_statistics.partition_quota_wait_time.ToTimedelta(),
                topic_quota_wait_time=msg.write_statistics.topic_quota_wait_time.ToTimedelta(),
            )
            return StreamWriteMessage.WriteResponse(
                partition_id=msg.partition_id,
                acks=acks,
                write_statistics=write_statistics,
                status=None,
            )

        @dataclass
        class WriteAck(IFromProto):
            seq_no: int
            message_write_status: Union[
                "StreamWriteMessage.WriteResponse.WriteAck.StatusWritten",
                "StreamWriteMessage.WriteResponse.WriteAck.StatusSkipped",
                int,
            ]

            @classmethod
            def from_proto(
                cls, proto_ack: ydb_topic_pb2.StreamWriteMessage.WriteResponse.WriteAck
            ):
                if proto_ack.HasField("written"):
                    message_write_status = (
                        StreamWriteMessage.WriteResponse.WriteAck.StatusWritten(
                            proto_ack.written.offset
                        )
                    )
                elif proto_ack.HasField("skipped"):
                    reason = proto_ack.skipped.reason
                    try:
                        message_write_status = StreamWriteMessage.WriteResponse.WriteAck.StatusSkipped(
                            reason=StreamWriteMessage.WriteResponse.WriteAck.StatusSkipped.Reason.from_protobuf_code(
                                reason
                            )
                        )
                    except ValueError:
                        message_write_status = reason
                else:
                    raise NotImplementedError("unexpected ack status")

                return StreamWriteMessage.WriteResponse.WriteAck(
                    seq_no=proto_ack.seq_no,
                    message_write_status=message_write_status,
                )

            @dataclass
            class StatusWritten:
                offset: int

            @dataclass
            class StatusSkipped:
                reason: "StreamWriteMessage.WriteResponse.WriteAck.StatusSkipped.Reason"

                class Reason(enum.Enum):
                    UNSPECIFIED = 0
                    ALREADY_WRITTEN = 1

                    @classmethod
                    def from_protobuf_code(
                        cls, code: int
                    ) -> Union[
                        "StreamWriteMessage.WriteResponse.WriteAck.StatusSkipped.Reason",
                        int,
                    ]:
                        try:
                            return StreamWriteMessage.WriteResponse.WriteAck.StatusSkipped.Reason(
                                code
                            )
                        except ValueError:
                            return code

        @dataclass
        class WriteStatistics:
            persisting_time: datetime.timedelta
            min_queue_wait_time: datetime.timedelta
            max_queue_wait_time: datetime.timedelta
            partition_quota_wait_time: datetime.timedelta
            topic_quota_wait_time: datetime.timedelta

    @dataclass
    class PartitioningMessageGroupID:
        message_group_id: str

    @dataclass
    class PartitioningPartitionID:
        partition_id: int

    PartitioningType = Union[PartitioningMessageGroupID, PartitioningPartitionID, None]

    @dataclass
    class FromClient(IToProto):
        value: "WriterMessagesFromClientToServer"

        def __init__(self, value: "WriterMessagesFromClientToServer"):
            self.value = value

        def to_proto(self) -> Message:
            res = ydb_topic_pb2.StreamWriteMessage.FromClient()
            value = self.value
            if isinstance(value, StreamWriteMessage.WriteRequest):
                res.write_request.CopyFrom(value.to_proto())
            elif isinstance(value, StreamWriteMessage.InitRequest):
                res.init_request.CopyFrom(value.to_proto())
            elif isinstance(value, UpdateTokenRequest):
                res.update_token_request.CopyFrom(value.to_proto())
            else:
                raise Exception("Unknown outcoming grpc message: %s" % value)
            return res

    class FromServer(IFromProto):
        @staticmethod
        def from_proto(msg: ydb_topic_pb2.StreamWriteMessage.FromServer) -> typing.Any:
            message_type = msg.WhichOneof("server_message")
            if message_type == "write_response":
                res = StreamWriteMessage.WriteResponse.from_proto(msg.write_response)
            elif message_type == "init_response":
                res = StreamWriteMessage.InitResponse.from_proto(msg.init_response)
            elif message_type == "update_token_response":
                res = UpdateTokenResponse.from_proto(msg.update_token_response)
            else:
                # todo log instead of exception - for allow add messages in the future
                raise UnknownGrpcMessageError("Unexpected proto message: %s" % msg)

            res.status = ServerStatus(msg.status, msg.issues)
            return res


WriterMessagesFromClientToServer = Union[
    StreamWriteMessage.InitRequest, StreamWriteMessage.WriteRequest, UpdateTokenRequest
]
WriterMessagesFromServerToClient = Union[
    StreamWriteMessage.InitResponse,
    StreamWriteMessage.WriteResponse,
    UpdateTokenResponse,
]


########################################################################################################################
#  StreamRead
########################################################################################################################


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
            offsets: List["OffsetsRange"]

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
        partition_offsets: "OffsetsRange"
        committed_offset: int
        write_time_high_watermark: float

    @dataclass
    class StartPartitionSessionRequest(IFromProto):
        partition_session: "StreamReadMessage.PartitionSession"
        committed_offset: int
        partition_offsets: "OffsetsRange"

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
