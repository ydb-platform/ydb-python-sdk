import asyncio

from ..._grpc.grpcwrapper.ydb_coordination import (
    AcquireSemaphore,
    ReleaseSemaphore,
    UpdateSemaphore,
    DescribeSemaphore,
    CreateSemaphore,
    DeleteSemaphore,
)
from ..._grpc.grpcwrapper.ydb_coordination_public_types import (
    CreateSemaphoreResult,
    DescribeLockResult,
)
from ...aio.coordination.reconnector import CoordinationReconnector


class CoordinationLock:
    _REQ_COUNTER = 1

    def __init__(self, client, name: str, node_path: str = None):
        self._client = client
        self._driver = client._driver
        self._name = name
        self._node_path = node_path

        self._count: int = 1
        self._timeout_millis: int = 30000

        self._reconnector = CoordinationReconnector(
            driver=self._driver,
            node_path=self._node_path,
            timeout_millis=self._timeout_millis,
        )

    @classmethod
    def _next_req_id(cls) -> int:
        cls._REQ_COUNTER += 1
        return cls._REQ_COUNTER

    async def acquire(self):
        req = AcquireSemaphore(
            req_id=self._next_req_id(),
            name=self._name,
            count=self._count,
            ephemeral=False,
            timeout_millis=self._timeout_millis,
        )
        await self._reconnector.send_and_wait(req)
        return self

    async def release(self):
        req = ReleaseSemaphore(req_id=self._next_req_id(), name=self._name)
        try:
            await asyncio.shield(self._reconnector.send_and_wait(req))
        except (asyncio.CancelledError, Exception):
            pass

    async def create(self, init_limit: int, init_data: bytes):
        req = CreateSemaphore(
            req_id=self._next_req_id(),
            name=self._name,
            limit=init_limit,
            data=init_data,
        )
        resp = await self._reconnector.send_and_wait(req)
        return CreateSemaphoreResult.from_proto(resp)

    async def delete(self):
        req = DeleteSemaphore(req_id=self._next_req_id(), name=self._name)
        resp = await self._reconnector.send_and_wait(req)
        return resp

    async def describe(self):
        req = DescribeSemaphore(
            req_id=self._next_req_id(),
            name=self._name,
            include_owners=True,
            include_waiters=True,
            watch_data=False,
            watch_owners=False,
        )
        resp = await self._reconnector.send_and_wait(req)
        return DescribeLockResult.from_proto(resp)

    async def update(self, new_data: bytes):
        req = UpdateSemaphore(req_id=self._next_req_id(), name=self._name, data=new_data)
        return await self._reconnector.send_and_wait(req)

    async def close(self):
        try:
            await self.release()
        except Exception:
            pass

        await self._reconnector.stop()

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
