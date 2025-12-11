import asyncio
import contextlib
from typing import Optional, Set

from ... import issues, _apis
from ..._grpc.grpcwrapper.common_utils import IToProto, GrpcWrapperAsyncIO
from ..._grpc.grpcwrapper.ydb_coordination import FromServer, Ping, SessionStart


class CoordinationStream:
    def __init__(self, driver):
        self._driver = driver
        self._stream: GrpcWrapperAsyncIO = GrpcWrapperAsyncIO(FromServer.from_proto)
        self._background_tasks: Set[asyncio.Task] = set()
        self._incoming_queue: asyncio.Queue = asyncio.Queue()
        self._closed = False
        self._started = False
        self.session_id: Optional[int] = None

    async def start_session(self, path: str, timeout_millis: int):
        if self._started:
            raise issues.Error("CoordinationStream already started")

        print("[CoordinationStream] Starting session...")
        self._started = True
        await self._stream.start(self._driver, _apis.CoordinationService.Stub, _apis.CoordinationService.Session)

        print(f"[CoordinationStream] Writing SessionStart for path {path}")
        self._stream.write(SessionStart(path=path, timeout_millis=timeout_millis))

        while True:
            try:
                print("[CoordinationStream] Waiting for SessionStart response...")
                resp = await self._stream.receive(timeout=3)
                print(f"[CoordinationStream] Received response: {resp}")

                if resp.session_started:
                    self.session_id = resp.session_started
                    print(f"[CoordinationStream] Session started: {self.session_id}")
                    break
                else:
                    print("[CoordinationStream] Response received but session not started, continuing...")
                    continue
            except asyncio.TimeoutError:
                print("[CoordinationStream] Timeout waiting for SessionStart response")
                raise issues.Error("Timeout waiting for SessionStart response")
            except Exception as e:
                print(f"[CoordinationStream] Exception during start_session: {e}")
                raise issues.Error(f"Failed to start session: {e}")

        print("[CoordinationStream] Starting reader loop task...")
        task = asyncio.get_running_loop().create_task(self._reader_loop())
        self._background_tasks.add(task)

    async def _reader_loop(self):
        while True:
            try:
                resp = await self._stream.receive(timeout=3)
                if self._closed:
                    break

                fs = FromServer.from_proto(resp)
                if fs.opaque:
                    try:
                        self._stream.write(Ping(fs.opaque))
                    except Exception:
                        raise issues.Error("Failed to write Ping")
                else:
                    await self._incoming_queue.put(resp)
            except asyncio.CancelledError:
                break

    async def send(self, req: IToProto):
        if self._closed:
            raise issues.Error("Stream closed")
        self._stream.write(req)

    async def receive(self, timeout: Optional[float] = None):
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

        # Завершаем все background tasks
        for task in list(self._background_tasks):
            task.cancel()

        with contextlib.suppress(asyncio.CancelledError):
            await asyncio.gather(*self._background_tasks, return_exceptions=True)

        self._background_tasks.clear()

        # Закрываем GRPC stream
        if self._stream:
            self._stream.close()
            self._stream = None

        # Чистим очередь, освобождая "висящие" get()
        while not self._incoming_queue.empty():
            try:
                self._incoming_queue.get_nowait()
            except Exception:
                break

        self.session_id = None

