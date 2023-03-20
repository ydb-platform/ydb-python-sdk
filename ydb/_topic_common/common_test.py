import asyncio
import threading
import time
import typing

import grpc
import pytest

from .common import CallFromSyncToAsync
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
