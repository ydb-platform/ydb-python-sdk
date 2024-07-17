from dataclasses import dataclass
import typing
from typing import Optional

from google.protobuf.message import Message

# Workaround for good IDE and universal for runtime
if typing.TYPE_CHECKING:
    from ..v4.protos import ydb_query_pb2
else:
    from ..common.protos import ydb_query_pb2

from . import ydb_query_public_types as public_types

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


@dataclass
class DeleteSessionResponse(IFromProto):
    status: Optional[ServerStatus]

    @staticmethod
    def from_proto(msg: ydb_query_pb2.DeleteSessionResponse) -> "DeleteSessionResponse":
        return DeleteSessionResponse(status=ServerStatus(msg.status, msg.issues))


@dataclass
class AttachSessionRequest(IToProto):
    session_id: str

    def to_proto(self) -> ydb_query_pb2.AttachSessionRequest:
        return ydb_query_pb2.AttachSessionRequest(session_id=self.session_id)

# @dataclass
# class SessionState(IFromProto):
#     status: Optional[ServerStatus]

#     @staticmethod
#     def from_proto(msg: ydb_query_pb2.SessionState) -> "SessionState":
#         return SessionState(status=ServerStatus(msg.status, msg.issues))


@dataclass
class TransactionMeta(IFromProto):
    tx_id: str

    @staticmethod
    def from_proto(msg: ydb_query_pb2.TransactionMeta) -> "TransactionMeta":
        return TransactionMeta(tx_id=msg.id)


@dataclass
class TransactionSettings(IFromPublic, IToProto):
    tx_mode: public_types.BaseQueryTxMode

    @staticmethod
    def from_public(tx_mode: public_types.BaseQueryTxMode) -> "TransactionSettings":
        return TransactionSettings(tx_mode=tx_mode)

    def to_proto(self) -> ydb_query_pb2.TransactionSettings:
        if self.tx_mode.name == 'snapshot_read_only':
            return ydb_query_pb2.TransactionSettings(snapshot_read_only=self.tx_mode.to_proto())
        if self.tx_mode.name == 'serializable_read_write':
            return ydb_query_pb2.TransactionSettings(serializable_read_write=self.tx_mode.to_proto())
        if self.tx_mode.name == 'online_read_only':
            return ydb_query_pb2.TransactionSettings(online_read_only=self.tx_mode.to_proto())
        if self.tx_mode.name == 'stale_read_only':
            return ydb_query_pb2.TransactionSettings(stale_read_only=self.tx_mode.to_proto())
        # TODO: add exception

@dataclass
class BeginTransactionRequest(IToProto):
    session_id: str
    tx_settings: TransactionSettings

    def to_proto(self) -> ydb_query_pb2.BeginTransactionRequest:
        return ydb_query_pb2.BeginTransactionRequest(
            session_id=self.session_id,
            tx_settings=self.tx_settings
            )

@dataclass
class BeginTransactionResponse(IFromProto):
    status: Optional[ServerStatus]
    tx_meta: TransactionMeta

    @staticmethod
    def from_proto(msg: ydb_query_pb2.BeginTransactionResponse) -> "BeginTransactionResponse":
        return BeginTransactionResponse(
            status=ServerStatus(msg.status, msg.issues),
            tx_meta=TransactionMeta.from_proto(msg.tx_meta),
        )