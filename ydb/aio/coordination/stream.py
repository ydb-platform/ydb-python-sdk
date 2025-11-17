import asyncio
import contextlib
from typing import Set, Optional

from ydb import issues, _apis
from ydb._grpc.grpcwrapper.ydb_coordination import FromServer, Ping, SessionStart


class CoordinationStream:
    def __init__(self, driver: "ydb.aio.Driver", request_queue: asyncio.Queue):
        self._driver = driver
        self._request_queue = request_queue
        self._stream = None
        self._closed: bool = False
        self._background_tasks: Set[asyncio.Task] = set()
        self._incoming_queue: asyncio.Queue = asyncio.Queue()
        self._state_changed = asyncio.Event()
        self._first_error: asyncio.Future = asyncio.get_running_loop().create_future()
        self.session_id: Optional[int] = None
        self._started: bool = False

    async def start_session(self, path: str, timeout_millis: int):
        if self._started:
            raise issues.Error("CoordinationStream already started")

        await self.send(
            SessionStart(
                path=path,
                session_id=0,
                timeout_millis=timeout_millis,
            ).to_proto()
        )

        await self._start_internal()

    async def _start_internal(self):
        if self._started:
            raise issues.Error("CoordinationStream already started")
        self._started = True

        async def request_gen():
            while not self._closed:
                req = await self._request_queue.get()
                yield req

        self._stream = await self._driver(
            request_gen(),
            _apis.CoordinationService.Stub,
            _apis.CoordinationService.Session,
        )

        try:
            async for resp in self._stream:
                fs = FromServer.from_proto(resp)
                if fs.session_started:
                    self.session_id = fs.session_started
                    break
        except Exception as exc:
            self._set_first_error(exc)
            raise

        self._background_tasks.add(asyncio.create_task(self._reader_loop()))

    async def _reader_loop(self):
        try:
            async for resp in self._stream:
                ping_opaque = FromServer.from_proto(resp).opaque
                if ping_opaque:
                    await self.send(Ping(ping_opaque).to_proto())
                else:
                    self._incoming_queue.put_nowait(resp)
                    self._state_changed.set()
        except Exception as exc:
            self._set_first_error(exc)

    async def send(self, req):
        self._check_error()
        if self._closed:
            raise issues.Error("Stream closed")
        await self._request_queue.put(req)

    def receive_nowait(self):
        self._check_error()
        if self._incoming_queue.empty():
            return None
        return self._incoming_queue.get_nowait()

    async def close(self):
        if self._closed:
            return
        self._closed = True

        for task in self._background_tasks:
            task.cancel()

        with contextlib.suppress(asyncio.CancelledError):
            await asyncio.gather(*self._background_tasks)

        if self._stream:
            try:
                self._stream.close()
            except Exception:
                pass

        self.session_id = None
        self._state_changed.set()

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
