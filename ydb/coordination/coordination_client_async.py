from typing import Optional

from ydb._grpc.grpcwrapper.ydb_coordination import (
    CreateNodeRequest,
    DescribeNodeRequest,
    AlterNodeRequest,
    DropNodeRequest,
)
from ydb._grpc.grpcwrapper.ydb_coordination_public_types import NodeConfig, NodeDescription
from ydb.coordination.base_coordination_client import BaseCoordinationClient


class AsyncCoordinationClient(BaseCoordinationClient):
    async def create_node(self, path: str, config: Optional[NodeConfig] = None, settings=None):
        return await self._call_create(
            CreateNodeRequest(path=path, config=config).to_proto(),
            settings=settings,
            wrap_args=(self,),
        )

    async def describe_node(self, path: str, settings=None) -> NodeDescription:
        return await self._call_describe(
            DescribeNodeRequest(path=path).to_proto(),
            settings=settings,
            wrap_args=(self, path),
        )

    async def alter_node(self, path: str, new_config: NodeConfig, settings=None):
        return await self._call_alter(
            AlterNodeRequest(path=path, config=new_config).to_proto(),
            settings=settings,
            wrap_args=(self,),
        )

    async def delete_node(self, path: str, settings=None):
        return await self._call_delete(
            DropNodeRequest(path=path).to_proto(),
            settings=settings,
            wrap_args=(self,),
        )

    async def lock(self):
        raise NotImplementedError("Will be implemented in future release")
