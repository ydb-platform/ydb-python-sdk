import pytest
from ydb.aio.query.session import QuerySessionAsync

@pytest.fixture
async def session(driver):
    session = QuerySessionAsync(driver)

    yield session

    try:
        await session.delete()
    except BaseException:
        pass