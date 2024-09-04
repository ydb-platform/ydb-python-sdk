import asyncio
import logging
from typing import (
    Callable,
    Optional,
    List,
)

from .session import (
    QuerySessionAsync,
)
from ... import issues
from ...retries import (
    RetrySettings,
    retry_operation_async,
)
from ... import convert
from ..._grpc.grpcwrapper import common_utils

logger = logging.getLogger(__name__)


class QuerySessionPoolAsync:
    """QuerySessionPoolAsync is an object to simplify operations with sessions of Query Service."""

    def __init__(self, driver: common_utils.SupportedDriverType, size: int = 100):
        """
        :param driver: A driver instance
        :param size: Size of session pool
        """

        logger.warning("QuerySessionPoolAsync is an experimental API, which could be changed.")
        self._driver = driver
        self._size = size
        self._should_stop = asyncio.Event()
        self._queue = asyncio.PriorityQueue()
        self._current_size = 0
        self._waiters = 0

    async def _create_new_session(self):
        session = QuerySessionAsync(self._driver)
        await session.create()
        logger.debug(f"New session was created for pool. Session id: {session._state.session_id}")
        return session

    async def acquire(self, timeout: float) -> QuerySessionAsync:
        if self._should_stop.is_set():
            logger.error("An attempt to take session from closed session pool.")
            raise RuntimeError("An attempt to take session from closed session pool.")

        try:
            _, session = self._queue.get_nowait()
            logger.debug(f"Acquired active session from queue: {session._state.session_id}")
            return session if session._state.attached else await self._create_new_session()
        except asyncio.QueueEmpty:
            pass

        if self._current_size < self._size:
            logger.debug(f"Session pool is not large enough: {self._current_size} < {self._size}, will create new one.")
            session = await self._create_new_session()
            self._current_size += 1
            return session

        try:
            self._waiters += 1
            session = await self._get_session_with_timeout(timeout)
            return session if session._state.attached else await self._create_new_session()
        except asyncio.TimeoutError:
            raise issues.SessionPoolEmpty("Timeout on acquire session")
        finally:
            self._waiters -= 1

    async def _get_session_with_timeout(self, timeout: float):
        task_wait = asyncio.ensure_future(asyncio.wait_for(self._queue.get(), timeout=timeout))
        task_stop = asyncio.ensure_future(asyncio.ensure_future(self._should_stop.wait()))
        done, _ = await asyncio.wait((task_wait, task_stop), return_when=asyncio.FIRST_COMPLETED)
        if task_stop in done:
            task_wait.cancel()
            return await self._create_new_session()  # TODO: not sure why
        _, session = task_wait.result()
        return session

    async def release(self, session: QuerySessionAsync) -> None:
        self._queue.put_nowait((1, session))
        logger.debug("Session returned to queue: %s", session._state.session_id)

    def checkout(self, timeout: float = 10) -> "SimpleQuerySessionCheckoutAsync":
        """WARNING: This API is experimental and could be changed.
        Return a Session context manager, that opens session on enter and closes session on exit.
        """

        return SimpleQuerySessionCheckoutAsync(self, timeout)

    async def retry_operation_async(
        self, callee: Callable, retry_settings: Optional[RetrySettings] = None, *args, **kwargs
    ):
        """WARNING: This API is experimental and could be changed.
        Special interface to execute a bunch of commands with session in a safe, retriable way.

        :param callee: A function, that works with session.
        :param retry_settings: RetrySettings object.

        :return: Result sets or exception in case of execution errors.
        """

        retry_settings = RetrySettings() if retry_settings is None else retry_settings

        async def wrapped_callee():
            async with self.checkout() as session:
                return await callee(session, *args, **kwargs)

        return await retry_operation_async(wrapped_callee, retry_settings)

    async def execute_with_retries(
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

        async def wrapped_callee():
            async with self.checkout() as session:
                it = await session.execute(query, parameters, *args, **kwargs)
                return [result_set async for result_set in it]

        return await retry_operation_async(wrapped_callee, retry_settings)

    async def stop(self, timeout=None):
        self._should_stop.set()

        tasks = []
        while True:
            try:
                _, session = self._queue.get_nowait()
                tasks.append(session.delete())
            except asyncio.QueueEmpty:
                break

        await asyncio.gather(*tasks)

        logger.debug("All session were deleted.")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()


class SimpleQuerySessionCheckoutAsync:
    def __init__(self, pool: QuerySessionPoolAsync, timeout: float):
        self._pool = pool
        self._timeout = timeout
        self._session = None

    async def __aenter__(self) -> QuerySessionAsync:
        self._session = await self._pool.acquire(self._timeout)
        return self._session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._pool.release(self._session)
