import pytest
from ydb.query.session import QuerySession
from ydb.query.pool import QuerySessionPool


@pytest.fixture
def session(driver_sync):
    session = QuerySession(driver_sync)

    yield session

    try:
        session.delete()
    except BaseException:
        pass


@pytest.fixture
def tx(session):
    session.create()
    transaction = session.transaction()

    yield transaction

    try:
        transaction.rollback()
    except BaseException:
        pass


@pytest.fixture
def pool(driver_sync):
    pool = QuerySessionPool(driver_sync)
    yield pool
