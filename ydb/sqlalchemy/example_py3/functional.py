#!/usr/bin/env python3

from __future__ import absolute_import, print_function, unicode_literals

import os

import ydb
import sqlalchemy as sa

from ydb.sqlalchemy import register_dialect, ParametrizedFunction


TOKEN_FILE = "~/.yt/token"
YDB_CLUSTER = "ydb-ru"
YDB_DB = "/ru/home/hhell/mydb"
YDB_TABLE = "some_dir/test_table_e"


ENDPOINTS = {
    "ydb-ru-prestable": "ydb-ru-prestable.yandex.net:2135",
    "ydb-ru": "ydb-ru.yandex.net:2135",
}


token = open(os.path.expanduser(TOKEN_FILE)).read().strip()
register_dialect()
engine = sa.create_engine(
    "yql:///ydb/",
    connect_args=dict(
        database=YDB_DB,
        endpoint=ENDPOINTS[YDB_CLUSTER],
        auth_token=token,
    ),
    echo=True,
)
dialect = engine.dialect
qi = dialect.identifier_preparer.quote_identifier
metadata = sa.MetaData()
inspect = sa.inspect(engine)

table_alias = "1 some tbl"
original_table = sa.Table(YDB_TABLE, metadata)
table = original_table.alias(table_alias)

# Not working: table = sa.text(qi(YDB_DB) + '.' + qi(YDB_TABLE) + ' as ' + qi(table_alias))
# Working: table = sa.text(qi(YDB_DB + '/' + YDB_TABLE) + ' as ' + qi(table_alias))

col_id = sa.literal_column("{}.{}".format(qi(table_alias), "id")).label("r_id")
col_str = sa.literal_column("{}.{}".format(qi(table_alias), "some_string")).label(
    "r_str"
)
col_num = sa.literal_column("{}.{}".format(qi(table_alias), "some_uint64")).label(
    "r_num"
)
# select_columns = [col_id, col_str, col_num]
select_columns = [sa.literal_column("*")]
stmt = sa.select(select_columns).select_from(table).where(col_id > 1).order_by(col_num)


def list_tables(endpoint, database, auth_token, show_dot=False):
    driver = ydb.Driver(
        ydb.DriverConfig(
            endpoint=endpoint,
            database=database,
            auth_token=auth_token,
        )
    )
    driver.wait(timeout=5)

    queue = [database]

    while queue:
        path = queue.pop(0)
        resp = driver.scheme_client.async_list_directory(path)
        res = resp.result()
        children = [
            ("{}/{}".format(path, child.name), child)
            for child in res.children
            if show_dot or not child.name.startswith(".")
        ]
        children.sort()
        for full_path, child in children:
            if child.is_table():
                yield full_path
            elif child.is_directory():
                queue.append(full_path)


def run(table=table, stmt=stmt):
    # not expected to be supported: `inspect.get_table_names()`

    print("\n### Tables ###")
    ans = list_tables(ENDPOINTS[YDB_CLUSTER], database=YDB_DB, auth_token=token)
    for table in ans:
        print(table)

    print("### Table columns ###")
    columns = inspect.get_columns(table)
    for col in columns:
        print(col)

    print("\n### SQL ###")
    stmt_str = str(
        stmt.compile(
            dialect=engine.dialect,
            compile_kwargs=dict(literal_binds=True),
        )
    )

    pexpr = ParametrizedFunction(
        "Datetime::Format",
        [sa.literal("%Y-%m-%d %H:%M:%S")],
        sa.func.DateTime.FromSeconds(sa.literal(1568592000)),
    ).label("val")

    pstm = sa.select([pexpr])
    pstm_str = str(
        pstm.compile(dialect=engine.dialect, compile_kwargs=dict(literal_binds=True))
    )
    res = engine.execute(pstm_str)
    print(pstm_str)
    print(res)

    print("\n### SQL ###")
    print(stmt_str)

    print("\n### Result schema ###")
    res = engine.execute(stmt)
    for col in res.cursor.description:
        print(">>> ", col)
    print("\n### Result data ###")
    for row in res:
        print(">>> ", row)

    print("\n### Date/Datetime test ###")
    res = engine.execute('SELECT Date("2021-04-15"), Datetime("2019-09-16T00:00:00Z")')
    for row in res:
        print(">>> ", row)


if __name__ == "__main__":
    run()
