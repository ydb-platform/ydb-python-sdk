import pytest
import sqlalchemy as sa

from ydb.sqlalchemy import register_dialect


@pytest.fixture
def sa_engine(endpoint, database):
    register_dialect()
    engine = sa.create_engine(
        "yql:///ydb/",
        connect_args={"database": database, "endpoint": endpoint},
    )

    yield engine
    engine.dispose()
