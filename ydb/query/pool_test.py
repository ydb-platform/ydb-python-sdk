from __future__ import annotations

import threading
import time
import unittest
from unittest.mock import MagicMock

from ydb import issues
from ydb.convert import _ResultSet, aggregate_result_sets_by_index
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


def _rs(index, rows, columns=None, truncated=False, data=None):
    return _ResultSet(
        columns=["id"] if columns is None else columns,
        rows=list(rows),
        truncated=truncated,
        index=index,
        data=data,
    )


class TestAggregateResultSetsByIndex(unittest.TestCase):
    def test_merges_parts_with_same_index_into_one_result_set(self):
        merged = aggregate_result_sets_by_index([_rs(0, [1, 2]), _rs(0, [3, 4]), _rs(0, [5])])

        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].index, 0)
        self.assertEqual(merged[0].rows, [1, 2, 3, 4, 5])

    def test_keeps_distinct_indexes_separate_and_ordered(self):
        merged = aggregate_result_sets_by_index([_rs(0, [1]), _rs(0, [2]), _rs(1, [3]), _rs(2, [4]), _rs(2, [5])])

        self.assertEqual([rs.index for rs in merged], [0, 1, 2])
        self.assertEqual([rs.rows for rs in merged], [[1, 2], [3], [4, 5]])

    def test_schema_kept_from_first_part_when_later_parts_omit_it(self):
        merged = aggregate_result_sets_by_index([_rs(0, [1], columns=["id", "name"]), _rs(0, [2], columns=[])])

        self.assertEqual(merged[0].columns, ["id", "name"])
        self.assertEqual(merged[0].rows, [1, 2])

    def test_truncated_flag_is_propagated_from_any_part(self):
        merged = aggregate_result_sets_by_index([_rs(0, [1], truncated=False), _rs(0, [2], truncated=True)])

        self.assertTrue(merged[0].truncated)

    def test_arrow_data_is_concatenated(self):
        merged = aggregate_result_sets_by_index(
            [_rs(0, [], data=b"aa"), _rs(0, [], data=b"bb"), _rs(0, [], data=b"cc")]
        )

        self.assertEqual(merged[0].data, b"aabbcc")

    def test_interleaved_parts_are_merged_by_index(self):
        merged = aggregate_result_sets_by_index([_rs(0, [1]), _rs(1, [2]), _rs(0, [3]), _rs(1, [4])])

        self.assertEqual([rs.index for rs in merged], [0, 1])
        self.assertEqual([rs.rows for rs in merged], [[1, 3], [2, 4]])

    def test_schema_filled_from_later_part_when_first_omits_it(self):
        merged = aggregate_result_sets_by_index([_rs(0, [1], columns=[]), _rs(0, [2], columns=["id", "name"])])

        self.assertEqual(merged[0].columns, ["id", "name"])
        self.assertEqual(merged[0].rows, [1, 2])

    def test_arrow_data_filled_from_later_part_when_first_has_none(self):
        merged = aggregate_result_sets_by_index([_rs(0, [], data=None), _rs(0, [], data=b"bb")])

        self.assertEqual(merged[0].data, b"bb")

    def test_parts_without_index_are_not_merged(self):
        merged = aggregate_result_sets_by_index([_rs(None, [1]), _rs(None, [2])])

        self.assertEqual([rs.rows for rs in merged], [[1], [2]])

    def test_empty_input_returns_empty_list(self):
        self.assertEqual(aggregate_result_sets_by_index([]), [])


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
