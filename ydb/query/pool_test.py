from __future__ import annotations

import asyncio
import concurrent.futures
import inspect
import threading
import time
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import grpc
import pytest

from ydb import _apis, _utilities, connection, driver, issues, pool, resolver
from ydb.aio import pool as aio_pool
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


@pytest.fixture
def grpc_stream_server():
    release = threading.Event()
    finished = threading.Event()
    started = threading.Event()

    def stream(request, context):
        context.add_callback(finished.set)
        yield context.peer().encode()
        if release.wait(5) and context.is_active():
            if request == b"unavailable":
                context.abort(grpc.StatusCode.UNAVAILABLE, "test connection loss")
            if request == b"cancelled":
                context.abort(grpc.StatusCode.CANCELLED, "test cancellation")
            yield b"last response"

    def unary(request, context):
        context.add_callback(finished.set)
        started.set()
        release.wait(5)
        if request == b"unavailable":
            context.abort(grpc.StatusCode.UNAVAILABLE, "test connection loss")
        return b"unary response"

    with concurrent.futures.ThreadPoolExecutor() as executor:
        server = grpc.server(executor)
        server.add_generic_rpc_handlers(
            (
                grpc.method_handlers_generic_handler(
                    "Test",
                    {
                        "Stream": grpc.unary_stream_rpc_method_handler(stream),
                        "BidiStream": grpc.stream_stream_rpc_method_handler(stream),
                        "Peer": grpc.unary_unary_rpc_method_handler(lambda _request, context: context.peer().encode()),
                        "Unary": grpc.unary_unary_rpc_method_handler(unary),
                    },
                ),
            )
        )
        port = server.add_insecure_port("127.0.0.1:0")
        server.start()
        try:
            yield port, release, finished, started
        finally:
            release.set()
            server.stop(0).wait(5)


class StreamStub:
    def __init__(self, channel):
        self.Stream = channel.unary_stream("/Test/Stream")
        self.BidiStream = channel.stream_stream("/Test/BidiStream")
        self.Peer = channel.unary_unary("/Test/Peer")
        self.Unary = channel.unary_unary("/Test/Unary")


@pytest.mark.asyncio
@pytest.mark.parametrize("is_async", [False, True])
@pytest.mark.parametrize(
    "timeout,method,finish",
    [(0, "Stream", "deadline"), (0.5, "BidiStream", "deadline"), (60, "Stream", "drain"), (60, "Stream", "shutdown")],
    ids=["immediate", "force-bidi", "drain", "shutdown"],
)
async def test_discovery_drains_live_channel(grpc_stream_server, is_async, timeout, method, finish):
    port, release, finished, _ = grpc_stream_server
    config = driver.DriverConfig(f"grpc://127.0.0.1:{port}", "/local", grpc_channel_shutdown_timeout=timeout)
    module = aio_pool if is_async else pool
    cache = module.ConnectionsCache()
    discovery = module.Discovery(cache, config)

    def publish(node_id):
        endpoint = resolver.EndpointInfo(
            _apis.ydb_discovery.EndpointInfo(address="127.0.0.1", port=port, node_id=node_id, location="local")
        )
        result = resolver.DiscoveryResult("local", [endpoint])
        if is_async:
            discovery._resolver.resolve = AsyncMock(return_value=result)
        else:
            discovery._resolver.context_resolve = MagicMock()
            discovery._resolver.context_resolve.return_value.__enter__.return_value = result

    async def call(fn, *args):
        result = fn(*args)
        return await result if inspect.isawaitable(result) else result

    async def read(stream):
        return await anext(stream) if is_async else next(stream)

    async def wait_for_close(connection):
        while connection._channel is not None:
            await asyncio.sleep(0.01)

    try:
        publish(1)
        assert await call(discovery.execute_discovery)
        old = await call(cache.get)
        stream = await call(old, iter(()) if method == "BidiStream" else b"", StreamStub, method)
        old_peer = await read(stream)

        publish(2)
        assert await call(discovery.execute_discovery)
        replacement = await call(cache.get, connection.EndpointKey(old.endpoint, 1))
        assert replacement is not old and replacement.node_id == 2
        with pytest.raises(issues.ConnectionLost):
            await call(old, b"", StreamStub, "Peer")

        if timeout:
            assert not finished.is_set()

        # The node is still reachable, and the replacement has its own transport.
        assert await call(replacement, b"", StreamStub, "Peer") != old_peer
        if finish == "drain":
            release.set()
            assert await read(stream) == b"last response"
        else:
            if finish == "shutdown":
                await call(cache.cleanup)
            assert await asyncio.to_thread(finished.wait, 3)
            with pytest.raises(issues.ConnectionLost):
                await read(stream)

        await asyncio.wait_for(wait_for_close(old), timeout=3)
        if finish != "shutdown":
            assert await call(cache.get) is replacement
    finally:
        await call(cache.cleanup)


