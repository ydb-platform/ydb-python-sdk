import logging
from typing import (
    Callable,
    Optional,
    List,
)
import time
import threading
import queue

from .session import (
    QuerySessionSync,
)
from ..retries import (
    RetrySettings,
    retry_operation_sync,
)
from .. import issues
from .. import convert
from ..settings import BaseRequestSettings
from .._grpc.grpcwrapper import common_utils


logger = logging.getLogger(__name__)


class QuerySessionPool:
    """QuerySessionPool is an object to simplify operations with sessions of Query Service."""

    def __init__(self, driver: common_utils.SupportedDriverType, size: int = 100):
        """
        :param driver: A driver instance
        """

        logger.warning("QuerySessionPool is an experimental API, which could be changed.")
        self._driver = driver
        self._queue = queue.Queue()
        self._current_size = 0
        self._size = size
        self._should_stop = threading.Event()
        self._lock = threading.RLock()

    def _create_new_session(self, timeout: float):
        session = QuerySessionSync(self._driver)
        session.create(settings=BaseRequestSettings().with_timeout(timeout))
        logger.debug(f"New session was created for pool. Session id: {session._state.session_id}")
        return session

    def acquire(self, timeout: float) -> QuerySessionSync:
        acquired = self._lock.acquire(timeout=timeout)
        try:
            if self._should_stop.is_set():
                logger.error("An attempt to take session from closed session pool.")
                raise RuntimeError("An attempt to take session from closed session pool.")

            session = None
            try:
                session = self._queue.get_nowait()
            except queue.Empty:
                pass

            start = time.monotonic()
            if session is None and self._current_size == self._size:
                try:
                    session = self._queue.get(block=True, timeout=timeout)
                except queue.Empty:
                    raise issues.SessionPoolEmpty("Timeout on acquire session")

            if session is not None:
                if session._state.attached:
                    logger.debug(f"Acquired active session from queue: {session._state.session_id}")
                    return session
                else:
                    self._current_size -= 1
                    logger.debug(f"Acquired dead session from queue: {session._state.session_id}")

            logger.debug(f"Session pool is not large enough: {self._current_size} < {self._size}, will create new one.")
            finish = time.monotonic()
            time_left = timeout - (finish - start)
            session = self._create_new_session(time_left)

            self._current_size += 1
            return session
        finally:
            if acquired:
                self._lock.release()

    def release(self, session: QuerySessionSync) -> None:
        self._queue.put_nowait(session)
        logger.debug("Session returned to queue: %s", session._state.session_id)

    def checkout(self, timeout: float = 10) -> "SimpleQuerySessionCheckout":
        """WARNING: This API is experimental and could be changed.
        Return a Session context manager, that opens session on enter and closes session on exit.
        """

        return SimpleQuerySessionCheckout(self, timeout)

    def retry_operation_sync(self, callee: Callable, retry_settings: Optional[RetrySettings] = None, *args, **kwargs):
        """WARNING: This API is experimental and could be changed.
        Special interface to execute a bunch of commands with session in a safe, retriable way.

        :param callee: A function, that works with session.
        :param retry_settings: RetrySettings object.

        :return: Result sets or exception in case of execution errors.
        """

        retry_settings = RetrySettings() if retry_settings is None else retry_settings

        def wrapped_callee():
            with self.checkout() as session:
                return callee(session, *args, **kwargs)

        return retry_operation_sync(wrapped_callee, retry_settings)

    def execute_with_retries(
        self,
        query: str,
        parameters: Optional[dict] = None,
        retry_settings: Optional[RetrySettings] = None,
        *args,
        **kwargs,
    ) -> List[convert.ResultSet]:
        """WARNING: This API is experimental and could be changed.
        Special interface to execute a one-shot queries in a safe, retriable way.
        Note: this method loads all data from stream before return, do not use this
        method with huge read queries.

        :param query: A query, yql or sql text.
        :param parameters: dict with parameters and YDB types;
        :param retry_settings: RetrySettings object.

        :return: Result sets or exception in case of execution errors.
        """

        retry_settings = RetrySettings() if retry_settings is None else retry_settings

        def wrapped_callee():
            with self.checkout() as session:
                it = session.execute(query, parameters, *args, **kwargs)
                return [result_set for result_set in it]

        return retry_operation_sync(wrapped_callee, retry_settings)

    def stop(self, timeout=-1):
        acquired = self._lock.acquire(timeout=timeout)
        try:
            self._should_stop.set()
            while True:
                try:
                    session = self._queue.get_nowait()
                    session.delete()
                except queue.Empty:
                    break

            logger.debug("All session were deleted.")
        finally:
            if acquired:
                self._lock.release()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def __del__(self):
        self.stop()


class SimpleQuerySessionCheckout:
    def __init__(self, pool: QuerySessionPool, timeout: float):
        self._pool = pool
        self._timeout = timeout
        self._session = None

    def __enter__(self) -> QuerySessionSync:
        self._session = self._pool.acquire(self._timeout)
        return self._session

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._pool.release(self._session)
