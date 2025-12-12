from typing import Optional

from ..._grpc.grpcwrapper.ydb_coordination import (
    CreateNodeRequest,
    DescribeNodeRequest,
    AlterNodeRequest,
    DropNodeRequest,
)
from ..._grpc.grpcwrapper.ydb_coordination_public_types import NodeConfig
from ...coordination.base import BaseCoordinationClient

from .lock import CoordinationLock


class CoordinationClient(BaseCoordinationClient):
    def __init__(self, driver):
        super().__init__(driver)
        self._driver = driver

    async def create_node(self, path: str, config: Optional[NodeConfig] = None, settings=None):
        return await self._call_create(
            CreateNodeRequest(path=path, config=config).to_proto(),
            settings=settings,
        )

    async def describe_node(self, path: str, settings=None) -> NodeConfig:
        return await self._call_describe(
            DescribeNodeRequest(path=path).to_proto(),
            settings=settings,
        )

    async def alter_node(self, path: str, new_config: NodeConfig, settings=None):
        return await self._call_alter(
            AlterNodeRequest(path=path, config=new_config).to_proto(),
            settings=settings,
        )

    async def delete_node(self, path: str, settings=None):
        return await self._call_delete(
            DropNodeRequest(path=path).to_proto(),
            settings=settings,
        )

    def lock(self, lock_name: str, node_path: str):
        return CoordinationLock(self, lock_name, node_path=node_path)
