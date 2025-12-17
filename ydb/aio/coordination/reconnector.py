import asyncio
import contextlib
from typing import Optional, Dict

from .stream import CoordinationStream
from ..._grpc.grpcwrapper.ydb_coordination import FromServer
from ... import issues


class CoordinationReconnector:
    def __init__(self, driver, node_path: str, timeout_millis: int = 30000):
        self._driver = driver
        self._node_path = node_path
        self._timeout_millis = timeout_millis

        self._stream: Optional[CoordinationStream] = None
        self._dispatch_task: Optional[asyncio.Task] = None

        self._wait_timeout = timeout_millis / 1000.0
        self._pending_futures: Dict[int, asyncio.Future] = {}
        self._ensure_lock = asyncio.Lock()

    async def stop(self):
        if self._dispatch_task:
            self._dispatch_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._dispatch_task
            self._dispatch_task = None

        if self._stream:
            with contextlib.suppress(Exception):
                await self._stream.close()
            self._stream = None

        if self._pending_futures:
            err = asyncio.CancelledError()
            for fut in self._pending_futures.values():
                if not fut.done():
                    fut.set_exception(err)
            self._pending_futures.clear()

    async def send_and_wait(self, req):
        await self._ensure_stream()

        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        self._pending_futures[req.req_id] = fut

        try:
            await self._stream.send(req)
        except Exception as exc:
            await self._pending_futures.pop(req.req_id, None)
            if not fut.done():
                fut.set_exception(exc)
            if self._stream:
                with contextlib.suppress(Exception):
                    await self._stream.close()
                self._stream = None
            raise

        try:
            return await asyncio.wait_for(
                asyncio.shield(fut),
                timeout=self._wait_timeout,
            )
        except Exception:
            await self._pending_futures.pop(req.req_id, None)
            raise

    async def _ensure_stream(self):
        async with self._ensure_lock:
            if self._stream is not None and not self._stream._closed:
                return

            if self._dispatch_task:
                self._dispatch_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self._dispatch_task
                self._dispatch_task = None

            if self._stream:
                with contextlib.suppress(Exception):
                    await self._stream.close()
                self._stream = None

            if self._pending_futures:
                err = issues.Error("Connection lost")
                for fut in self._pending_futures.values():
                    if not fut.done():
                        fut.set_exception(err)
                self._pending_futures.clear()

            stream = CoordinationStream(self._driver)
            await stream.start_session(self._node_path, self._timeout_millis)

            self._stream = stream

            loop = asyncio.get_running_loop()
            self._dispatch_task = loop.create_task(self._dispatch_loop(stream))

    async def _dispatch_loop(self, stream: CoordinationStream):
        try:
            while True:
                try:
                    resp = await stream.receive(self._wait_timeout)
                except asyncio.TimeoutError:
                    continue
                except Exception as exc:
                    await self._on_stream_error(stream, exc)
                    break

                if resp is None:
                    continue

                fs = FromServer.from_proto(resp)
                raw = fs.raw

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

                fut = self._pending_futures.pop(payload.req_id, None)
                if fut and not fut.done():
                    fut.set_result(payload)
        finally:
            if self._stream is stream:
                with contextlib.suppress(Exception):
                    await stream.close()
                self._stream = None

    async def _on_stream_error(self, stream: CoordinationStream, exc: Exception):
        if self._pending_futures:
            for fut in self._pending_futures.values():
                if not fut.done():
                    fut.set_exception(exc)
            self._pending_futures.clear()

        if self._stream is stream:
            with contextlib.suppress(Exception):
                await stream.close()
            self._stream = None
