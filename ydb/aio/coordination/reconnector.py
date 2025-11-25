import asyncio
import contextlib
from typing import Optional

from ydb.aio.coordination.stream import CoordinationStream


class CoordinationReconnector:
    def __init__(
        self,
        driver,
        request_queue: asyncio.Queue,
        node_path: str,
        timeout_millis: int,
    ):
        self._driver = driver
        self._request_queue = request_queue
        self._node_path = node_path
        self._timeout_millis = timeout_millis

        self._task: Optional[asyncio.Task] = None
        self._stream: Optional[CoordinationStream] = None

        self._ready: Optional[asyncio.Event] = None
        self._stopped = False
        self._first_error: Optional[Exception] = None

    def start(self):
        if self._stopped:
            return

        if self._ready is None:
            self._ready = asyncio.Event()

        self._first_error = None

        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._connection_loop())

    async def stop(self, flush: bool):
        self._stopped = True

        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

        if self._stream:
            with contextlib.suppress(Exception):
                await self._stream.close()
            self._stream = None

        if self._ready:
            self._ready.clear()

    async def wait_ready(self):
        if self._first_error:
            raise self._first_error
        if not self._ready:
            raise RuntimeError("Reconnector not started")
        await self._ready.wait()
        if self._first_error:
            raise self._first_error

    def get_stream(self) -> CoordinationStream:
        if self._stream is None or self._stream.session_id is None:
            raise RuntimeError("Coordination stream is not ready")
        return self._stream

    async def _connection_loop(self):
        if self._stopped:
            return

        try:
            self._stream = CoordinationStream(self._driver)
            await self._stream.start_session(self._node_path, self._timeout_millis)
            if self._ready:
                self._ready.set()

            if self._stream._background_tasks:
                done, pending = await asyncio.wait(
                    self._stream._background_tasks,
                    return_when=asyncio.FIRST_EXCEPTION,
                )

                for d in done:
                    if d.cancelled():
                        continue
                    exc = d.exception()
                    if exc:
                        raise exc

        except Exception as exc:
            self._first_error = exc
            if self._ready:
                self._ready.clear()
            if self._stream:
                with contextlib.suppress(Exception):
                    await self._stream.close()
            self._stream = None