@pytest.mark.parametrize("timeout", [-1, float("inf"), float("nan")])
def test_shutdown_timeout_rejects_invalid_values(timeout):
    with pytest.raises(ValueError, match="grpc_channel_shutdown_timeout"):
        driver.DriverConfig("localhost:2135", grpc_channel_shutdown_timeout=timeout)


@pytest.mark.asyncio
@pytest.mark.parametrize("call_style", ["sync", "future", "async"])
async def test_retiring_channel_interrupts_pending_unary_rpc(grpc_stream_server, call_style):
    port, _, finished, started = grpc_stream_server
    is_async = call_style == "async"
    module = aio_pool if is_async else pool
    cache = module.ConnectionsCache()
    endpoint = f"127.0.0.1:{port}"
    conn = module.Connection(endpoint, driver.DriverConfig(endpoint, "/local"))
    cache.add(conn)
    try:
        if is_async:
            response = asyncio.create_task(conn(b"", StreamStub, "Unary"))
        elif call_style == "future":
            response = asyncio.wrap_future(conn.future(b"", StreamStub, "Unary"))
        else:
            response = asyncio.create_task(asyncio.to_thread(conn, b"", StreamStub, "Unary"))
        assert await asyncio.to_thread(started.wait, 3)

        cache.retire(conn, 0)
        with pytest.raises(issues.ConnectionLost):
            await asyncio.wait_for(response, timeout=3)
        assert await asyncio.to_thread(finished.wait, 3)
    finally:
        if is_async:
            await cache.cleanup()
        else:
            cache.cleanup()


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["Stream", "Unary"])
async def test_caller_cancellation_does_not_retire_channel(grpc_stream_server, method):
    port, _, _, started = grpc_stream_server
    endpoint = f"127.0.0.1:{port}"
    async with aio_pool.Connection(endpoint, driver.DriverConfig(endpoint, "/local")) as conn:
        if method == "Stream":
            stream = await conn(b"", StreamStub, method)
            peer = await anext(stream)
            stream.cancel()
            with pytest.raises(asyncio.CancelledError):
                await anext(stream)
            assert await conn(b"", StreamStub, "Peer") == peer
        else:
            response = asyncio.create_task(conn(b"", StreamStub, method))
            assert await asyncio.to_thread(started.wait, 3)
            response.cancel()
            with pytest.raises(asyncio.CancelledError):
                await response
            assert await conn(b"", StreamStub, "Peer")


def test_failed_future_start_does_not_keep_retired_channel_busy():
    endpoint = "127.0.0.1:1"
    with connection.Connection(endpoint, driver.DriverConfig(endpoint, "/local")) as conn:
        with patch.object(connection._RpcState, "future", side_effect=ValueError("gRPC channel closed")):
            with pytest.raises(ValueError, match="gRPC channel closed"):
                conn.future(b"", StreamStub, "Unary")
        assert conn.calls == 0
        assert conn.begin_retirement()
        conn.finish_retirement(time.monotonic())
        assert conn._channel is None


