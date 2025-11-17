import asyncio
from typing import Optional

from ydb._grpc.grpcwrapper.ydb_coordination import (
    CreateNodeRequest,
    DescribeNodeRequest,
    AlterNodeRequest,
    DropNodeRequest,
)
from ydb._grpc.grpcwrapper.ydb_coordination_public_types import NodeConfig
from ydb.aio.coordination.lock import CoordinationLock
from ydb.aio.coordination.reconnector import CoordinationReconnector
from ydb.aio.coordination.stream import CoordinationStream
from ydb.coordination.base_coordination_client import BaseCoordinationClient


class CoordinationClient(BaseCoordinationClient):
    def __init__(self, driver):
        super().__init__(driver)
        self._driver = driver
        self._closed = asyncio.Event()
        self._request_queue: asyncio.Queue = asyncio.Queue()
        self._stream: Optional[CoordinationStream] = None
        self._reader_task: Optional[asyncio.Task] = None
        self.session_id: Optional[int] = None
        self._session_ready: asyncio.Event = asyncio.Event()
        self._reconnector = CoordinationReconnector(self)
        self._first_error: asyncio.Future = asyncio.get_running_loop().create_future()
        self._node_path: Optional[str] = None

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
            settings=settings
        )

    def lock(self, lock_name: str, node_path: str):
        self._node_path = node_path
        return CoordinationLock(self, lock_name)
