from __future__ import absolute_import, print_function, unicode_literals

from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine
from sqlalchemy.dialects import registry
from sqlalchemy.sql import select

from ydb.sqlalchemy import YqlDialect, register_dialect


register_dialect()


engine = create_engine(
    'yql:///ydb/?database=/ru/home/gvit/mydb&endpoint=ydb-ru.yandex.net:2135', echo=True)

metadata = MetaData()
users = Table('users',
              metadata,
              Column('id', Integer, primary_key=True, nullable=True),
              Column('name', String, nullable=True),
              Column('fullname', String, nullable=True)
              )


def run():
    statement = select([users.c.fullname]) \
        .where(users.c.name == 'John') \
        .order_by(users.c.fullname)

    statement_str = str(statement.compile(dialect=engine.dialect, compile_kwargs=dict(literal_binds=True)))
    print('<<< ', statement_str.replace('\n', '  '))

    for row in engine.execute(statement):
        print('>>> ', row.fullname)


if __name__ == '__main__':
    run()
