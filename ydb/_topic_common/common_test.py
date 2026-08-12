import asyncio
import threading
import time
import typing

import grpc
import pytest

from .common import CallFromSyncToAsync, _get_shared_event_loop, _shutdown_shared_event_loop
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


def _shared_loop_threads_alive() -> bool:
    return any(t.name == "Common ydb topic event loop" and t.is_alive() for t in threading.enumerate())


def _force_stop_real_shared_loop():
    """Ensure module globals do not retain a live shared loop between mocked tests."""
    import ydb._topic_common.common as common

    loop = common._shared_event_loop
    thread = common._shared_event_loop_thread
    common._shared_event_loop = None
    common._shared_event_loop_thread = None
    if loop is not None:
        try:
            if loop.is_running():
                loop.call_soon_threadsafe(loop.stop)
        except RuntimeError:
            pass
    if thread is not None and thread.is_alive():
        thread.join(timeout=5)


class TestSharedEventLoop:
    def teardown_method(self):
        _shutdown_shared_event_loop()
        _force_stop_real_shared_loop()

    def test_shutdown_joins_thread(self):
        loop = _get_shared_event_loop()
        assert _shared_loop_threads_alive()

        fut = asyncio.run_coroutine_threadsafe(asyncio.sleep(0.01), loop)
        assert fut.result(1) is None

        _shutdown_shared_event_loop()
        assert not _shared_loop_threads_alive()

    def test_shutdown_is_idempotent_when_unused(self):
        _shutdown_shared_event_loop()
        _shutdown_shared_event_loop()
        assert not _shared_loop_threads_alive()

    def test_recreate_after_shutdown(self):
        loop = _get_shared_event_loop()
        fut = asyncio.run_coroutine_threadsafe(asyncio.sleep(0.01), loop)
        assert fut.result(1) is None

        _shutdown_shared_event_loop()
        assert not _shared_loop_threads_alive()

        loop2 = _get_shared_event_loop()
        assert loop2 is not loop
        assert _shared_loop_threads_alive()

        fut2 = asyncio.run_coroutine_threadsafe(asyncio.sleep(0.01), loop2)
        assert fut2.result(1) is None

        _shutdown_shared_event_loop()
        assert not _shared_loop_threads_alive()

    def test_get_returns_same_loop(self):
        loop1 = _get_shared_event_loop()
        loop2 = _get_shared_event_loop()
        assert loop1 is loop2

    def test_shutdown_cancels_pending_tasks(self):
        loop = _get_shared_event_loop()
        started = threading.Event()
        cancelled = threading.Event()

        async def long_running():
            started.set()
            try:
                await asyncio.sleep(3600)
            except asyncio.CancelledError:
                cancelled.set()
                raise

        asyncio.run_coroutine_threadsafe(long_running(), loop)
        assert started.wait(timeout=1)

        _shutdown_shared_event_loop()
        assert not _shared_loop_threads_alive()
        assert cancelled.wait(timeout=1)

    def test_shutdown_skips_stop_when_loop_not_running(self):
        import ydb._topic_common.common as common

        _force_stop_real_shared_loop()

        class FakeLoop:
            def __init__(self):
                self.stop_called = False

            def is_running(self):
                return False

            def call_soon_threadsafe(self, callback):
                self.stop_called = True

        loop = FakeLoop()
        common._shared_event_loop = loop
        common._shared_event_loop_thread = None

        _shutdown_shared_event_loop()

        assert not loop.stop_called
        assert common._shared_event_loop is None

    def test_shutdown_handles_stop_runtime_error(self, caplog):
        import logging

        import ydb._topic_common.common as common

        _force_stop_real_shared_loop()

        class FakeLoop:
            def is_running(self):
                return True

            def stop(self):
                return None

            def call_soon_threadsafe(self, callback):
                raise RuntimeError("loop is closed")

        common._shared_event_loop = FakeLoop()
        common._shared_event_loop_thread = None

        with caplog.at_level(logging.DEBUG):
            _shutdown_shared_event_loop()

        assert common._shared_event_loop is None
        assert any("already stopped" in r.message for r in caplog.records)

    def test_shutdown_warns_when_thread_does_not_stop(self, caplog):
        import logging

        import ydb._topic_common.common as common

        _force_stop_real_shared_loop()

        class FakeLoop:
            def is_running(self):
                return True

            def stop(self):
                return None

            def call_soon_threadsafe(self, callback):
                return None

        class StuckThread:
            def is_alive(self):
                return True

            def join(self, timeout=None):
                return None

        common._shared_event_loop = FakeLoop()
        common._shared_event_loop_thread = StuckThread()

        with caplog.at_level(logging.WARNING):
            _shutdown_shared_event_loop(timeout=0.01)

        assert common._shared_event_loop is None
        assert any("did not stop in time" in r.message for r in caplog.records)

    def test_cleanup_logs_when_cancelling_tasks_fails(self, monkeypatch, caplog):
        import logging

        loop = _get_shared_event_loop()
        fut = asyncio.run_coroutine_threadsafe(asyncio.sleep(0.01), loop)
        assert fut.result(1) is None

        def boom(_event_loop):
            raise RuntimeError("all_tasks failed")

        monkeypatch.setattr(asyncio, "all_tasks", boom)

        with caplog.at_level(logging.DEBUG):
            _shutdown_shared_event_loop()

        assert not _shared_loop_threads_alive()
        assert any("cancelling shared event loop tasks" in r.message for r in caplog.records)
