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

        # pending futures by req_id
        self._pending_futures: Dict[int, asyncio.Future] = {}

        # чтобы не создавать несколько стримов параллельно
        self._ensure_lock = asyncio.Lock()

        logger.debug("[CoordinationReconnector] init node_path=%s timeout=%s", node_path, timeout_millis)

    # --------------------
    # PUBLIC API
    # --------------------

    async def stop(self):
        logger.debug("[CoordinationReconnector] stop() called")

        # cancel dispatch loop
        if self._dispatch_task:
            self._dispatch_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._dispatch_task
            self._dispatch_task = None

        # close stream
        if self._stream:
            with contextlib.suppress(Exception):
                await self._stream.close()
            self._stream = None

        # fail pending futures
        for fut in self._pending_futures.values():
            if not fut.done():
                fut.set_exception(asyncio.CancelledError())
        self._pending_futures.clear()

    async def send_and_wait(self, req):
        """
        Отправить запрос и дождаться ответа с тем же req_id.

        Если стрим отсутствует или сломан — лениво создаём новый.
        """
        await self._ensure_stream()

        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        self._pending_futures[req.req_id] = fut

        logger.debug("[CoordinationReconnector] send req_id=%s req=%s", req.req_id, req)
        try:
            await self._stream.send(req)
        except Exception as exc:
            # немедленный провал отправки: чистим future и закрываем стрим
            logger.exception("[CoordinationReconnector] send failed for req_id=%s: %s", req.req_id, exc)
            await self._pending_futures.pop(req.req_id, None)
            if not fut.done():
                fut.set_exception(exc)

            # текущий стрим считаем умершим, закроем его
            if self._stream:
                with contextlib.suppress(Exception):
                    await self._stream.close()
                self._stream = None
            raise

        try:
            # ждём ответ, shield — чтобы не убить внутреннюю логику при внешней отмене таска
            result = await asyncio.wait_for(asyncio.shield(fut), timeout=self._wait_timeout)
            logger.debug("[CoordinationReconnector] got result for req_id=%s", req.req_id)
            return result
        except Exception:
            # timeout / cancel / другое — убираем future из словаря и пробрасываем
            await self._pending_futures.pop(req.req_id, None)
            raise

    # --------------------
    # INTERNAL
    # --------------------

    async def _ensure_stream(self):
        """
        Убедиться, что есть живой CoordinationStream.

        Если:
          - стрима нет, или
          - он уже закрыт,
        то создаём новый, стартуем session и запускаем _dispatch_loop.
        """
        async with self._ensure_lock:
            # double-check под локом
            if self._stream is not None and not self._stream._closed:
                return

            logger.debug("[CoordinationReconnector] ensuring stream: creating new CoordinationStream")

            # на всякий случай прибираем старые сущности
            if self._dispatch_task:
                self._dispatch_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self._dispatch_task
                self._dispatch_task = None

            if self._stream:
                with contextlib.suppress(Exception):
                    await self._stream.close()
                self._stream = None

            # при обрыве соединения — заваливаем все pending futures
            if self._pending_futures:
                err = issues.Error("Connection lost")
                for fut in self._pending_futures.values():
                    if not fut.done():
                        fut.set_exception(err)
                self._pending_futures.clear()

            # создаём новый CoordinationStream
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

            # запускаем диспетчер этого стрима
            self._dispatch_task = asyncio.create_task(self._dispatch_loop(stream))
            logger.debug("[CoordinationReconnector] dispatch loop started")

    async def _dispatch_loop(self, stream: CoordinationStream):
        """
        Получаем FromServer и маппим по req_id на futures.
        Привязан к конкретному stream. При любой фатальной ошибке — выходим.
        """
        logger.debug("[CoordinationReconnector] _dispatch_loop entered (session_id=%s)", stream.session_id)
        try:
            while True:
                try:
                    resp = await stream.receive(self._wait_timeout)
                except asyncio.TimeoutError:
                    # нет сообщений — просто ждём дальше
                    continue
                except asyncio.CancelledError:
                    logger.debug("[CoordinationReconnector] _dispatch_loop cancelled")
                    break
                except Exception as exc:
                    logger.exception("[CoordinationReconnector] _dispatch_loop receive error: %s", exc)
                    # считаем стрим мёртвым, пусть следующая send_and_wait() пересоздаст
                    await self._on_stream_error(stream, exc)
                    break

                if resp is None:
                    continue

                try:
                    fs = FromServer.from_proto(resp)
                    raw = fs.raw
                except Exception:
                    logger.exception("[CoordinationReconnector] Failed to parse FromServer")
                    continue

                # определяем тип ответа
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
                    # это может быть pong или другой служебный ответ — игнорируем
                    continue

                req_id = getattr(payload, "req_id", None)
                if req_id is None:
                    continue

                fut = self._pending_futures.pop(req_id, None)
                if fut and not fut.done():
                    fut.set_result(payload)
                    logger.debug("[CoordinationReconnector] completed req_id=%s", req_id)

        finally:
            # если этот стрим всё ещё текущий — помечаем, что его нет
            if self._stream is stream:
                logger.debug("[CoordinationReconnector] _dispatch_loop finished, clearing current stream")
                self._stream = None
            # не трогаем _dispatch_task здесь — её обнуляет _ensure_stream/stop при необходимости

    async def _on_stream_error(self, stream: CoordinationStream, exc: Exception):
        """
        Обработка ошибки стрима: пробрасываем её всем pending futures и закрываем стрим.
        """
        # отдаём ошибку всем, кто ждёт ответ
        for fut in self._pending_futures.values():
            if not fut.done():
                fut.set_exception(exc)
        self._pending_futures.clear()

        if self._stream is stream:
            with contextlib.suppress(Exception):
                await stream.close()
            self._stream = None
        logger.debug("[CoordinationReconnector] stream error handled, stream closed")


