import pytest
from ydb.aio.query.session import QuerySessionAsync
from ydb.aio.query.pool import QuerySessionPoolAsync


@pytest.fixture
async def session(driver):
    session = QuerySessionAsync(driver)

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
    async with QuerySessionPoolAsync(driver) as pool:
        yield pool
