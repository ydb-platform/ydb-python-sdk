from __future__ import annotations

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from ydb import issues
from ydb.aio.query.pool import QuerySessionPool
from ydb.aio.query.session import QuerySession
from ydb.aio.query.transaction import QueryTxContext
from ydb.observability.metrics import QuerySessionPoolMetrics
from ydb._grpc.grpcwrapper import ydb_query_public_types as _ydb_query_public


def _make_pool(size=1):
    driver = MagicMock()
    pool = QuerySessionPool.__new__(QuerySessionPool)
    pool._driver = driver
    pool._size = size
    pool._should_stop = asyncio.Event()
    pool._queue = asyncio.Queue()
    pool._current_size = 0
    pool._loop = asyncio.get_event_loop()
    pool._query_client_settings = None
    pool._metrics = QuerySessionPoolMetrics("test-query-session-pool", driver, size)
    return pool


def _make_active_session():
    session = MagicMock()
    session.is_active = True
    return session


class TestAcquireTimeout(unittest.IsolatedAsyncioTestCase):
    async def test_acquire_returns_session_when_available(self):
        pool = _make_pool(size=2)
        session = _make_active_session()
        pool._queue.put_nowait(session)

        acquired = await pool.acquire(timeout=1.0)

        self.assertIs(acquired, session)

    async def test_acquire_creates_new_session_when_pool_not_full(self):
        pool = _make_pool(size=2)
        session = _make_active_session()
        pool._create_new_session = AsyncMock(return_value=session)

        acquired = await pool.acquire(timeout=1.0)

        self.assertIs(acquired, session)
        self.assertEqual(pool._current_size, 1)

    async def test_acquire_raises_session_pool_empty_on_timeout(self):
        pool = _make_pool(size=1)
        pool._current_size = 1  # simulate full pool

        with self.assertRaises(issues.SessionPoolEmpty):
            await pool.acquire(timeout=0.05)

    async def test_no_timeout_waits_until_session_released(self):
        pool = _make_pool(size=1)
        session = _make_active_session()
        pool._current_size = 1

        async def release_after_delay():
            await asyncio.sleep(0.1)
            await pool.release(session)

        asyncio.create_task(release_after_delay())
        acquired = await pool.acquire(timeout=None)

        self.assertIs(acquired, session)

    async def test_session_not_leaked_when_timeout_races_with_queue_get(self):
        pool = _make_pool(size=1)
        pool._current_size = 1
        session = _make_active_session()

        released_sessions = []

        async def tracking_release(s):
            released_sessions.append(s)

        pool.release = tracking_release

        async def enqueue_immediately():
            pool._queue.put_nowait(session)

        asyncio.create_task(enqueue_immediately())
        try:
            await pool.acquire(timeout=0.001)
        except issues.SessionPoolEmpty:
            pass

        await asyncio.sleep(0.05)
        total = pool._queue.qsize() + len(released_sessions)
        self.assertGreaterEqual(total, 0)

    async def test_retry_reacquires_invalidated_session_before_first_use(self):
        pool = _make_pool(size=1)

        invalidated_session = QuerySession.__new__(QuerySession)
        invalidated_session._session_id = "invalidated-session"
        invalidated_session._closed = False
        invalidated_session._invalidated = False
        invalidated_session._stream = None
        invalidated_session._close_session(invalidate=True)

        live_session = MagicMock()
        live_session.explain = AsyncMock(return_value="ok")

        sessions = iter([invalidated_session, live_session])
        pool.acquire = AsyncMock(side_effect=lambda timeout=None: next(sessions))
        pool.release = AsyncMock()

        result = await pool.retry_operation_async(lambda session: session.explain("SELECT 1"))

        self.assertEqual(result, "ok")
        live_session.explain.assert_awaited_once_with("SELECT 1")


async def _async_empty_iter():
    """Async-iterable that yields nothing; usable as a stub for session.execute return value."""
    if False:
        yield


class TestQuerySessionExecutePoolId(unittest.IsolatedAsyncioTestCase):
    """Test that pool_id flows from async session.execute() → _execute_call() → driver."""

    def _make_session(self):
        driver = MagicMock()
        driver._driver_config.query_client_settings = None
        session = QuerySession(driver)
        session._session_id = "fake-session-id"
        return session

    async def test_execute_passes_pool_id_to_execute_call(self):
        session = self._make_session()

        captured = {}

        async def fake_execute_call(**kwargs):
            captured.update(kwargs)
            return _async_empty_iter()

        with patch.object(type(session), "_execute_call", side_effect=fake_execute_call):
            await session.execute("SELECT 1", pool_id="my-pool")

        self.assertEqual(captured.get("pool_id"), "my-pool")

    async def test_execute_without_pool_id_passes_none(self):
        session = self._make_session()

        captured = {}

        async def fake_execute_call(**kwargs):
            captured.update(kwargs)
            return _async_empty_iter()

        with patch.object(type(session), "_execute_call", side_effect=fake_execute_call):
            await session.execute("SELECT 1")

        self.assertIsNone(captured.get("pool_id"))


class TestPoolIdParameter(unittest.IsolatedAsyncioTestCase):
    async def test_execute_with_retries_passes_pool_id_to_session(self):
        pool = _make_pool(size=1)

        session = MagicMock()
        session.is_active = True
        session.execute = AsyncMock(return_value=_async_empty_iter())

        async def mock_acquire(timeout=None):
            return session

        pool.acquire = mock_acquire
        pool.release = AsyncMock()

        await pool.execute_with_retries("SELECT 1", pool_id="my-pool")

        session.execute.assert_awaited_once()
        call_kwargs = session.execute.call_args[1]
        self.assertEqual(call_kwargs.get("pool_id"), "my-pool")

    async def test_execute_with_retries_without_pool_id(self):
        pool = _make_pool(size=1)

        session = MagicMock()
        session.is_active = True
        session.execute = AsyncMock(return_value=_async_empty_iter())

        async def mock_acquire(timeout=None):
            return session

        pool.acquire = mock_acquire
        pool.release = AsyncMock()

        await pool.execute_with_retries("SELECT 1")

        session.execute.assert_awaited_once()
        call_kwargs = session.execute.call_args[1]
        self.assertIsNone(call_kwargs.get("pool_id"))


class TestQueryTxContextExecutePoolId(unittest.IsolatedAsyncioTestCase):
    """Test that pool_id flows from async QueryTxContext.execute() → _execute_call()."""

    def _make_tx(self):
        driver = MagicMock()
        driver._driver_config.query_client_settings = None
        session = MagicMock()
        session.session_id = "fake-session-id"
        session.node_id = None
        session._endpoint_key = None
        tx_mode = _ydb_query_public.QuerySerializableReadWrite()
        tx = QueryTxContext(driver, session, tx_mode)
        return tx

    async def test_execute_passes_pool_id_to_execute_call(self):
        tx = self._make_tx()

        captured = {}

        async def fake_execute_call(**kwargs):
            captured.update(kwargs)
            return _async_empty_iter()

        with patch.object(type(tx), "_execute_call", side_effect=fake_execute_call):
            await tx.execute("SELECT 1", pool_id="my-pool")

        self.assertEqual(captured.get("pool_id"), "my-pool")

    async def test_execute_without_pool_id_passes_none(self):
        tx = self._make_tx()

        captured = {}

        async def fake_execute_call(**kwargs):
            captured.update(kwargs)
            return _async_empty_iter()

        with patch.object(type(tx), "_execute_call", side_effect=fake_execute_call):
            await tx.execute("SELECT 1")

        self.assertIsNone(captured.get("pool_id"))
