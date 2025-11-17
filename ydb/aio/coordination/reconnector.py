import asyncio
import contextlib
from typing import Optional

from ydb.aio.coordination.stream import CoordinationStream


class CoordinationReconnector:
    def __init__(self, client):
        self._client = client
        self._task: Optional[asyncio.Task] = None
        self._first_error: asyncio.Future = asyncio.get_running_loop().create_future()
        self._state_changed = asyncio.Event()

    def start(self):
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._connection_loop())

    async def stop(self):
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

        if self._client._stream:
            await self._client._stream.close()
            self._client._stream = None

    async def _connection_loop(self):
        attempt = 0
        backoff = 0.1
        while not self._client._closed.is_set():
            try:
                self._client._stream = CoordinationStream(
                    self._client._driver, self._client._request_queue
                )
                await self._client._stream.start()
                self._client.session_id = self._client._stream.session_id
                self._client._session_ready.set()

                await asyncio.wait(self._client._stream._background_tasks, return_when=asyncio.FIRST_EXCEPTION)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self._client.session_id = None
                self._client._session_ready.clear()
                if not self._first_error.done():
                    self._first_error.set_result(exc)
                await asyncio.sleep(backoff)
                attempt += 1
                backoff = min(backoff * 2, 3.0)
            finally:
                if self._client._stream:
                    await self._client._stream.close()
                    self._client._stream = None