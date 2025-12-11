import asyncio
from typing import Optional

from ydb import issues
from ydb._grpc.grpcwrapper.ydb_coordination import (
    AcquireSemaphore,
    ReleaseSemaphore,
    UpdateSemaphore,
    DescribeSemaphore,
    CreateSemaphore,
    DeleteSemaphore,
)
from ydb._grpc.grpcwrapper.ydb_coordination_public_types import CreateSemaphoreResult, DescribeLockResult
from ydb.aio.coordination.reconnector import CoordinationReconnector


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
        await self._reconnector.send_and_wait(req, "acquire")
        return self

    async def release(self):
        req = ReleaseSemaphore(req_id=self._next_req_id(), name=self._name)
        try:
            print(f"Releasing lock {self._name} with req_id={req.req_id}")
            await asyncio.shield(self._reconnector.send_and_wait(req, "release"))
            print(f"Released lock {self._name} req_id={req.req_id}")
        except (asyncio.CancelledError, Exception):
            # игнорируем, чтобы __aexit__ не падал
            pass

    async def create(self, init_limit: int, init_data: bytes):
        req = CreateSemaphore(
            req_id=self._next_req_id(),
            name=self._name,
            limit=init_limit,
            data=init_data,
        )
        resp = await self._reconnector.send_and_wait(req, "create")
        return CreateSemaphoreResult.from_proto(resp)

    async def delete(self):
        req = DeleteSemaphore(req_id=self._next_req_id(), name=self._name)
        resp = await self._reconnector.send_and_wait(req, "delete")
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
        resp = await self._reconnector.send_and_wait(req, "describe")
        return DescribeLockResult.from_proto(resp)

    async def update(self, new_data: bytes):
        req = UpdateSemaphore(req_id=self._next_req_id(), name=self._name, data=new_data)
        return await self._reconnector.send_and_wait(req, "update")

    async def close(self, flush: bool = True):
        try:
            req = ReleaseSemaphore(req_id=self._next_req_id(), name=self._name)
            await asyncio.shield(self._reconnector.send_and_wait(req, "release"))
        except issues.Error:
            pass
        await self._reconnector.stop(flush)

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.release()
