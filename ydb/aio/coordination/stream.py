import asyncio
import contextlib
from typing import Optional, Set

from ... import issues, _apis
from ..._grpc.grpcwrapper.common_utils import IToProto, GrpcWrapperAsyncIO
from ..._grpc.grpcwrapper.ydb_coordination import FromServer, Ping, SessionStart


class CoordinationStream:
    def __init__(self, driver):
        self._driver = driver
        self._stream: Optional[GrpcWrapperAsyncIO] = GrpcWrapperAsyncIO(
            FromServer.from_proto
        )
        self._background_tasks: Set[asyncio.Task] = set()
        self._incoming_queue: asyncio.Queue = asyncio.Queue()
        self._closed = False
        self._started = False
        self.session_id: Optional[int] = None

    async def start_session(self, path: str, timeout_millis: int):
        if self._started:
            raise issues.Error("CoordinationStream already started")

        self._started = True

        await self._stream.start(
            self._driver,
            _apis.CoordinationService.Stub,
            _apis.CoordinationService.Session,
        )

        # initial handshake
        self._stream.write(SessionStart(path=path, timeout_millis=timeout_millis))

        while True:
            try:
                resp = await self._stream.receive(timeout=3)
            except asyncio.TimeoutError:
                raise issues.Error("Timeout waiting for SessionStart response")
            except StopAsyncIteration:
                raise issues.Error("Stream closed while waiting for SessionStart response")
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                raise issues.Error(f"Failed to start session: {exc}") from exc

            if resp is None:
                # защита от странных ситуаций — подождём ещё
                continue

            if getattr(resp, "session_started", None):
                self.session_id = resp.session_started
                break

        # запускаем фонового читателя
        loop = asyncio.get_running_loop()
        task = loop.create_task(self._reader_loop())
        self._background_tasks.add(task)

        def _on_done(t: asyncio.Task) -> None:
            # убрать таск из набора и прочитать exception,
            # чтобы не было "Task exception was never retrieved"
            self._background_tasks.discard(t)
            with contextlib.suppress(asyncio.CancelledError, Exception):
                _ = t.exception()

        task.add_done_callback(_on_done)

    async def _reader_loop(self):
        try:
            while True:
                try:
                    resp = await self._stream.receive(timeout=3)
                except asyncio.TimeoutError:
                    # тишина — просто ждём дальше
                    continue
                except asyncio.CancelledError:
                    break
                except StopAsyncIteration:
                    # сервер закрыл grpc-стрим
                    break
                except Exception:
                    # любая другая ошибка — тихо вываливаемся
                    break

                if self._closed:
                    break

                if resp is None:
                    # например, таймаут из receive()
                    continue

                fs = FromServer.from_proto(resp)
                if fs.opaque:
                    # keep-alive ping
                    try:
                        self._stream.write(Ping(fs.opaque))
                    except Exception:
                        # не поднимаем ошибку наружу, просто выходим
                        break
                else:
                    await self._incoming_queue.put(resp)
        finally:
            # если reader закончился сам (по StopAsyncIteration/ошибке),
            # помечаем стрим закрытым и будим ожидающих на очереди
            if not self._closed:
                self._closed = True
                with contextlib.suppress(asyncio.QueueFull):
                    self._incoming_queue.put_nowait(None)

    async def send(self, req: IToProto):
        if self._closed:
            raise issues.Error("Stream closed")
        self._stream.write(req)

    async def receive(self, timeout: Optional[float] = None):
        if self._closed:
            # важно: если нас закрыли, больше ничего не ждём
            raise issues.Error("Stream closed")

        try:
            if timeout is not None:
                return await asyncio.wait_for(self._incoming_queue.get(), timeout)
            return await self._incoming_queue.get()
        except asyncio.TimeoutError:
            # старый контракт: на таймаут возвращаем None
            return None

    async def close(self):
        if self._closed:
            return

        self._closed = True

        # разбудим хотя бы одного ожидающего receive(), чтобы он смог корректно завершиться
        with contextlib.suppress(asyncio.QueueFull):
            self._incoming_queue.put_nowait(None)

        # отменяем фоновые таски и ждём их завершения
        if self._background_tasks:
            for task in list(self._background_tasks):
                task.cancel()

            with contextlib.suppress(asyncio.CancelledError):
                await asyncio.gather(*self._background_tasks, return_exceptions=True)

            self._background_tasks.clear()

        # закрываем grpc-стрим
        if self._stream is not None:
            with contextlib.suppress(Exception):
                self._stream.close()
            self._stream = None

        # подчистим очередь
        while not self._incoming_queue.empty():
            with contextlib.suppress(asyncio.QueueEmpty):
                self._incoming_queue.get_nowait()

        self.session_id = None
