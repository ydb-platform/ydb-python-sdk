import asyncio
import logging
from typing import Optional

from ydb import issues
from ydb._topic_common.common import _get_shared_event_loop, CallFromSyncToAsync
from ydb.aio.coordination.lock import CoordinationLock

logger = logging.getLogger(__name__)


class CoordinationLockSync:
    def __init__(
        self,
        client,
        name: str,
        node_path: Optional[str] = None,
        count: int = 1,
        timeout_millis: int = 30000,
        *,
        eventloop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        self._closed = False
        self._name = name
        self.loop = eventloop or _get_shared_event_loop()
        self._caller = CallFromSyncToAsync(self.loop)
        self._timeout_sec = timeout_millis / 1000.0
        self._client = client
        self._node_path = node_path
        self._count = count
        self._timeout_millis = timeout_millis

        async def create_reader():
            return CoordinationLock(self._client, self._name, self._node_path)

        # Инициализация асинхронного reader
        self._async_reader = asyncio.run_coroutine_threadsafe(create_reader(), self.loop).result()

    def _check_closed(self):
        if self._closed:
            raise issues.Error(f"CoordinationLockSync {self._name} already closed")

    # ------------------ Контекстный менеджер ------------------ #
    def __enter__(self):
        self.acquire(timeout=self._timeout_sec)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # ------------------ Основные методы ------------------ #
    def acquire(self, timeout: Optional[float] = None):
        self._check_closed()
        return self._caller.safe_call_with_result(self._async_reader.acquire(), timeout or self._timeout_sec)

    def release(self, timeout: Optional[float] = None):
        self._check_closed()
        return self._caller.safe_call_with_result(self._async_reader.release(), timeout or self._timeout_sec)

    def create(self, init_limit: int, init_data: bytes, timeout: Optional[float] = None):
        self._check_closed()
        return self._caller.safe_call_with_result(self._async_reader.create(init_limit, init_data), timeout or self._timeout_sec)

    def delete(self, timeout: Optional[float] = None):
        self._check_closed()
        return self._caller.safe_call_with_result(self._async_reader.delete(), timeout or self._timeout_sec)

    def describe(self, timeout: Optional[float] = None):
        self._check_closed()
        return self._caller.safe_call_with_result(self._async_reader.describe(), timeout or self._timeout_sec)

    def update(self, new_data: bytes, timeout: Optional[float] = None):
        self._check_closed()
        return self._caller.safe_call_with_result(self._async_reader.update(new_data), timeout or self._timeout_sec)

    # ------------------ Закрытие ------------------ #
    def close(self, flush=True, timeout: Optional[float] = None):
        if self._closed:
            return

        self._closed = True

        self._caller.safe_call_with_result(self._async_reader.close(flush), timeout)