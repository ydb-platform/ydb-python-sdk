import asyncio

import grpc
import pytest

from .common import callback_from_asyncio, GrpcWrapperAsyncIO, ServerStatus
from .. import issues

# Workaround for good autocomplete in IDE and universal import at runtime
# noinspection PyUnreachableCode
if False:
    from ydb._grpc.v4.protos import (
        ydb_status_codes_pb2,
        ydb_issue_message_pb2,
        ydb_topic_pb2,
    )
else:
    # noinspection PyUnresolvedReferences
    from ydb._grpc.common.protos import (
        ydb_status_codes_pb2,
        ydb_issue_message_pb2,
        ydb_topic_pb2,
    )

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

