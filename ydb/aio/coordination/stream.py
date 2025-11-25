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
        self._stream: Optional[GrpcWrapperAsyncIO] = None
        self._background_tasks: Set[asyncio.Task] = set()
        self._incoming_queue: asyncio.Queue = asyncio.Queue()
        self._closed = False
        self._started = False
        self._first_error: asyncio.Future = asyncio.get_running_loop().create_future()
        self.session_id: Optional[int] = None
        self._state_changed = asyncio.Event()

    async def start_session(self, path: str, timeout_millis: int):
        if self._started:
            raise issues.Error("CoordinationStream already started")

        self._started = True
        self._stream = GrpcWrapperAsyncIO(FromServer.from_proto)
        await self._stream.start(self._driver, _apis.CoordinationService.Stub, _apis.CoordinationService.Session)

        start_msg: IToProto = SessionStart(path=path, timeout_millis=timeout_millis)
        self._stream.write(start_msg)

        try:
            async for resp in self._stream.from_server_grpc:
                fs = FromServer.from_proto(resp)
                if fs.session_started:
                    self.session_id = fs.session_started
                    break
            else:
                raise issues.Error("Failed to start coordination session")
        except asyncio.TimeoutError:
            raise issues.Error("Timeout waiting for SessionStart response")
        except Exception as e:
            raise issues.Error(f"Failed to start session: {e}")

        self._background_tasks.add(asyncio.create_task(self._reader_loop()))

    async def _reader_loop(self):
        try:
            async for resp in self._stream.from_server_grpc:
                if self._closed:
                    break

                fs = FromServer.from_proto(resp)
                if fs.opaque:
                    self._stream.write(Ping(fs.opaque))
                else:
                    await self._incoming_queue.put(resp)
                    self._state_changed.set()
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            self._set_first_error(exc)

    async def send(self, req: IToProto):
        self._check_error()
        if self._closed:
            raise issues.Error("Stream closed")
        if not isinstance(req, IToProto):
            raise TypeError(f"Cannot write object of type {type(req).__name__}, must implement IToProto")
        self._stream.write(req)

    async def receive(self, timeout: Optional[float] = None):
        self._check_error()
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

        tasks = list(self._background_tasks)
        for task in tasks:
            task.cancel()

        with contextlib.suppress(asyncio.CancelledError):
            await asyncio.gather(*tasks, return_exceptions=True)

        self._background_tasks.clear()

        if self._stream:
            close_coro = getattr(self._stream, "close", None)
            if close_coro and asyncio.iscoroutinefunction(close_coro):
                await self._stream.close()
            else:
                self._stream.close()

        self.session_id = None
        self._started = False
        self._state_changed.set()
        self._incoming_queue = asyncio.Queue()

    def _set_first_error(self, exc: Exception):
        if not self._first_error.done():
            self._first_error.set_result(exc)
            self._state_changed.set()

    def _get_first_error(self):
        if self._first_error.done():
            return self._first_error.result()

    def _check_error(self):
        err = self._get_first_error()
        if err:
            raise err
