import asyncio
import contextlib
from typing import Optional, Set

import ydb
from ydb import issues, _apis
from ydb._grpc.grpcwrapper.common_utils import IToProto, GrpcWrapperAsyncIO
from ydb._grpc.grpcwrapper.ydb_coordination import FromServer, Ping, SessionStart


class CoordinationStream:
    def __init__(self, driver: "ydb.aio.Driver"):
        self._driver = driver
        self._stream: GrpcWrapperAsyncIO = GrpcWrapperAsyncIO(FromServer.from_proto)
        self._background_tasks: Set[asyncio.Task] = set()
        self._incoming_queue: asyncio.Queue = asyncio.Queue()
        self._closed = False
        self._started = False
        self.session_id: Optional[int] = None

    async def start_session(self, path: str, timeout_millis: int):
        if self._started:
            raise issues.Error("CoordinationStream already started")

        self._started = True
        await self._stream.start(self._driver, _apis.CoordinationService.Stub, _apis.CoordinationService.Session)

        self._stream.write(SessionStart(path=path, timeout_millis=timeout_millis))

        while True:
            try:
                resp = await self._stream.receive(timeout=3)
                if resp.session_started:
                    self.session_id = resp.session_started
                    break
                else:
                    continue
            except asyncio.TimeoutError:
                raise issues.Error("Timeout waiting for SessionStart response")
            except Exception as e:
                raise issues.Error(f"Failed to start session: {e}")

        task = asyncio.get_running_loop().create_task(self._reader_loop())
        self._background_tasks.add(task)

    async def _reader_loop(self):
        while True:
            try:
                resp = await self._stream.receive(timeout=3)
                if self._closed:
                    break

                fs = FromServer.from_proto(resp)
                if fs.opaque:
                    try:
                        self._stream.write(Ping(fs.opaque))
                    except Exception:
                        raise issues.Error("Failed to write Ping")
                else:
                    await self._incoming_queue.put(resp)
            except asyncio.CancelledError:
                break

    async def send(self, req: IToProto):
        if self._closed:
            raise issues.Error("Stream closed")
        self._stream.write(req)

    async def receive(self, timeout: Optional[float] = None):
        if self._closed:
            raise issues.Error("Stream closed")

        try:
            if timeout is not None:
                return await asyncio.wait_for(self._incoming_queue.get(), timeout)
            else:
                return await self._incoming_queue.get()
        except asyncio.TimeoutError:
            return None

    async def close(self):
        if self._closed:
            return
        self._closed = True

        for task in list(self._background_tasks):
            task.cancel()

        with contextlib.suppress(asyncio.CancelledError):
            await asyncio.gather(*self._background_tasks, return_exceptions=True)

        self._background_tasks.clear()

        if self._stream:
            self._stream.close()
            self._stream = None

        self.session_id = None
