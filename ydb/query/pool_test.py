from __future__ import annotations

import asyncio
import concurrent.futures
import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

from unittest.mock import patch

from ydb import _utilities, connection, issues, pool
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

    def test_attach_raises_stream_error_from_first_response(self):
        session = self._make_session()
        stream = MagicMock()
        stream.__next__.side_effect = issues.Unavailable("Socket closed")

        with patch.object(type(session), "_attach_call", return_value=stream):
            with self.assertRaises(issues.Unavailable):
                session._attach(first_resp_timeout=5)

        self.assertFalse(session.is_active)
        self.assertTrue(session._invalidated)
        stream.cancel.assert_called_once()

    def test_attach_first_response_timeout_cancels_stream_and_helper_exits(self):
        # #911: after the timeout cancels the stream, the helper thread must exit quietly.
        session = self._make_session()
        cancelled = threading.Event()
        stream = MagicMock()
        stream.cancel.side_effect = cancelled.set

        def blocking_next():
            cancelled.wait()
            raise issues.Cancelled("Stream cancelled")

        stream.__next__.side_effect = blocking_next

        unhandled = []
        with patch.object(type(session), "_attach_call", return_value=stream), patch.object(
            threading, "excepthook", lambda args: unhandled.append(args.exc_value)
        ):
            with self.assertRaises(concurrent.futures.TimeoutError):
                session._attach(first_resp_timeout=0.1)
            for thread in threading.enumerate():
                if thread.name == "first response attach stream thread":
                    thread.join(timeout=5)
                    self.assertFalse(thread.is_alive())

        self.assertFalse(session.is_active)
        self.assertTrue(session._invalidated)
        stream.cancel.assert_called_once()
        self.assertEqual(unhandled, [])


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


class TestQuerySessionDelete(unittest.TestCase):
    def test_closes_before_delete_call(self):
        session = QuerySession(MagicMock())
        session._session_id = "session-id"
        session._session_metrics = MagicMock()

        def delete_call(settings=None):
            self.assertTrue(session.is_closed)
            session._close_session(invalidate=True, reason="attach_closed")

        session._delete_call = MagicMock(side_effect=delete_call)

        session.delete()

        self.assertFalse(session._invalidated)
        session._session_metrics.count_closed.assert_called_once_with(None)


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


class _StreamCall:
    def __init__(self, completed=False, complete_on_subscribe=False):
        self.messages = iter((1, 2))
        self.completed = completed
        self.complete_on_subscribe = complete_on_subscribe
        self.callbacks = []

    def __iter__(self):
        return self

    def __next__(self):
        try:
            return next(self.messages)
        except StopIteration:
            self.complete()
            raise

    def add_callback(self, callback):
        if self.completed:
            return False
        self.callbacks.append(callback)
        if self.complete_on_subscribe:
            self.complete()
        return True

    def complete(self):
        self.completed = True
        callbacks, self.callbacks = self.callbacks, []
        for callback in callbacks:
            callback()

    def cancel(self):
        self.complete()


