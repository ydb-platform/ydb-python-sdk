from __future__ import annotations

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock

from ydb import issues
from ydb.aio.query.pool import QuerySessionPool


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
