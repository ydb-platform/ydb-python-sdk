import typing
from dataclasses import dataclass

import ydb

if typing.TYPE_CHECKING:
    from ..v4.protos import ydb_coordination_pb2
else:
    from ..common.protos import ydb_coordination_pb2

from .common_utils import IToProto, IFromProto, ServerStatus
from . import ydb_coordination_public_types as public_types


# -------------------- Requests --------------------

@dataclass
class CreateNodeRequest(IToProto):
    path: str
    config: typing.Optional[public_types.NodeConfig] = None
    operation_params: typing.Any = None

    def to_proto(self) -> ydb_coordination_pb2.CreateNodeRequest:
        cfg_proto = self.config.to_proto() if self.config else None
        return ydb_coordination_pb2.CreateNodeRequest(
            path=self.path,
            config=cfg_proto,
            operation_params=self.operation_params,
        )


@dataclass
class DescribeNodeRequest(IToProto):
    path: str
    operation_params: typing.Any = None

    def to_proto(self) -> ydb_coordination_pb2.DescribeNodeRequest:
        return ydb_coordination_pb2.DescribeNodeRequest(
            path=self.path,
            operation_params=self.operation_params,
        )


@dataclass
class DropNodeRequest(IToProto):
    path: str
    operation_params: typing.Any = None

    def to_proto(self) -> ydb_coordination_pb2.DropNodeRequest:
        return ydb_coordination_pb2.DropNodeRequest(
            path=self.path,
            operation_params=self.operation_params,
        )


@dataclass
class CreateNodeResponse(IFromProto):
    operation : ydb.Operation
    OPERATION_FIELD_NUMBER : int

    @staticmethod
    def from_proto(msg: ydb_coordination_pb2.CreateNodeResponse) -> "CreateNodeResponse":
        return CreateNodeResponse(
            operation=msg.operation,
            OPERATION_FIELD_NUMBER=msg.OPERATION_FIELD_NUMBER
        )


@dataclass
class DescribeNodeResponse(IFromProto):
    operation : ydb.Operation
    OPERATION_FIELD_NUMBER : int

    @staticmethod
    def from_proto(msg: "ydb_coordination_pb2.DescribeNodeResponse") -> "DescribeNodeResponse":
        return DescribeNodeResponse(
            operation=msg.operation,
            OPERATION_FIELD_NUMBER=msg.OPERATION_FIELD_NUMBER
        )


@dataclass
class DropNodeResponse(IFromProto):
    operation : ydb.Operation
    OPERATION_FIELD_NUMBER : int

    @staticmethod
    def from_proto(msg: ydb_coordination_pb2.DropNodeResponse) -> "DropNodeResponse":
        return DropNodeResponse(
            operation=msg.operation,
            OPERATION_FIELD_NUMBER=msg.OPERATION_FIELD_NUMBER
        )

