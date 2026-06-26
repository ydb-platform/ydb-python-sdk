import asyncio
import threading
import time
import typing

import grpc
import pytest

from .common import CallFromSyncToAsync
from ._stream_reconnector import StreamReconnector
from ._stream_connection import StreamConnection
from .test_helpers import wait_condition
from ..retries import RetrySettings
from .._grpc.grpcwrapper.common_utils import (
    GrpcWrapperAsyncIO,
    ServerStatus,
    callback_from_asyncio,
)
from .. import issues

# Workaround for good IDE and universal for runtime
if typing.TYPE_CHECKING:
    from ydb._grpc.v4.protos import (
        ydb_status_codes_pb2,
        ydb_topic_pb2,
    )
else:
    # noinspection PyUnresolvedReferences
    from ydb._grpc.common.protos import (
        ydb_status_codes_pb2,
        ydb_topic_pb2,
    )


@pytest.fixture()
def separate_loop():
    loop = asyncio.new_event_loop()

    def run_loop():
        loop.run_forever()
        pass

    t = threading.Thread(target=run_loop, name="test separate loop")
    t.start()

    yield loop

    loop.call_soon_threadsafe(lambda: loop.stop())
    t.join()


@pytest.mark.asyncio
class Test:
    async def test_callback_from_asyncio(self):
        class TestError(Exception):
            pass

        def sync_success():
            return 1

        assert await callback_from_asyncio(sync_success) == 1

        def sync_failed():
            raise TestError()

        with pytest.raises(TestError):
            await callback_from_asyncio(sync_failed)

        async def async_success():
            await asyncio.sleep(0)
            return 1

        assert await callback_from_asyncio(async_success) == 1

        async def async_failed():
            await asyncio.sleep(0)
            raise TestError()

        with pytest.raises(TestError):
            await callback_from_asyncio(async_failed)


@pytest.mark.asyncio
class TestGrpcWrapperAsyncIO:
    async def test_convert_grpc_errors_to_ydb(self):
        class TestError(grpc.RpcError, grpc.Call):
            def __init__(self):
                pass

            def code(self):
                return grpc.StatusCode.UNAUTHENTICATED

            def details(self):
                return "test error"

        class FromServerMock:
            async def __anext__(self):
                raise TestError()

        wrapper = GrpcWrapperAsyncIO(lambda: None)
        wrapper.from_server_grpc = FromServerMock()

        with pytest.raises(issues.Unauthenticated):
            await wrapper.receive()

    async def convert_status_code_to_ydb_error(self):
        class FromServerMock:
            async def __anext__(self):
                return ydb_topic_pb2.StreamReadMessage.FromServer(
                    status=ydb_status_codes_pb2.StatusIds.OVERLOADED,
                    issues=[],
                )

        wrapper = GrpcWrapperAsyncIO(lambda: None)
        wrapper.from_server_grpc = FromServerMock()

        with pytest.raises(issues.Overloaded):
            await wrapper.receive()


class TestServerStatus:
    def test_success(self):
        status = ServerStatus(
            status=ydb_status_codes_pb2.StatusIds.SUCCESS,
            issues=[],
        )
        assert status.is_success()
        assert issues._process_response(status) is None

    def test_failed(self):
        status = ServerStatus(
            status=ydb_status_codes_pb2.StatusIds.OVERLOADED,
            issues=[],
        )
        assert not status.is_success()
        with pytest.raises(issues.Overloaded):
            issues._process_response(status)


@pytest.mark.asyncio
class TestCallFromSyncToAsync:
    @pytest.fixture()
    def caller(self, separate_loop):
        return CallFromSyncToAsync(separate_loop)

    def test_unsafe_call_with_future(self, separate_loop, caller):
        callback_loop = None

        async def callback():
            nonlocal callback_loop
            callback_loop = asyncio.get_running_loop()
            return 1

        f = caller.unsafe_call_with_future(callback())

        assert f.result() == 1
        assert callback_loop is separate_loop

    def test_unsafe_call_with_result_ok(self, separate_loop, caller):
        callback_loop = None

        async def callback():
            nonlocal callback_loop
            callback_loop = asyncio.get_running_loop()
            return 1

        res = caller.unsafe_call_with_result(callback(), None)

        assert res == 1
        assert callback_loop is separate_loop

    def test_unsafe_call_with_result_timeout(self, separate_loop, caller):
        timeout = 0.01
        callback_loop = None

        async def callback():
            nonlocal callback_loop
            callback_loop = asyncio.get_running_loop()
            await asyncio.sleep(1)
            return 1

        start = time.monotonic()
        with pytest.raises(TimeoutError):
            caller.unsafe_call_with_result(callback(), timeout)
        finished = time.monotonic()

        assert callback_loop is separate_loop
        assert finished - start > timeout

    def test_safe_call_with_result_ok(self, separate_loop, caller):
        callback_loop = None

        async def callback():
            nonlocal callback_loop
            callback_loop = asyncio.get_running_loop()
            return 1

        res = caller.safe_call_with_result(callback(), 1)

        assert res == 1
        assert callback_loop is separate_loop

    def test_safe_call_with_result_timeout(self, separate_loop, caller):
        timeout = 0.01
        callback_loop = None
        cancelled = False

        async def callback():
            nonlocal callback_loop, cancelled
            callback_loop = asyncio.get_running_loop()
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                cancelled = True
                raise

            return 1

        start = time.monotonic()
        with pytest.raises(TimeoutError):
            caller.safe_call_with_result(callback(), timeout)
        finished = time.monotonic()

        # wait one loop for handle task cancelation
        asyncio.run_coroutine_threadsafe(asyncio.sleep(0), separate_loop)

        assert callback_loop is separate_loop
        assert finished - start > timeout
        assert cancelled

    def test_safe_callback_with_0_timeout_ok(self, separate_loop, caller):
        callback_loop = None

        async def f1():
            return 1

        async def f2():
            return await f1()

        async def callback():
            nonlocal callback_loop
            callback_loop = asyncio.get_running_loop()
            return await f2()

        res = caller.safe_call_with_result(callback(), 0)
        assert callback_loop is separate_loop
        assert res == 1

    def test_safe_callback_with_0_timeout_timeout(self, separate_loop, caller):
        callback_loop = None
        cancelled = False

        async def callback():
            try:
                nonlocal callback_loop, cancelled

                callback_loop = asyncio.get_running_loop()
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                cancelled = True
                raise

        with pytest.raises(TimeoutError):
            caller.safe_call_with_result(callback(), 0)

        assert callback_loop is separate_loop
        assert cancelled

    def test_call_sync_ok(self, separate_loop, caller):
        callback_eventloop = None

        def callback():
            nonlocal callback_eventloop
            callback_eventloop = asyncio.get_running_loop()
            return 1

        res = caller.call_sync(callback)
        assert callback_eventloop is separate_loop
        assert res == 1

    def test_call_sync_error(self, separate_loop, caller):
        callback_eventloop = None

        class TestError(RuntimeError):
            pass

        def callback():
            nonlocal callback_eventloop
            callback_eventloop = asyncio.get_running_loop()
            raise TestError

        with pytest.raises(TestError):
            caller.call_sync(callback)
        assert callback_eventloop is separate_loop