class TestStreamConnectionCleanup(unittest.TestCase):
    def setUp(self):
        self.channel = Mock()
        self.closed = threading.Event()
        self.channel.close.side_effect = self.closed.set
        for name, value in (("channel_factory", lambda *args, **kwargs: self.channel), ("_stubs_list", ())):
            patched = patch.object(connection, name, value)
            patched.start()
            self.addCleanup(patched.stop)
        metadata = patch.object(connection, "_construct_metadata", return_value=[])
        metadata.start()
        self.addCleanup(metadata.stop)
        self.connection = connection.Connection("localhost:1")
        self.cache = pool.ConnectionsCache()
        self.cache.add(self.connection)

    def call(self, response, wrap_result=None):
        stub = type("Stub", (), {})
        self.connection._stub_instances[stub] = SimpleNamespace(ReadTable=lambda *args, **kwargs: response)
        return self.connection(SimpleNamespace(), stub, "ReadTable", wrap_result=wrap_result)

    def cleanup_outdated(self):
        self.cache.make_outdated(self.connection)
        self.cache.cleanup_outdated()
        self.assertFalse(self.cache.connections)
        self.assertFalse(self.cache.outdated)

    def assert_closed(self):
        self.assertTrue(self.closed.wait(5), "channel was not closed")
        self.channel.close.assert_called_once_with()

    def assert_finished(self):
        self.assertEqual(self.connection.calls, 0)
        self.assertFalse(self.connection._call_states)

    def test_cleanup_preserves_active_stream(self):
        stream = self.call(_StreamCall())
        self.assertEqual(next(stream), 1)
        self.cleanup_outdated()
        self.channel.close.assert_not_called()
        self.assertEqual(list(stream), [2])
        self.assert_finished()
        self.assert_closed()

    def test_cancellation_releases_connection(self):
        stream = self.call(_StreamCall())
        self.cleanup_outdated()
        self.channel.close.assert_not_called()
        stream.cancel()
        self.assert_finished()
        self.assert_closed()

    def test_rpc_completion_releases_unconsumed_stream(self):
        response = _StreamCall()
        stream = self.call(response)
        self.cleanup_outdated()
        self.channel.close.assert_not_called()
        response.complete()
        self.assert_finished()
        self.assert_closed()
        self.assertEqual(list(stream), [1, 2])

    def test_cleanup_waits_for_all_streams(self):
        first, second = self.call(_StreamCall()), self.call(_StreamCall())
        self.cleanup_outdated()
        first.cancel()
        self.assertEqual(self.connection.calls, 1)
        self.channel.close.assert_not_called()
        second.cancel()
        self.assert_finished()
        self.assert_closed()

    def test_terminal_cleanup_cancels_active_stream(self):
        response = _StreamCall()
        self.call(response)
        self.assertEqual(self.connection.calls, 1)

        def close_channel():
            response.cancel()
            self.closed.set()

        self.channel.close.side_effect = close_channel
        self.cache.cleanup()
        self.assert_closed()
        self.assertTrue(response.completed)
        self.assert_finished()
        self.assertFalse(self.cache.connections)

    def test_terminal_cleanup_cancels_retired_stream(self):
        response = _StreamCall()
        self.call(response)
        self.cleanup_outdated()
        self.channel.close.assert_not_called()

        def close_channel():
            response.cancel()
            self.closed.set()

        self.channel.close.side_effect = close_channel
        self.cache.cleanup()
        self.assert_closed()
        self.assertTrue(response.completed)
        self.assert_finished()

    def test_stale_remove_preserves_replacement(self):
        response = _StreamCall()
        self.call(response)
        self.cleanup_outdated()
        with patch.object(connection, "channel_factory", return_value=Mock()):
            replacement = connection.Connection(self.connection.endpoint)
        self.cache.add(replacement, preferred=True)
        self.cache.make_outdated(replacement)
        self.connection.close()
        for mapping, key in (
            (self.cache.connections, replacement.endpoint),
            (self.cache.connections_by_node_id, replacement.node_id),
            (self.cache.preferred, replacement.endpoint),
            (self.cache.outdated, replacement.endpoint),
        ):
            self.assertIs(mapping.get(key), replacement)
        response.cancel()
        self.assert_closed()

    def test_already_completed_rpc_releases_once(self):
        self.call(_StreamCall(completed=True))
        self.assert_finished()
        self.cleanup_outdated()
        self.assert_closed()

    def test_rpc_completing_during_subscription_releases_once(self):
        self.call(_StreamCall(complete_on_subscribe=True))
        self.assert_finished()
        self.cleanup_outdated()
        self.assert_closed()

    def test_unary_call_releases_connection(self):
        self.assertEqual(self.call(42), 42)
        self.assert_finished()
        self.cleanup_outdated()
        self.assert_closed()

    def test_wrapper_failure_releases_connection(self):
        def fail(*args):
            raise ValueError("invalid response")

        with self.assertRaisesRegex(ValueError, "invalid response"):
            self.call(_StreamCall(), wrap_result=fail)
        self.assert_finished()
        self.cleanup_outdated()
        self.assert_closed()

    def test_completion_callback_does_not_wait_for_channel_drain(self):
        response = _StreamCall()
        self.call(response)
        self.cleanup_outdated()
        self.channel.close.assert_not_called()
        callback_returned = threading.Event()
        errors = []

        def close_channel():
            if not callback_returned.wait(5):
                errors.append("channel.close blocked its completion callback")
            self.closed.set()

        self.channel.close.side_effect = close_channel

        def complete():
            try:
                response.complete()
            finally:
                callback_returned.set()

        completion = threading.Thread(target=complete, daemon=True)
        completion.start()
        self.assertTrue(callback_returned.wait(5), "completion callback blocked on channel.close")
        completion.join(5)
        self.assertFalse(completion.is_alive())
        self.assert_closed()
        self.assertFalse(errors, errors)
        self.assert_finished()

    def test_terminal_cleanup_callback_does_not_wait_for_channel_drain(self):
        response, active = _StreamCall(), _StreamCall()
        self.call(response)
        self.call(active)
        response.add_callback(self.cache.cleanup)
        callback_returned = threading.Event()
        errors = []

        def close_channel():
            if not callback_returned.wait(5):
                errors.append("channel.close blocked its completion callback")
            active.cancel()
            self.closed.set()

        self.channel.close.side_effect = close_channel

        def complete():
            try:
                response.complete()
            finally:
                callback_returned.set()

        completion = threading.Thread(target=complete, daemon=True)
        completion.start()
        self.assertTrue(callback_returned.wait(5), "completion callback blocked on channel.close")
        completion.join(5)
        self.assertFalse(completion.is_alive())
        self.assert_closed()
        self.assertFalse(errors, errors)
        self.assert_finished()


