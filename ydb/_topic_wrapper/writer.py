import datetime
import enum
import typing
from dataclasses import dataclass, field
from typing import Union

from google.protobuf.message import Message

from ydb._topic_wrapper.common import (
    IToProto,
    IFromProto,
    ServerStatus,
    UpdateTokenRequest,
    UpdateTokenResponse,
    UnknownGrpcMessageError,
)

# Workaround for good autocomplete in IDE and universal import at runtime
if False:
    from ydb._grpc.v4.protos import ydb_topic_pb2
else:
    from ydb._grpc.common.protos import ydb_topic_pb2


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
