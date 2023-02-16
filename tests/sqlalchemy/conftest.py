import pytest
import sqlalchemy as sa

from ydb._sqlalchemy import register_dialect


@pytest.fixture(scope="module")
def engine(endpoint, database):
    register_dialect()
    engine = sa.create_engine(
        "yql:///ydb/",
        connect_args={"database": database, "endpoint": endpoint},
    )

    yield engine
    engine.dispose()


@pytest.fixture(scope="module")
def connection(engine):
    with engine.connect() as conn:
        yield conn
