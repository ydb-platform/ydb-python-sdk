from unittest import mock

import grpc
import pytest
from grpc._cython import cygrpc

from ydb.aio.query.pool import QuerySessionPool
from ydb.aio.query.session import QuerySession


@pytest.fixture
async def session(driver):
    session = QuerySession(driver)

    yield session

    try:
        await session.delete()
    except BaseException:
        pass


@pytest.fixture
async def tx(session):
    await session.create()
    transaction = session.transaction()

    yield transaction

    try:
        await transaction.rollback()
    except BaseException:
        pass


@pytest.fixture
async def pool(driver):
    async with QuerySessionPool(driver) as pool:
        yield pool


@pytest.fixture
async def ydb_terminates_streams_with_unavailable():
    async def _patch(self):
        message = await self._read()  # Read the first message
        while message is not cygrpc.EOF:  # While the message is not empty, continue reading the stream
            yield message
            message = await self._read()

        # Emulate stream termination
        raise grpc.aio.AioRpcError(
            code=grpc.StatusCode.UNAVAILABLE,
            initial_metadata=await self.initial_metadata(),
            trailing_metadata=await self.trailing_metadata(),
        )

    with mock.patch.object(grpc.aio._call._StreamResponseMixin, "_fetch_stream_responses", _patch):
        yield
