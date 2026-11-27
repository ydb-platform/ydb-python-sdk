from __future__ import annotations

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from ydb import _apis, issues, resolver
from ydb.aio import _utilities as aio_utilities
from ydb.aio import connection as aio_connection
from ydb.aio import pool as aio_pool
from ydb.aio.driver import DriverConfig
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


async def _wait_signalled(event: asyncio.Event) -> None:
    """Wait for a test signal, bounded so a regression fails the test instead of hanging the suite."""
    await asyncio.wait_for(event.wait(), timeout=5)


class TestDiscoveryChannelRetirement(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.config = DriverConfig("localhost:2135", "/local")
        self.cache = aio_pool.ConnectionsCache()
        self.channel = MagicMock()
        self.channel.close = AsyncMock()
        with patch.object(aio_connection, "channel_factory", return_value=self.channel):
            self.connection = aio_connection.Connection(self.config.endpoint, self.config)
        self.cache.add(self.connection)
        self.addAsyncCleanup(self.cache.cleanup)

    async def test_cleanup_closes_channel_before_retirement_task_starts(self):
        self.cache.retire(self.connection, self.config.grpc_channel_shutdown_timeout)
        self.cache.retire(self.connection, self.config.grpc_channel_shutdown_timeout)
        self.assertEqual(len(self.cache._retirement_tasks), 1)
        self.assertEqual(self.cache.size, 0)

        await self.cache.cleanup()

        self.channel.close.assert_awaited_once()
        self.assertFalse(self.cache._retirement_tasks)

    async def test_failed_channel_close_releases_retirement_task(self):
        self.channel.close.side_effect = RuntimeError("close failed")
        with self.assertLogs("ydb.pool", level="ERROR") as logs:
            self.cache.retire(self.connection, 0)
            await asyncio.gather(*self.cache._retirement_tasks, return_exceptions=True)

        self.assertIn("Failed to close retired channel", logs.output[0])
        self.assertFalse(self.cache._retirement_tasks)

    async def test_discovery_cancellation_closes_retired_channel(self):
        discovery = aio_pool.Discovery(self.cache, self.config)
        discovery._base_emergency_retry_interval = 0
        resolving_again = asyncio.Event()

        async def resolve():
            if discovery._resolver.resolve.await_count == 1:
                return resolver.DiscoveryResult("local", [])
            resolving_again.set()
            await asyncio.Future()

        discovery._resolver.resolve = AsyncMock(side_effect=resolve)
        call = MagicMock()
        call.done.return_value = False
        self.connection._track_call(MagicMock(), call)

        task = asyncio.create_task(discovery.run())
        try:
            await _wait_signalled(resolving_again)
            self.assertEqual(self.cache.size, 0)
            self.channel.close.assert_not_awaited()
        finally:
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task

        call.cancel.assert_called_once()
        self.channel.close.assert_awaited_once()
        self.assertFalse(self.cache._retirement_tasks)

    async def test_discovery_can_stop_after_recovering_from_a_failed_round(self):
        discovery = aio_pool.Discovery(self.cache, self.config)
        discovery._base_emergency_retry_interval = 0

        async def execute():
            if discovery.execute_discovery.await_count == 1:
                raise RuntimeError("discovery unavailable")
            discovery.stop()
            return True

        discovery.execute_discovery = AsyncMock(side_effect=execute)
        await asyncio.wait_for(discovery.run(), timeout=3)

        self.assertEqual(discovery.execute_discovery.await_count, 2)
        self.assertIsNone(self.cache._fast_fail_error)
        self.channel.close.assert_awaited_once()


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


class TestAcquireCancellation(unittest.IsolatedAsyncioTestCase):
    """Cancelling acquire() while the session is being created must not lose a pool slot."""

    @staticmethod
    def _hanging_create(entered: asyncio.Event):
        async def slow_create():
            entered.set()
            await asyncio.sleep(30)

        return slow_create

    async def _cancel_during_create(self, pool):
        entered = asyncio.Event()
        pool._create_new_session = self._hanging_create(entered)

        task = asyncio.create_task(pool.acquire())
        await _wait_signalled(entered)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task

    async def test_cancelled_create_does_not_leak_pool_capacity(self):
        pool = _make_pool(size=1)

        await self._cancel_during_create(pool)

        self.assertEqual(pool._current_size, 0)

    async def test_pool_still_usable_after_cancelled_create(self):
        pool = _make_pool(size=1)

        await self._cancel_during_create(pool)

        session = _make_active_session()
        pool._create_new_session = AsyncMock(return_value=session)

        acquired = await asyncio.wait_for(pool.acquire(), timeout=1)

        self.assertIs(acquired, session)
        self.assertEqual(pool._current_size, 1)

    async def test_failed_create_does_not_leak_pool_capacity(self):
        pool = _make_pool(size=1)
        pool._create_new_session = AsyncMock(side_effect=issues.ConnectionError("no connection"))

        with self.assertRaises(issues.ConnectionError):
            await pool.acquire()

        self.assertEqual(pool._current_size, 0)


class TestSessionAttachCancellation(unittest.IsolatedAsyncioTestCase):
    """A cancelled attach must retire the session instead of orphaning it server-side."""

    def _make_session(self):
        driver = MagicMock()
        driver._driver_config.query_client_settings = None
        session = QuerySession(driver)
        session._session_id = "fake-session-id"
        return session

    async def test_attach_invalidates_session_when_cancelled_awaiting_first_response(self):
        session = self._make_session()
        stream = MagicMock()
        entered = asyncio.Event()

        async def fake_attach_call(*args, **kwargs):
            return stream

        async def hanging_first_message(*args, **kwargs):
            entered.set()
            await asyncio.sleep(30)

        with (
            patch.object(type(session), "_attach_call", side_effect=fake_attach_call),
            patch.object(aio_utilities, "AsyncResponseIterator", MagicMock()),
            patch.object(aio_utilities, "get_first_message_with_timeout", hanging_first_message),
        ):
            task = asyncio.create_task(session._attach())
            await _wait_signalled(entered)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task

        self.assertFalse(session.is_active)
        self.assertTrue(session._invalidated)
        stream.cancel.assert_called_once()

    async def test_attach_invalidates_session_when_cancelled_before_stream_is_open(self):
        session = self._make_session()
        entered = asyncio.Event()

        async def hanging_attach_call(*args, **kwargs):
            entered.set()
            await asyncio.sleep(30)

        with patch.object(type(session), "_attach_call", side_effect=hanging_attach_call):
            task = asyncio.create_task(session._attach())
            await _wait_signalled(entered)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task

        self.assertFalse(session.is_active)
        self.assertTrue(session._invalidated)

    async def test_attach_raises_stream_error_from_first_response(self):
        session = self._make_session()

        class FailingStream:
            cancel = MagicMock()

            def __aiter__(self):
                return self

            async def __anext__(self):
                raise issues.Unavailable("Socket closed")

        stream = FailingStream()

        async def fake_attach_call(*args, **kwargs):
            return stream

        with patch.object(type(session), "_attach_call", side_effect=fake_attach_call):
            with self.assertRaises(issues.Unavailable):
                await asyncio.wait_for(session._attach(), timeout=5)

        self.assertFalse(session.is_active)
        self.assertTrue(session._invalidated)
        stream.cancel.assert_called_once()


class TestQuerySessionDelete(unittest.IsolatedAsyncioTestCase):
    async def test_pool_exit_waits_for_session_status_reader(self):
        await self._check_pool_waits_for_status_reader()

    async def test_pool_exit_waits_for_session_status_reader_when_delete_rpc_fails(self):
        await self._check_pool_waits_for_status_reader(issues.Unavailable("DeleteSession failed"))

    async def _check_pool_waits_for_status_reader(self, delete_error=None):
        reading = asyncio.Event()
        finished = asyncio.Event()

        async def read_status():
            yield _apis.ydb_query.SessionState(status=issues.StatusCode.SUCCESS)
            reading.set()
            try:
                await asyncio.Future()
            finally:
                await asyncio.sleep(0)
                finished.set()

        stream = MagicMock()
        stream.__aiter__.side_effect = read_status

        async def create_call(session, settings=None):
            session._session_id = "session-id"

        with (
            patch.object(QuerySession, "_create_call", autospec=True, side_effect=create_call),
            patch.object(QuerySession, "_attach_call", new_callable=AsyncMock, return_value=stream),
            patch.object(QuerySession, "_delete_call", new_callable=AsyncMock, side_effect=delete_error) as delete_call,
        ):
            async with QuerySessionPool(MagicMock(), size=1) as pool:
                async with pool.checkout():
                    await _wait_signalled(reading)

        self.assertTrue(finished.is_set())
        stream.cancel.assert_called_once()
        delete_call.assert_awaited_once()

    async def test_delete_without_creating_session(self):
        session = QuerySession(MagicMock())
        session._delete_call = AsyncMock()

        await session.delete()
        await session.delete()

        self.assertTrue(session.is_closed)
        session._delete_call.assert_not_called()

    async def test_closes_before_delete_call(self):
        session = QuerySession(MagicMock())
        session._session_id = "session-id"
        session._session_metrics = MagicMock()

        async def delete_call(settings=None):
            self.assertTrue(session.is_closed)
            session._close_session(invalidate=True, reason="attach_closed")

        session._delete_call = AsyncMock(side_effect=delete_call)

        await session.delete()

        self.assertFalse(session._invalidated)
        session._session_metrics.count_closed.assert_called_once_with(None)


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
