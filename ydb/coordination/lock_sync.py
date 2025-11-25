import asyncio
from typing import Optional

from ydb import issues
from ydb._topic_common.common import _get_shared_event_loop, CallFromSyncToAsync
from ydb.aio.coordination.lock import CoordinationLock


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
        self._loop = eventloop or _get_shared_event_loop()
        self._timeout_sec = timeout_millis / 1000.0
        self._caller = CallFromSyncToAsync(self._loop)
        self._client = client
        self._node_path = node_path
        self._count = count
        self._timeout_millis = timeout_millis

        async def _make_lock():
            return CoordinationLock(
                client=self._client,
                name=self._name,
                node_path=self._node_path,
                count=self._count,
                timeout_millis=self._timeout_millis,
            )

        self._async_lock: CoordinationLock = self._caller.safe_call_with_result(_make_lock(), self._timeout_sec)

    def _check_closed(self):
        if self._closed:
            raise issues.Error(f"CoordinationLockSync {self._name} already closed")

    def __enter__(self):
        self.acquire(timeout=self._timeout_sec)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.release(timeout=self._timeout_sec)
        except Exception:
            pass

    def acquire(self, timeout: Optional[float] = None):
        self._check_closed()
        t = timeout or self._timeout_sec
        return self._caller.safe_call_with_result(self._async_lock.acquire(), t)

    def release(self, timeout: Optional[float] = None):
        if self._closed:
            return
        t = timeout or self._timeout_sec
        return self._caller.safe_call_with_result(self._async_lock.release(), t)

    def create(self, init_limit: int, init_data: bytes, timeout: Optional[float] = None):
        self._check_closed()
        t = timeout or self._timeout_sec
        return self._caller.safe_call_with_result(self._async_lock.create(init_limit, init_data), t)

    def delete(self, timeout: Optional[float] = None):
        self._check_closed()
        t = timeout or self._timeout_sec
        return self._caller.safe_call_with_result(self._async_lock.delete(), t)

    def describe(self, timeout: Optional[float] = None):
        self._check_closed()
        t = timeout or self._timeout_sec
        return self._caller.safe_call_with_result(self._async_lock.describe(), t)

    def update(self, new_data: bytes, timeout: Optional[float] = None):
        self._check_closed()
        t = timeout or self._timeout_sec
        return self._caller.safe_call_with_result(self._async_lock.update(new_data), t)

    def close(self, timeout: Optional[float] = None):
        if self._closed:
            return
        t = timeout or self._timeout_sec

        try:
            self._caller.safe_call_with_result(self._async_lock.release(), t)
        except Exception:
            pass

        try:
            self._caller.safe_call_with_result(self._async_lock.close(True), t)
        except Exception:
            pass

        self._closed = True
