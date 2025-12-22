from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import Optional, Set

from ... import issues, _apis
from ..._grpc.grpcwrapper.common_utils import IToProto, GrpcWrapperAsyncIO
from ..._grpc.grpcwrapper.ydb_coordination import FromServer, Ping, SessionStart

logger = logging.getLogger(__name__)


class CoordinationStream:
    def __init__(self, driver):
        self._driver = driver
        self._stream: Optional[GrpcWrapperAsyncIO] = GrpcWrapperAsyncIO(FromServer.from_proto)

        self._background_tasks: Set[asyncio.Task] = set()
        self._incoming_queue: asyncio.Queue = asyncio.Queue()

        self._closed = False
        self._started = False
        self.session_id: Optional[int] = None

    @staticmethod
    def _extract_session_id(session_started_obj) -> int:
        if session_started_obj is None:
            raise issues.Error("Empty session_started in response")

        sid = getattr(session_started_obj, "session_id", None)
        if sid is not None:
            return int(sid)

        try:
            return int(session_started_obj)
        except Exception as exc:
            raise issues.Error(f"Unexpected session_started type: {type(session_started_obj)!r}") from exc

    async def start_session(self, path: str, timeout_millis: int, session_id: Optional[int] = None):
        if self._started:
            raise issues.Error("CoordinationStream already started")

        self._started = True

        await self._stream.start(
            self._driver,
            _apis.CoordinationService.Stub,
            _apis.CoordinationService.Session,
        )

        if session_id is None:
            self._stream.write(SessionStart(path=path, timeout_millis=timeout_millis))
        else:
            self._stream.write(SessionStart(path=path, timeout_millis=timeout_millis, session_id=int(session_id)))

        try:
            while True:
                try:
                    resp = await self._stream.receive(timeout=3, is_coordination_calls=True)
                except asyncio.TimeoutError:
                    raise issues.Error("Timeout waiting for SessionStart response")
                except StopAsyncIteration:
                    raise issues.Error("Stream closed while waiting for SessionStart response")
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    raise issues.Error(f"Failed to start session: {exc}") from exc

                if resp is None:
                    continue

                ss = getattr(resp, "session_started", None)
                if ss:
                    self.session_id = self._extract_session_id(ss)
                    break

        except Exception:
            with contextlib.suppress(Exception):
                await self._stream.close()
            self._stream = None
            self._started = False
            raise

        loop = asyncio.get_running_loop()
        task = loop.create_task(self._reader_loop())
        self._background_tasks.add(task)

        def _on_done(t: asyncio.Task) -> None:
            self._background_tasks.discard(t)
            with contextlib.suppress(asyncio.CancelledError):
                _ = t.exception()

        task.add_done_callback(_on_done)

    async def _reader_loop(self):
        try:
            while True:
                try:
                    resp = await self._stream.receive(timeout=3, is_coordination_calls=True)
                except asyncio.TimeoutError:
                    continue
                except asyncio.CancelledError:
                    break
                except StopAsyncIteration:
                    break
                except Exception:
                    break

                if self._closed:
                    break

                if resp is None:
                    continue

                fs = FromServer.from_proto(resp)

                if fs.opaque:
                    try:
                        self._stream.write(Ping(fs.opaque))
                    except Exception:
                        break
                else:
                    await self._incoming_queue.put(resp)
        finally:
            if not self._closed:
                self._closed = True
                with contextlib.suppress(asyncio.QueueFull):
                    self._incoming_queue.put_nowait(None)

            if self._stream is not None:
                with contextlib.suppress(Exception):
                    await self._stream.close()
                self._stream = None

    async def send(self, req: IToProto):
        if self._closed:
            raise issues.Error("Stream closed")
        self._stream.write(req)

    async def receive(self, timeout: Optional[float] = None):
        if self._closed:
            raise issues.Error("Stream closed")

        if timeout is None:
            return await self._incoming_queue.get()

        return await asyncio.wait_for(self._incoming_queue.get(), timeout=timeout)

    async def close(self):
        if self._closed:
            return

        self._closed = True

        for t in list(self._background_tasks):
            t.cancel()
        if self._background_tasks:
            with contextlib.suppress(Exception):
                await asyncio.gather(*self._background_tasks, return_exceptions=True)
        self._background_tasks.clear()

        with contextlib.suppress(asyncio.QueueFull):
            self._incoming_queue.put_nowait(None)

        if self._stream is not None:
            with contextlib.suppress(Exception):
                await self._stream.close()
            self._stream = None
