import ydb

import sqlalchemy as sa


def test_get_columns(driver_sync, sa_engine):
    session = ydb.retry_operation_sync(
        lambda: driver_sync.table_client.session().create()
    )
    session.execute_scheme(
        "CREATE TABLE test(id Int64 NOT NULL, value TEXT, num DECIMAL(22, 9), PRIMARY KEY (id))"
    )
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
