from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import Optional, Dict

from ... import issues
from ..._grpc.grpcwrapper.common_utils import IToProto
from ..._grpc.grpcwrapper.ydb_coordination import FromServer
from .stream import CoordinationStream

logger = logging.getLogger(__name__)


class CoordinationReconnector:
    def __init__(self, driver, node_path: str, timeout_millis: int = 30000):
        self._driver = driver
        self._node_path = node_path
        self._timeout_millis = timeout_millis
        self._wait_timeout = timeout_millis / 1000.0

        self._stream: Optional[CoordinationStream] = None

        self._pending_futures: Dict[int, asyncio.Future] = {}
        self._pending_requests: Dict[int, IToProto] = {}

        self._send_lock = asyncio.Lock()
        self._state_changed = asyncio.Event()

        self._closed = False
        self._connection_task: Optional[asyncio.Task] = None

        self._session_id: Optional[int] = None

    async def stop(self):
        if self._closed:
            return
        self._closed = True

        if self._connection_task is not None:
            self._connection_task.cancel()
            with contextlib.suppress(asyncio.CancelledError, RuntimeError):
                await self._connection_task
            self._connection_task = None

        if self._stream is not None:
            with contextlib.suppress(Exception, RuntimeError):
                await self._stream.close()
            self._stream = None

        self._fail_all_pending(asyncio.CancelledError())
        self._state_changed.set()

    async def send_and_wait(self, req: IToProto):
        if self._closed:
            raise issues.Error("CoordinationReconnector is closed")

        await self._ensure_connection_loop_started()
        await self._wait_ready_stream()

        loop = asyncio.get_running_loop()
        fut = loop.create_future()

        self._pending_futures[req.req_id] = fut
        self._pending_requests[req.req_id] = req

        try:
            await self._safe_send(req)
        except BaseException as exc:
            await self._trigger_reconnect(exc)

        try:
            return await asyncio.wait_for(asyncio.shield(fut), timeout=self._wait_timeout)
        except Exception:
            self._pending_requests.pop(req.req_id, None)
            self._pending_futures.pop(req.req_id, None)
            raise

    async def _ensure_connection_loop_started(self):
        if self._connection_task is not None:
            return
        asyncio.get_running_loop()
        self._connection_task = asyncio.create_task(self._connection_loop())

    async def _connection_loop(self):
        attempt = 0
        while not self._closed:
            try:
                logger.debug(
                    "Connecting coordination session (restore session_id=%r, pending=%d)",
                    self._session_id,
                    len(self._pending_requests),
                )

                stream = CoordinationStream(self._driver)
                await stream.start_session(
                    self._node_path,
                    self._timeout_millis,
                    session_id=self._session_id,
                )

                self._session_id = stream.session_id

                self._stream = stream
                attempt = 0
                self._state_changed.set()

                await self._resend_pending()
                await self._dispatch_loop(stream)

            except asyncio.CancelledError:
                return
            except BaseException as err:
                err = self._normalize_stream_error(err)
                attempt += 1
                logger.warning("Reconnect failed: %r", err)
                await asyncio.sleep(min(0.1 * attempt, 2.0))
            finally:
                if self._stream is not None:
                    self._session_id = self._session_id or getattr(self._stream, "session_id", None)
                    with contextlib.suppress(Exception):
                        await self._stream.close()
                    self._stream = None
                self._state_changed.set()

    async def _wait_ready_stream(self):
        while True:
            if self._closed:
                raise issues.Error("CoordinationReconnector is closed")

            if self._stream is not None and not self._stream._closed:
                return

            await self._state_changed.wait()
            self._state_changed.clear()

    async def _trigger_reconnect(self, exc: BaseException):
        exc = self._normalize_stream_error(exc)
        logger.warning("Coordination stream error: %r. Triggering reconnect.", exc)

        if self._stream is not None:
            self._session_id = self._session_id or getattr(self._stream, "session_id", None)
            with contextlib.suppress(Exception):
                await self._stream.close()

        self._stream = None
        self._state_changed.set()

    async def _safe_send(self, req: IToProto):
        async with self._send_lock:
            if self._stream is None or self._stream._closed:
                raise issues.Error("Stream is not ready")
            await self._stream.send(req)

    async def _resend_pending(self):
        if self._stream is None or self._stream._closed:
            return

        async with self._send_lock:
            if self._stream is None or self._stream._closed:
                return

            for req_id, req in list(self._pending_requests.items()):
                fut = self._pending_futures.get(req_id)
                if fut is None or fut.done():
                    self._pending_requests.pop(req_id, None)
                    continue

                try:
                    await self._stream.send(req)
                except BaseException as exc:
                    await self._trigger_reconnect(exc)
                    return

    async def _dispatch_loop(self, stream: CoordinationStream):
        while not self._closed:
            if self._stream is not stream:
                return

            try:
                resp = await stream.receive(self._wait_timeout)
            except asyncio.TimeoutError:
                continue
            except BaseException as exc:
                await self._trigger_reconnect(exc)
                return

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
            self._pending_requests.pop(payload.req_id, None)

            if fut is not None and not fut.done():
                fut.set_result(payload)

    def _fail_all_pending(self, exc: BaseException):
        if not self._pending_futures:
            return
        for fut in list(self._pending_futures.values()):
            if not fut.done():
                fut.set_exception(exc)
        self._pending_futures.clear()
        self._pending_requests.clear()

    @staticmethod
    def _normalize_stream_error(err: BaseException) -> BaseException:
        if isinstance(err, (StopIteration, StopAsyncIteration)):
            return issues.Error("Stream closed")
        return err
