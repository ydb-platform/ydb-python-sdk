from typing import Optional

from .. import issues
from .._topic_common.common import _get_shared_event_loop, CallFromSyncToAsync
from ..aio.coordination.semaphore import CoordinationSemaphore as CoordinationSemaphoreAio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .session import CoordinationSession


class CoordinationSemaphore:
    def __init__(self, session: "CoordinationSession", name: str, timeout_sec: float = 5):
        self._session = session
        self._name = name
        self._timeout_sec = timeout_sec
        self._closed = False
        self._caller = CallFromSyncToAsync(_get_shared_event_loop())
        self._async_semaphore: CoordinationSemaphoreAio = self._session._async_node.lock(name)

    def _check_closed(self):
        if self._closed:
            raise issues.Error(f"CoordinationSemaphore {self._name} already closed")

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
            self._async_semaphore.acquire(),
            t,
        )

    def release(self, timeout: Optional[float] = None):
        if self._closed:
            return
        t = timeout or self._timeout_sec
        return self._caller.safe_call_with_result(
            self._async_semaphore.release(),
            t,
        )

    def describe(self, timeout: Optional[float] = None):
        self._check_closed()
        t = timeout or self._timeout_sec
        return self._caller.safe_call_with_result(
            self._async_semaphore.describe(),
            t,
        )

    def update(self, new_data: bytes, timeout: Optional[float] = None):
        self._check_closed()
        t = timeout or self._timeout_sec
        return self._caller.safe_call_with_result(
            self._async_semaphore.update(new_data),
            t,
        )

    def close(self, timeout: Optional[float] = None):
        if self._closed:
            return
        t = timeout or self._timeout_sec
        try:
            self._caller.safe_call_with_result(
                self._async_semaphore.release(),
                t,
            )
        finally:
            self._closed = True
