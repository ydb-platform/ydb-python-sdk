import sqlalchemy as sa
from sqlalchemy import text

import ydb


def test_get_columns(driver_sync, sa_engine):
    session = ydb.retry_operation_sync(lambda: driver_sync.table_client.session().create())
    session.execute_scheme("CREATE TABLE test(id Int64 NOT NULL, value TEXT, num DECIMAL(22, 9), PRIMARY KEY (id))")
    inspect = sa.inspect(sa_engine)
    columns = inspect.get_columns("test")
    for c in columns:
        c["type"] = type(c["type"])

    assert columns == [
        {"name": "id", "type": sa.INTEGER, "nullable": False},
        {"name": "value", "type": sa.TEXT, "nullable": True},
        {"name": "num", "type": sa.DECIMAL, "nullable": True},
    ]

    session.execute_scheme("DROP TABLE test")


def test_query_list(sa_engine):
    with sa_engine.connect() as connection:
        result = connection.execute(text("SELECT AsList(1, 2, 3, 4) as c"))
        row = next(result)
        assert row["c"] == [1, 2, 3, 4]