@pytest.mark.asyncio
@pytest.mark.parametrize("is_async", [False, True])
async def test_close_lets_pending_unary_rpc_finish(grpc_stream_server, is_async):
    port, release, _, started = grpc_stream_server
    endpoint = f"127.0.0.1:{port}"
    config = driver.DriverConfig(endpoint, "/local")
    if is_async:
        conn = aio_pool.Connection(endpoint, config)
        response = asyncio.create_task(conn(b"", StreamStub, "Unary"))
    else:
        conn = connection.Connection(endpoint, config)
        response = asyncio.wrap_future(conn.future(b"", StreamStub, "Unary"))

    try:
        assert await asyncio.to_thread(started.wait, 3)
        if is_async:
            closing = asyncio.create_task(conn.close())
            await asyncio.sleep(0)
            assert not closing.done()
        else:
            conn.close()
        assert conn.closing
        assert conn._channel is not None

        release.set()
        assert await asyncio.wait_for(response, timeout=3) == b"unary response"
        if is_async:
            await asyncio.wait_for(closing, timeout=3)
    finally:
        release.set()
        if is_async:
            await conn.close()
        else:
            conn.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("is_async", [False, True])
@pytest.mark.parametrize("request_body,error", [(b"unavailable", issues.Unavailable), (b"cancelled", issues.Cancelled)])
async def test_stream_reports_transport_failure_before_retirement(grpc_stream_server, is_async, request_body, error):
    port, release, _, _ = grpc_stream_server
    endpoint = f"127.0.0.1:{port}"
    config = driver.DriverConfig(endpoint, "/local")
    if is_async:
        callback = AsyncMock()
        async with aio_pool.Connection(endpoint, config) as conn:
            stream = await conn(request_body, StreamStub, "Stream", on_disconnected=callback)
            assert await anext(stream)
            release.set()
            with pytest.raises(error):
                await anext(stream)
    else:
        callback = MagicMock()
        with connection.Connection(endpoint, config) as conn:
            stream = conn(request_body, StreamStub, "Stream", on_disconnected=callback)
            assert next(stream)
            release.set()
            with pytest.raises(error):
                next(stream)

    if error is issues.Unavailable:
        callback.assert_called_once()
    else:
        callback.assert_not_called()


@pytest.mark.asyncio
async def test_unary_reports_transport_failure_before_retirement(grpc_stream_server):
    port, release, _, _ = grpc_stream_server
    endpoint = f"127.0.0.1:{port}"
    callback = AsyncMock()
    async with aio_pool.Connection(endpoint, driver.DriverConfig(endpoint, "/local")) as conn:
        release.set()
        with pytest.raises(issues.ConnectionLost):
            await conn(b"unavailable", StreamStub, "Unary", on_disconnected=callback)
        callback.assert_awaited_once()


def test_stream_finished_before_registration_does_not_delay_retirement(grpc_stream_server):
    port, release, _, _ = grpc_stream_server
    endpoint = f"127.0.0.1:{port}"
    with connection.Connection(endpoint, driver.DriverConfig(endpoint, "/local")) as conn:
        stub = StreamStub(conn._channel)
        state = connection._RpcState(stub, "Stream", endpoint, conn.endpoint_key)
        release.set()
        stream = stub.Stream(b"", timeout=5)
        assert len(list(stream)) == 2
        assert stream.code() is grpc.StatusCode.OK
        conn._track_stream(stream, state)
        assert not conn._stream_calls


def test_discovery_can_stop_after_recovering_from_a_failed_round():
    config = driver.DriverConfig("localhost:2135", "/local")
    cache = pool.ConnectionsCache()
    discovery = pool.Discovery(cache, config)
    discovery._base_emergency_retry_interval = 0
    discovery._base_discovery_interval = 0
    conn = connection.Connection(config.endpoint, config)
    cache.add(conn)

    outcomes = iter(["failed", "recovered", "stop"])

    def execute_round():
        outcome = next(outcomes)
        if outcome == "stop":
            discovery.stop()
        return outcome != "failed"

    with patch.object(discovery, "execute_discovery", side_effect=execute_round) as execute, patch.object(
        cache, "complete_discovery", wraps=cache.complete_discovery
    ) as complete:
        discovery.run()

    assert execute.call_count == 3
    assert isinstance(complete.call_args_list[0].args[0], issues.ConnectionFailure)
    assert complete.call_args_list[1].args == (None,)
    assert conn._channel is None
