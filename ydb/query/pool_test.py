from __future__ import annotations

import asyncio
import threading
import time
import unittest
from unittest.mock import MagicMock

from unittest.mock import patch

from ydb import _utilities, issues
from ydb.convert import _ResultSet, aggregate_result_sets_by_index, aggregate_result_sets_by_index_async
from ydb.query.base import create_execute_query_request
from ydb.query.pool import QuerySessionPool
from ydb.query.session import QuerySession
from ydb.query.transaction import QueryTxContext
from ydb._grpc.grpcwrapper import ydb_query_public_types as _ydb_query_public


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


class TestSessionAttachInterrupted(unittest.TestCase):
    """An interrupted attach must retire the session instead of orphaning it server-side."""

    def _make_session(self):
        driver = MagicMock()
        driver._driver_config.query_client_settings = None
        session = QuerySession(driver)
        session._session_id = "fake-session-id"
        return session

    def test_attach_invalidates_session_when_interrupted_awaiting_first_response(self):
        session = self._make_session()
        stream = MagicMock()

        with patch.object(type(session), "_attach_call", return_value=stream), patch.object(
            _utilities, "SyncResponseIterator", MagicMock()
        ), patch.object(_utilities, "get_first_message_with_timeout", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                session._attach()

        self.assertFalse(session.is_active)
        self.assertTrue(session._invalidated)
        stream.cancel.assert_called_once()

    def test_attach_invalidates_session_when_interrupted_before_stream_is_open(self):
        session = self._make_session()

        with patch.object(type(session), "_attach_call", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                session._attach()

        self.assertFalse(session.is_active)
        self.assertTrue(session._invalidated)


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

    def test_arrow_parts_are_not_merged(self):
        merged = aggregate_result_sets_by_index([_rs(0, [], data=b"aa"), _rs(0, [], data=b"bb")])

        self.assertEqual([rs.data for rs in merged], [b"aa", b"bb"])

    def test_interleaved_parts_are_merged_by_index(self):
        merged = aggregate_result_sets_by_index([_rs(0, [1]), _rs(1, [2]), _rs(0, [3]), _rs(1, [4])])

        self.assertEqual([rs.index for rs in merged], [0, 1])
        self.assertEqual([rs.rows for rs in merged], [[1, 3], [2, 4]])

    def test_schema_filled_from_later_part_when_first_omits_it(self):
        merged = aggregate_result_sets_by_index([_rs(0, [1], columns=[]), _rs(0, [2], columns=["id", "name"])])

        self.assertEqual(merged[0].columns, ["id", "name"])
        self.assertEqual(merged[0].rows, [1, 2])

    def test_parts_without_index_are_not_merged(self):
        merged = aggregate_result_sets_by_index([_rs(None, [1]), _rs(None, [2])])

        self.assertEqual([rs.rows for rs in merged], [[1], [2]])

    def test_empty_input_returns_empty_list(self):
        self.assertEqual(aggregate_result_sets_by_index([]), [])

    def test_async_stream_is_merged_in_one_pass(self):
        async def stream():
            for part in [_rs(0, [1]), _rs(0, [2]), _rs(1, [3]), _rs(1, [4])]:
                yield part

        merged = asyncio.run(aggregate_result_sets_by_index_async(stream()))

        self.assertEqual([rs.index for rs in merged], [0, 1])
        self.assertEqual([rs.rows for rs in merged], [[1, 2], [3, 4]])


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


class TestQuerySessionExecutePoolId(unittest.TestCase):
    """Test that pool_id flows from session.execute() → _execute_call() → driver."""

    def _make_session(self):
        driver = MagicMock()
        driver._driver_config.query_client_settings = None
        session = QuerySession(driver)
        session._session_id = "fake-session-id"
        return session

    def test_execute_passes_pool_id_to_driver(self):
        session = self._make_session()

        captured = {}

        def fake_execute_call(**kwargs):
            captured.update(kwargs)
            return iter([])

        with patch.object(type(session), "_execute_call", side_effect=fake_execute_call):
            session.execute("SELECT 1", pool_id="my-pool")

        self.assertEqual(captured.get("pool_id"), "my-pool")

    def test_execute_without_pool_id_passes_none(self):
        session = self._make_session()

        captured = {}

        def fake_execute_call(**kwargs):
            captured.update(kwargs)
            return iter([])

        with patch.object(type(session), "_execute_call", side_effect=fake_execute_call):
            session.execute("SELECT 1")

        self.assertIsNone(captured.get("pool_id"))


class TestCreateExecuteQueryRequest(unittest.TestCase):
    def test_pool_id_is_set_in_request(self):
        req = create_execute_query_request(
            query="SELECT 1",
            session_id="sess-1",
            tx_id=None,
            commit_tx=None,
            tx_mode=None,
            syntax=None,
            exec_mode=None,
            stats_mode=None,
            schema_inclusion_mode=None,
            result_set_format=None,
            arrow_format_settings=None,
            parameters=None,
            concurrent_result_sets=None,
            pool_id="my-pool",
        )
        self.assertEqual(req.pool_id, "my-pool")
        proto = req.to_proto()
        self.assertEqual(proto.pool_id, "my-pool")

    def test_pool_id_defaults_to_none_and_is_absent_from_proto(self):
        req = create_execute_query_request(
            query="SELECT 1",
            session_id="sess-1",
            tx_id=None,
            commit_tx=None,
            tx_mode=None,
            syntax=None,
            exec_mode=None,
            stats_mode=None,
            schema_inclusion_mode=None,
            result_set_format=None,
            arrow_format_settings=None,
            parameters=None,
            concurrent_result_sets=None,
            pool_id=None,
        )
        self.assertIsNone(req.pool_id)
        proto = req.to_proto()
        self.assertEqual(proto.pool_id, "")


class TestPoolIdParameter(unittest.TestCase):
    def test_execute_with_retries_passes_pool_id_to_session(self):
        pool = _make_pool(size=1)

        session = MagicMock()
        session.is_active = True
        session.execute = MagicMock(return_value=[])

        def mock_acquire(timeout=None):
            return session

        pool.acquire = mock_acquire
        pool.release = MagicMock()

        pool.execute_with_retries("SELECT 1", pool_id="my-pool")

        session.execute.assert_called_once()
        call_kwargs = session.execute.call_args[1]
        self.assertEqual(call_kwargs.get("pool_id"), "my-pool")

    def test_execute_with_retries_without_pool_id(self):
        pool = _make_pool(size=1)

        session = MagicMock()
        session.is_active = True
        session.execute = MagicMock(return_value=[])

        def mock_acquire(timeout=None):
            return session

        pool.acquire = mock_acquire
        pool.release = MagicMock()

        pool.execute_with_retries("SELECT 1")

        session.execute.assert_called_once()
        call_kwargs = session.execute.call_args[1]
        self.assertIsNone(call_kwargs.get("pool_id"))


class TestQueryTxContextExecutePoolId(unittest.TestCase):
    """Test that pool_id flows from QueryTxContext.execute() → _execute_call()."""

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

    def test_execute_passes_pool_id_to_execute_call(self):
        tx = self._make_tx()

        captured = {}

        def fake_execute_call(**kwargs):
            captured.update(kwargs)
            return iter([])

        with patch.object(type(tx), "_execute_call", side_effect=fake_execute_call):
            tx.execute("SELECT 1", pool_id="my-pool")

        self.assertEqual(captured.get("pool_id"), "my-pool")

    def test_execute_without_pool_id_passes_none(self):
        tx = self._make_tx()

        captured = {}

        def fake_execute_call(**kwargs):
            captured.update(kwargs)
            return iter([])

        with patch.object(type(tx), "_execute_call", side_effect=fake_execute_call):
            tx.execute("SELECT 1")

        self.assertIsNone(captured.get("pool_id"))
