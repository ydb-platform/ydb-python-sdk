from __future__ import annotations

import threading
import time
import unittest
from unittest.mock import MagicMock

from ydb import issues
from ydb.query.pool import QuerySessionPool
from ydb.query.session import QuerySession


def _make_pool(size=1):
    driver = MagicMock()
    pool = QuerySessionPool(driver, size=size)
    return pool


def _make_active_session():
    session = MagicMock()
    session.is_active = True
    return session


class TestAcquireTimeout(unittest.TestCase):
    def test_acquire_returns_session_when_available(self):
        pool = _make_pool(size=2)
        session = _make_active_session()
        pool._queue.put_nowait(session)

        acquired = pool.acquire(timeout=1.0)

        self.assertIs(acquired, session)

    def test_acquire_raises_session_pool_empty_on_timeout(self):
        pool = _make_pool(size=1)
        pool._current_size = 1  # simulate full pool

        with self.assertRaises(issues.SessionPoolEmpty):
            pool.acquire(timeout=0.05)

    def test_no_timeout_waits_until_session_released(self):
        pool = _make_pool(size=1)
        session = _make_active_session()

        def release_after_delay():
            time.sleep(0.1)
            pool.release(session)

        pool._current_size = 1
        t = threading.Thread(target=release_after_delay)
        t.start()
        try:
            acquired = pool.acquire(timeout=None)
            self.assertIs(acquired, session)
        finally:
            t.join()


class TestRetryOperationSync(unittest.TestCase):
    def test_retry_reacquires_invalidated_session_before_first_use(self):
        pool = _make_pool(size=1)

        invalidated_session = QuerySession(pool._driver)
        invalidated_session._session_id = "invalidated-session"
        invalidated_session._close_session(invalidate=True)

        live_session = MagicMock()
        live_session.explain.return_value = "ok"

        sessions = iter([invalidated_session, live_session])
        pool.acquire = MagicMock(side_effect=lambda timeout=None: next(sessions))
        pool.release = MagicMock()

        result = pool.retry_operation_sync(lambda session: session.explain("SELECT 1"))

        self.assertEqual(result, "ok")
        live_session.explain.assert_called_once_with("SELECT 1")
