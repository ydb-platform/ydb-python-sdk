import asyncio
import contextlib
from typing import Optional, Dict

from ...aio.coordination.stream import CoordinationStream
from ..._grpc.grpcwrapper.ydb_coordination import FromServer
from ... import issues
import logging

logger = logging.getLogger(__name__)


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

        logger.debug(
            "[CoordinationReconnector] init node_path=%s timeout_millis=%s",
            node_path,
            timeout_millis,
        )

    async def stop(self):
        logger.debug("[CoordinationReconnector] stop() called")

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
        fut: asyncio.Future = loop.create_future()
        self._pending_futures[req.req_id] = fut

        logger.debug("[CoordinationReconnector] send req_id=%s req=%s", req.req_id, req)
        try:
            await self._stream.send(req)
        except Exception as exc:
            logger.exception(
                "[CoordinationReconnector] send failed for req_id=%s: %s",
                req.req_id,
                exc,
            )
            await self._pending_futures.pop(req.req_id, None)
            if not fut.done():
                fut.set_exception(exc)

            if self._stream:
                with contextlib.suppress(Exception):
                    await self._stream.close()
                self._stream = None
            raise

        try:
            result = await asyncio.wait_for(
                asyncio.shield(fut),
                timeout=self._wait_timeout,
            )
            logger.debug(
                "[CoordinationReconnector] got result for req_id=%s",
                req.req_id,
            )
            return result
        except Exception:
            await self._pending_futures.pop(req.req_id, None)
            raise

    async def _ensure_stream(self):
        async with self._ensure_lock:
            if self._stream is not None and not self._stream._closed:
                return

            logger.debug("[CoordinationReconnector] ensuring stream: creating new CoordinationStream")

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
            logger.debug(
                "[CoordinationReconnector] starting session path=%s timeout_millis=%s",
                self._node_path,
                self._timeout_millis,
            )
            await stream.start_session(self._node_path, self._timeout_millis)
            logger.debug(
                "[CoordinationReconnector] session started, session_id=%s",
                stream.session_id,
            )

            self._stream = stream

            loop = asyncio.get_running_loop()
            dispatch_task = loop.create_task(self._dispatch_loop(stream))
            self._dispatch_task = dispatch_task

            def _on_done(t: asyncio.Task) -> None:
                with contextlib.suppress(asyncio.CancelledError, Exception):
                    _ = t.exception()
                if self._dispatch_task is t:
                    self._dispatch_task = None

            dispatch_task.add_done_callback(_on_done)

            logger.debug("[CoordinationReconnector] dispatch loop started")

    async def _dispatch_loop(self, stream: CoordinationStream):
        logger.debug(
            "[CoordinationReconnector] _dispatch_loop entered (session_id=%s)",
            stream.session_id,
        )
        try:
            while True:
                try:
                    resp = await stream.receive(self._wait_timeout)
                except asyncio.TimeoutError:
                    continue
                except asyncio.CancelledError:
                    logger.debug("[CoordinationReconnector] _dispatch_loop cancelled")
                    break
                except issues.Error as exc:
                    logger.debug(
                        "[CoordinationReconnector] _dispatch_loop issues.Error: %s",
                        exc,
                    )
                    await self._on_stream_error(stream, exc)
                    break
                except Exception as exc:
                    logger.exception(
                        "[CoordinationReconnector] _dispatch_loop receive error: %s",
                        exc,
                    )
                    await self._on_stream_error(stream, exc)
                    break

                if resp is None:
                    if getattr(stream, "_closed", False):
                        logger.debug("[CoordinationReconnector] stream closed, leaving _dispatch_loop")
                        break
                    continue

                try:
                    fs = FromServer.from_proto(resp)
                    raw = fs.raw
                except Exception:
                    logger.exception("[CoordinationReconnector] Failed to parse FromServer")
                    continue

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
                if req_id is None:
                    continue

                fut = self._pending_futures.pop(req_id, None)
                if fut and not fut.done():
                    fut.set_result(payload)
                    logger.debug(
                        "[CoordinationReconnector] completed req_id=%s",
                        req_id,
                    )
        finally:
            logger.debug("[CoordinationReconnector] _dispatch_loop finished")
            if self._stream is stream:
                with contextlib.suppress(Exception):
                    await stream.close()
                self._stream = None
                logger.debug("[CoordinationReconnector] stream closed in _dispatch_loop finally")

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

        logger.debug("[CoordinationReconnector] stream error handled, stream closed: %s", exc)
