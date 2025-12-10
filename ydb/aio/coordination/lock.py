import asyncio
import contextlib

from ydb import issues
from ydb._grpc.grpcwrapper.ydb_coordination import (
    AcquireSemaphore,
    ReleaseSemaphore,
    UpdateSemaphore,
    DescribeSemaphore,
    CreateSemaphore,
    DeleteSemaphore,
    FromServer,
)
from ydb._grpc.grpcwrapper.ydb_coordination_public_types import CreateSemaphoreResult, DescribeLockResult
from ydb.aio.coordination.reconnector import CoordinationReconnector


class CoordinationLock:
    def __init__(self, client, name: str, node_path: str = None):
        self._client = client
        self._driver = client._driver
        self._name = name
        self._node_path = node_path

        self._count: int = 1
        self._timeout_millis: int = 30000

        self._stream = None
        self._reconnector = CoordinationReconnector(
            driver=self._driver,
            request_queue=asyncio.Queue(),
            node_path=self._node_path,
            timeout_millis=self._timeout_millis,
        )

        self._wait_timeout: float = self._timeout_millis / 1000.0

        self._pending_futures = {
            "acquire": [],
            "release": [],
            "create": [],
            "delete": [],
            "describe": [],
            "update": [],
        }

    async def _ensure_session(self):
        if self._stream is not None and self._stream.session_id is not None:
            return

        if not self._node_path:
            raise issues.Error("node_path is not set for CoordinationLock")

        self._reconnector.start()
        await self._reconnector.wait_ready()
        self._stream = self._reconnector.get_stream()

        if not hasattr(self._stream, "_dispatch_task") or self._stream._dispatch_task is None:
            self._stream._dispatch_task = asyncio.create_task(self._stream_dispatch_loop())

    async def _stream_dispatch_loop(self):
        try:
            while True:
                resp = await self._stream.receive(self._wait_timeout)
                print("[RECV RAW]", resp)
                fs = FromServer.from_proto(resp)
                print("[RECV PARSED]", fs)

                raw = fs.raw

                if raw.HasField("acquire_semaphore_result"):
                    op_type = "acquire"
                    payload = fs.acquire_semaphore_result
                elif raw.HasField("describe_semaphore_result"):
                    op_type = "describe"
                    payload = fs.describe_semaphore_result
                elif raw.HasField("create_semaphore_result"):
                    op_type = "create"
                    payload = fs.create_semaphore_result
                elif raw.HasField("update_semaphore_result"):
                    op_type = "update"
                    payload = fs.update_semaphore_result
                elif raw.HasField("delete_semaphore_result"):
                    op_type = "delete"
                    payload = fs.delete_semaphore_result
                else:
                    continue

                futures = self._pending_futures.get(op_type, [])
                for fut in futures:
                    if not fut.done():
                        print("[RESOLVE FUTURE]", fut)
                        fut.set_result(payload)
                self._pending_futures[op_type] = []

        except asyncio.CancelledError:
            for futs in self._pending_futures.values():
                for fut in futs:
                    if not fut.done():
                        fut.set_exception(asyncio.CancelledError())
                futs.clear()
            raise
        except Exception as exc:
            for futs in self._pending_futures.values():
                for fut in futs:
                    if not fut.done():
                        fut.set_exception(exc)
                futs.clear()
            with contextlib.suppress(Exception):
                await self._stream.close()
            return

    async def _send_and_wait(self, req, op_type: str):
        await self._ensure_session()
        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        self._pending_futures[op_type].append(fut)
        await self._stream.send(req)
        return await asyncio.wait_for(fut, timeout=self._wait_timeout)

    async def __aenter__(self):
        req = AcquireSemaphore(
            req_id=0,
            name=self._name,
            count=self._count,
            ephemeral=False,
            timeout_millis=self._timeout_millis,
        )
        await self._send_and_wait(req, "acquire")
        return self

    async def __aexit__(self, exc_type, exc, tb):
        try:
            req = ReleaseSemaphore(req_id=0, name=self._name)
            if self._stream is not None:
                await self._stream.send(req)
        except issues.Error:
            pass

    async def acquire(self):
        return await self.__aenter__()

    async def release(self):
        await self.__aexit__(None, None, None)

    async def create(self, init_limit, init_data):
        req = CreateSemaphore(req_id=0, name=self._name, limit=init_limit, data=init_data)
        resp = await self._send_and_wait(req, "create")
        return CreateSemaphoreResult.from_proto(resp)

    async def delete(self):
        req = DeleteSemaphore(req_id=0, name=self._name)
        resp = await self._send_and_wait(req, "delete")
        return resp

    async def describe(self):
        req = DescribeSemaphore(
            req_id=0,
            name=self._name,
            include_owners=True,
            include_waiters=True,
            watch_data=False,
            watch_owners=False,
        )
        resp = await self._send_and_wait(req, "describe")
        return DescribeLockResult.from_proto(resp)

    async def update(self, new_data):
        req = UpdateSemaphore(req_id=0, name=self._name, data=new_data)
        resp = await self._send_and_wait(req, "update")
        return resp

    async def close(self, flush: bool = True):
        try:
            req = ReleaseSemaphore(req_id=0, name=self._name)
            if self._stream is not None:
                await self._stream.send(req)
        except issues.Error:
            pass

        if self._reconnector is not None:
            await self._reconnector.stop(flush)

        self._stream = None
        self._node_path = None
