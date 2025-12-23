from typing import Optional

from .. import issues
from .._topic_common.common import _get_shared_event_loop, CallFromSyncToAsync
from ..aio.coordination.semaphore import CoordinationSemaphore


class CoordinationSemaphoreSync:
    def __init__(self, node_sync, name: str, timeout_sec: float = 5):
        self._node_sync = node_sync
        self._name = name
        self._timeout_sec = timeout_sec
        self._closed = False
        self._caller = CallFromSyncToAsync(_get_shared_event_loop())
        self._async_lock: CoordinationSemaphore = self._node_sync._async_node.lock(name)

    def _check_closed(self):
        if self._closed:
            raise issues.Error(f"CoordinationLockSync {self._name} already closed")

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.release()
        except Exception:
            pass

    def acquire(self, timeout: Optional[float] = None):
        self._check_closed()
        t = timeout or self._timeout_sec
        return self._caller.safe_call_with_result(
            self._async_lock.acquire(),
            t,
        )

    def release(self, timeout: Optional[float] = None):
        if self._closed:
            return
        t = timeout or self._timeout_sec
        return self._caller.safe_call_with_result(
            self._async_lock.release(),
            t,
        )

    def describe(self, timeout: Optional[float] = None):
        self._check_closed()
        t = timeout or self._timeout_sec
        return self._caller.safe_call_with_result(
            self._async_lock.describe(),
            t,
        )

    def update(self, new_data: bytes, timeout: Optional[float] = None):
        self._check_closed()
        t = timeout or self._timeout_sec
        return self._caller.safe_call_with_result(
            self._async_lock.update(new_data),
            t,
        )

    def close(self, timeout: Optional[float] = None):
        if self._closed:
            return
        t = timeout or self._timeout_sec
        try:
            self._caller.safe_call_with_result(
                self._async_lock.release(),
                t,
            )
        finally:
            self._closed = True
