import typing
from dataclasses import dataclass


if typing.TYPE_CHECKING:
    from ..v4.protos import ydb_coordination_pb2
else:
    from ..common.protos import ydb_coordination_pb2

from .common_utils import IToProto
from ydb.coordination import NodeConfig


@dataclass
class CreateNodeRequest(IToProto):
    path: str
    config: typing.Optional[NodeConfig] = None

    def to_proto(self) -> ydb_coordination_pb2.CreateNodeRequest:
        cfg_proto = self.config.to_proto() if self.config else None
        return ydb_coordination_pb2.CreateNodeRequest(
            path=self.path,
            config=cfg_proto,
        )


@dataclass
class AlterNodeRequest(IToProto):
    path: str
    config: typing.Optional[NodeConfig] = None

    def to_proto(self) -> ydb_coordination_pb2.AlterNodeRequest:
        cfg_proto = self.config.to_proto() if self.config else None
        return ydb_coordination_pb2.AlterNodeRequest(
            path=self.path,
            config=cfg_proto,
        )


@dataclass
class DescribeNodeRequest(IToProto):
    path: str

    def to_proto(self) -> ydb_coordination_pb2.DescribeNodeRequest:
        return ydb_coordination_pb2.DescribeNodeRequest(
            path=self.path,
        )


@dataclass
class DropNodeRequest(IToProto):
    path: str

    def to_proto(self) -> ydb_coordination_pb2.DropNodeRequest:
        return ydb_coordination_pb2.DropNodeRequest(
            path=self.path,
        )