def test_connection_cache_cleanup_during_disconnect(monkeypatch):
    channel = Mock()
    channel_closed = threading.Event()
    channel.close.side_effect = channel_closed.set
    monkeypatch.setattr(connection, "channel_factory", lambda *args, **kwargs: channel)
    monkeypatch.setattr(connection, "_stubs_list", [])
    cached_connection = connection.Connection("localhost:1")
    cache = pool.ConnectionsCache()
    disconnect_entered = threading.Event()
    stop_entered = threading.Event()
    errors = []

    def before_remove(_):
        if threading.current_thread() is disconnect_thread:
            disconnect_entered.set()
            assert stop_entered.wait(5), "driver cleanup did not reach connection.close"

    cached_connection.add_cleanup_callback(before_remove)
    cache.add(cached_connection)
    cache.make_outdated(cached_connection)
    original_close = connection.Connection.close

    def close(self, *args, **kwargs):
        if threading.current_thread() is stop_thread:
            stop_entered.set()
        return original_close(self, *args, **kwargs)

    monkeypatch.setattr(connection.Connection, "close", close)

    def run(action):
        try:
            action()
        except BaseException as error:
            errors.append(error)

    disconnect_thread = threading.Thread(target=run, args=(cached_connection.close,), daemon=True)
    stop_thread = threading.Thread(
        target=run,
        args=(cache.cleanup,),
        daemon=True,
    )
    disconnect_thread.start()
    assert disconnect_entered.wait(5), "disconnect did not reach its cleanup callback"
    stop_thread.start()
    disconnect_thread.join(5)
    stop_thread.join(5)
    assert not disconnect_thread.is_alive(), "disconnect deadlocked with driver shutdown"
    assert not stop_thread.is_alive(), "driver shutdown deadlocked with disconnect"
    assert not errors, errors
    assert not cache.connections
    assert not cache.connections_by_node_id
    assert not cache.outdated
    assert channel_closed.wait(5), "driver shutdown did not close the channel"
    channel.close.assert_called_once()
