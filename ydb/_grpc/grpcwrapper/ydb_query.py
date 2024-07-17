from dataclasses import dataclass
import typing
from typing import Optional

from google.protobuf.message import Message

# Workaround for good IDE and universal for runtime
if typing.TYPE_CHECKING:
    from ..v4.protos import ydb_query_pb2
else:
    from ..common.protos import ydb_query_pb2

from .common_utils import (
    IFromProto,
    IFromProtoWithProtoType,
    IToProto,
    IToPublic,
    IFromPublic,
    ServerStatus,
    UnknownGrpcMessageError,
    proto_duration_from_timedelta,
    proto_timestamp_from_datetime,
    datetime_from_proto_timestamp,
    timedelta_from_proto_duration,
)

@dataclass
class CreateSessionResponse(IFromProto):
    status: Optional[ServerStatus]
    session_id: str
    node_id: int

    @staticmethod
    def from_proto(msg: ydb_query_pb2.CreateSessionResponse) -> "CreateSessionResponse":
        return CreateSessionResponse(
            status=ServerStatus(msg.status, msg.issues),
            session_id=msg.session_id,
            node_id=msg.node_id,
        )


# @dataclass
# class DeleteSessionRequest(IToProto):
#     session_id: str

#     def to_proto(self) -> ydb_query_pb2.DeleteSessionRequest:
#         return ydb_query_pb2.DeleteSessionRequest(session_id=self.session_id)


@dataclass
class DeleteSessionResponse(IFromProto):
    status: Optional[ServerStatus]

    @staticmethod
    def from_proto(msg: ydb_query_pb2.DeleteSessionResponse) -> "DeleteSessionResponse":
        return DeleteSessionResponse(status=ServerStatus(msg.status, msg.issues))