class _FakeConn:
    def __init__(self):
        self.close_calls = 0
        self.close_raises = None
        self._err = asyncio.Future()

    async def wait_error(self):
        raise await self._err

    def fail(self, err):
        if not self._err.done():
            self._err.set_result(err)

    async def close(self, flush=False):
        self.close_calls += 1
        if self.close_raises is not None:
            raise self.close_raises


class _FakeReconnector(StreamReconnector):
    def __init__(self, conns):
        self._conns = list(conns)
        super().__init__(retry_settings=RetrySettings())

    def _new_connection(self):
        if not self._conns:
            raise issues.Error("no more connections")
        return self._conns.pop(0)

    async def _handshake(self, conn):
        pass

    async def _run(self, conn):
        await conn.wait_error()

    async def _close_connection(self, conn, flush):
        await conn.close(flush)

    def _terminal_error(self):
        return issues.Error("reconnector closed")


class _FakeConnection(StreamConnection):
    async def _init_and_spawn(self, init_message=None):
        pass

    def _make_update_token_request(self, token):
        return ("update-token", token)


@pytest.mark.asyncio
class TestStreamReconnectorBase:
    async def test_reconnect_then_fatal(self):
        c1, c2 = _FakeConn(), _FakeConn()
        r = _FakeReconnector([c1, c2])
        await wait_condition(lambda: r.connection is c1)
        c1.fail(issues.Unavailable("retriable"))  # reconnect
        await wait_condition(lambda: r.connection is c2)
        c2.fail(issues.Error("fatal"))  # not retriable -> stop
        await wait_condition(lambda: r._fatal_error() is not None)
        assert isinstance(r._fatal_error(), issues.Error)
        assert c1.close_calls >= 1
        await r.close(False)

    async def test_cancelled_error_reconnects(self):
        c1, c2 = _FakeConn(), _FakeConn()
        r = _FakeReconnector([c1, c2])
        await wait_condition(lambda: r.connection is c1)
        c1.fail(asyncio.CancelledError())  # not closed -> ConnectionLost -> reconnect
        await wait_condition(lambda: r.connection is c2)
        await r.close(False)

    async def test_finally_swallows_close_error(self):
        c1, c2 = _FakeConn(), _FakeConn()
        c1.close_raises = RuntimeError("boom")
        r = _FakeReconnector([c1, c2])
        await wait_condition(lambda: r.connection is c1)
        c1.fail(issues.Unavailable("retriable"))
        await wait_condition(lambda: r.connection is c2)
        await r.close(False)

    async def test_close_without_connection_is_idempotent(self):
        r = _FakeReconnector([])  # connect fails immediately, _conn stays None
        await wait_condition(lambda: r._fatal_error() is not None)
        await r.close(False)  # _conn is None
        await r.close(False)  # already closed

    async def test_retriable_connect_failure_keeps_looping(self):
        c = _FakeConn()
        calls = {"n": 0}

        class R(_FakeReconnector):
            def _new_connection(self):
                calls["n"] += 1
                if calls["n"] == 1:
                    raise issues.Unavailable("retriable connect failure")  # conn stays None, loop retries
                return c

        r = R([])
        await wait_condition(lambda: r.connection is c)
        await r.close(False)


@pytest.mark.asyncio
class TestStreamConnectionBase:
    def _make(self, **kw):
        return _FakeConnection(from_proto=lambda x: x, stub=None, method="m", **kw)

    async def test_update_token_loop_without_token_function(self):
        # no interval -> guard returns immediately (no hot loop)
        conn = self._make(update_token_interval=None, get_token_function=lambda: "t")
        await conn._update_token_loop()
        # interval set but no token function -> loop returns after the first tick
        conn2 = self._make(update_token_interval=0, get_token_function=None)
        await conn2._update_token_loop()

    async def test_update_token_coroutine_and_no_stream(self):
        async def coro_token():
            return "T"

        conn = self._make(update_token_interval=0, get_token_function=coro_token)
        conn._stream = None  # exercise the "no stream" branch of _update_token
        conn._update_token_event.set()
        task = asyncio.create_task(conn._update_token_loop())
        await asyncio.sleep(0.02)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
