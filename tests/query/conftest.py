import pytest
from ydb.query.session import QuerySessionSync


@pytest.fixture
def session(driver_sync):
    session = QuerySessionSync(driver_sync)

    yield session

    try:
        session.delete()
    except BaseException:
        pass

@pytest.fixture
def transaction(session):
    session.create()
    transaction = session.transaction()

    yield transaction

    try:
        transaction.rollback()
    except BaseException:
        pass

