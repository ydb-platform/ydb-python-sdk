# coordination_reconnector.py
import asyncio
import contextlib
from typing import Optional

from ydb.aio.coordination.stream import CoordinationStream
from ydb._grpc.grpcwrapper.ydb_coordination import FromServer


class CoordinationReconnector:
    def __init__(self, driver, node_path: str, timeout_millis: int = 30000):
        self._driver = driver
        self._node_path = node_path
        self._timeout_millis = timeout_millis

        self._stream: Optional[CoordinationStream] = None
        self._task: Optional[asyncio.Task] = None
        self._dispatch_task: Optional[asyncio.Task] = None
        self._ready: Optional[asyncio.Event] = None

        self._stopped = False
        self._first_error: Optional[Exception] = None
        self._wait_timeout = timeout_millis / 1000.0
        self._pending_futures = {}

    def start(self):
        if self._stopped:
            return
        if self._ready is None:
            self._ready = asyncio.Event()
        self._first_error = None
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._connection_loop())

    async def stop(self, flush=True):
        self._stopped = True
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        if self._dispatch_task:
            self._dispatch_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._dispatch_task
            self._dispatch_task = None
        if self._stream:
            with contextlib.suppress(Exception):
                await self._stream.close()
            self._stream = None
        if self._ready:
            self._ready.clear()
        for fut in self._pending_futures.values():
            if not fut.done():
                fut.set_exception(asyncio.CancelledError())
        self._pending_futures.clear()

    async def send_and_wait(self, req):
        self.start()
        if self._first_error:
            raise self._first_error
        if not self._ready:
            raise RuntimeError("Reconnector not started")
        await self._ready.wait()
        if self._first_error:
            raise self._first_error

        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        self._pending_futures[req.req_id] = fut
        await self._stream.send(req)
        return await asyncio.wait_for(asyncio.shield(fut), timeout=self._wait_timeout)


    async def _connection_loop(self):
        if self._stopped:
            return
        try:
            self._stream = CoordinationStream(self._driver)
            await self._stream.start_session(self._node_path, self._timeout_millis)

            if self._ready:
                self._ready.set()

            if self._dispatch_task is None or self._dispatch_task.done():
                self._dispatch_task = asyncio.create_task(self._dispatch_loop())

            if getattr(self._stream, "_background_tasks", None):
                done, pending = await asyncio.wait(
                    list(self._stream._background_tasks),
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

        finally:
            if self._dispatch_task:
                if not self._dispatch_task.done():
                    self._dispatch_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await self._dispatch_task
                self._dispatch_task = None

            if self._stream:
                with contextlib.suppress(Exception):
                    await self._stream.close()
                self._stream = None

    async def _dispatch_loop(self):
        while True:
            try:
                resp = await self._stream.receive(self._wait_timeout)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                for fut in self._pending_futures.values():
                    if not fut.done():
                        fut.set_exception(exc)
                self._pending_futures.clear()
                with contextlib.suppress(Exception):
                    await self._stream.close()
                break

            if resp is None:
                continue

            try:
                fs = FromServer.from_proto(resp)
                raw = fs.raw
            except Exception as exc:
                for fut in self._pending_futures.values():
                    if not fut.done():
                        fut.set_exception(exc)
                self._pending_futures.clear()
                with contextlib.suppress(Exception):
                    await self._stream.close()
                break

            payload = None
            for field_name in (
                    "acquire_semaphore_result",
                    "release_semaphore_result",
                    "describe_semaphore_result",
                    "create_semaphore_result",
                    "update_semaphore_result",
                    "delete_semaphore_result",
            ):
                if raw.HasField(field_name):
                    payload = getattr(fs, field_name)
                    break
            if payload is None:
                continue

            req_id = getattr(payload, "req_id", None)
            if req_id is not None:
                fut = self._pending_futures.pop(req_id, None)
                if isinstance(fut, asyncio.Future) and not fut.done():
                    fut.set_result(payload)
