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

        self._ready = asyncio.Event()
        self._stopped = False

        self._first_error: asyncio.Future = asyncio.get_running_loop().create_future()
        self._state_changed = asyncio.Event()

    def start(self):
        if self._stopped:
            return
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._connection_loop())

    async def stop(self):
        self._stopped = True

        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

        if self._stream:
            await self._stream.close()
            self._stream = None

        self._ready.clear()

    async def wait_ready(self):
        await self._ready.wait()

    def get_stream(self) -> CoordinationStream:
        if self._stream is None or self._stream.session_id is None:
            raise RuntimeError("Coordination stream is not ready")
        return self._stream

    async def _connection_loop(self):
        attempt = 0
        backoff = 0.1

        while not self._stopped:
            try:
                stream = CoordinationStream(
                    self._driver,
                    self._request_queue,
                )

                await stream.start_session(
                    self._node_path,
                    self._timeout_millis,
                )

                self._stream = stream
                self._ready.set()

                await asyncio.wait(
                    stream._background_tasks,
                    return_when=asyncio.FIRST_EXCEPTION,
                )

            except asyncio.CancelledError:
                break

            except Exception as exc:
                self._ready.clear()
                self._stream = None

                if not self._first_error.done():
                    self._first_error.set_result(exc)
                    self._state_changed.set()

                if self._stopped:
                    break

                await asyncio.sleep(backoff)
                attempt += 1
                backoff = min(backoff * 2, 3.0)

            finally:
                if self._stream:
                    await self._stream.close()
                    self._stream = None
