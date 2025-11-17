import asyncio
from typing import Optional

from ydb import issues
from ydb._grpc.grpcwrapper.ydb_coordination import (
    AcquireSemaphore,
    ReleaseSemaphore,
    FromServer,
)
from ydb.aio.coordination.stream import CoordinationStream
from ydb.aio.coordination.reconnector import CoordinationReconnector


class CoordinationLock:
    def __init__(
        self,
        client,
        name: str,
        node_path: Optional[str] = None,
        count: int = 1,
        timeout_millis: int = 30000,
    ):
        self._client = client
        self._driver = client._driver
        self._name = name
        self._node_path = node_path

        self._req_id: Optional[int] = None
        self._count: int = count
        self._timeout_millis: int = timeout_millis
        self._next_req_id: int = 1

        self._request_queue: asyncio.Queue = asyncio.Queue()
        self._stream: Optional[CoordinationStream] = None

        self._reconnector = CoordinationReconnector(
            driver=self._driver,
            request_queue=self._request_queue,
            node_path=self._node_path,
            timeout_millis=self._timeout_millis,
        )

        self._wait_timeout: float = self._timeout_millis / 1000.0

    def next_req_id(self) -> int:
        r = self._next_req_id
        self._next_req_id += 1
        return r

    async def send(self, req):
        if self._stream is None:
            raise issues.Error("Stream is not started yet")
        await self._stream.send(req)

    async def _ensure_session(self):
        if self._stream is not None and self._stream.session_id is not None:
            return

        if not self._node_path:
            raise issues.Error("node_path is not set for CoordinationLock")

        self._reconnector.start()
        await self._reconnector.wait_ready()

        self._stream = self._reconnector.get_stream()

    async def _wait_for_acquire_response(self):
        try:
            while True:
                resp = await asyncio.wait_for(
                    self._stream._incoming_queue.get(),
                    timeout=self._wait_timeout,
                )
                acquire_resp = FromServer.from_proto(resp).acquire_semaphore_result
                if acquire_resp and acquire_resp.req_id == self._req_id:
                    return acquire_resp
        except asyncio.TimeoutError:
            raise issues.Error(
                f"Timeout waiting for lock {self._name} acquisition"
            )

    async def __aenter__(self):
        await self._ensure_session()

        self._req_id = self.next_req_id()

        req = AcquireSemaphore(
            req_id=self._req_id,
            name=self._name,
            count=self._count,
            ephemeral=True,
            timeout_millis=self._timeout_millis,
        ).to_proto()

        await self.send(req)

        resp = await self._wait_for_acquire_response()
        if resp.acquired:
            return self
        else:
            raise issues.Error(f"Failed to acquire lock: {resp.issues}")

    async def __aexit__(self, exc_type, exc, tb):
        if self._req_id is not None:
            try:
                req = ReleaseSemaphore(req_id=self._req_id, name=self._name)
                await self.send(req)
            except issues.Error:
                pass

        await self._reconnector.stop()
        self._stream = None
        self._node_path = None

    async def acquire(self):
        return await self.__aenter__()

    async def release(self):
        await self.__aexit__(None, None, None)
