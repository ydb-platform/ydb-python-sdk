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
    ):
        self._closed = False
        self._name = name
        self._caller = CallFromSyncToAsync(_get_shared_event_loop())
        self._timeout_sec = 5

        async def _make_lock():
            return CoordinationLock(
                client=client,
                name=self._name,
                node_path=node_path,
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

        self._caller.safe_call_with_result(self._async_lock.release(), t)
        self._caller.safe_call_with_result(self._async_lock.close(True), t)
        self._closed = True
