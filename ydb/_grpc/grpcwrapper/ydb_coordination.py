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
class AlterNodeRequest(IToProto):
    path: str
    config: typing.Optional[public_types.NodeConfig] = None
    operation_params: typing.Any = None

    def to_proto(self) -> ydb_coordination_pb2.AlterNodeRequest:
        cfg_proto = self.config.to_proto() if self.config else None
        return ydb_coordination_pb2.AlterNodeRequest(
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


