import datetime
import logging
import argparse
import sqlalchemy as sa
from sqlalchemy import orm, exc, sql
from sqlalchemy import Table, Column, Integer, String, Float, TIMESTAMP
from ydb._sqlalchemy import register_dialect

from fill_tables import fill_all_tables, to_days
from models import Base, Series, Episodes


def describe_table(engine, name):
    inspect = sa.inspect(engine)
    print(f"describe table {name}:")
    for col in inspect.get_columns(name):
        print(f"\t{col['name']}: {col['type']}")


def simple_select(conn):
    stm = sa.select(Series).where(Series.series_id == 1)
    res = conn.execute(stm)
    print(res.one())


def simple_insert(conn):
    stm = Episodes.__table__.insert().values(
        series_id=3, season_id=6, episode_id=1, title="TBD"
    )
    conn.execute(stm)


def test_types(conn):
    types_tb = Table(
        "test_types",
        Base.metadata,
        Column("id", Integer, primary_key=True),
        Column("str", String),
        Column("num", Float),
        Column("dt", TIMESTAMP),
    )
    types_tb.drop(bind=conn.engine, checkfirst=True)
    types_tb.create(bind=conn.engine, checkfirst=True)

    stm = types_tb.insert().values(
        id=1,
        str=b"Hello World!",
        num=3.1415,
        dt=datetime.datetime.now(),
    )
    conn.execute(stm)

    # GROUP BY
    stm = sa.select(types_tb.c.str, sa.func.max(types_tb.c.num)).group_by(
        types_tb.c.str
    )
    rs = conn.execute(stm)
    for x in rs:
        print(x)


def run_example_orm(engine):
    Base.metadata.bind = engine
    Base.metadata.drop_all()
    Base.metadata.create_all()

    session = orm.sessionmaker(bind=engine)()

    rs = session.query(Episodes).all()
    for e in rs:
        print(f"{e.episode_id}: {e.title}")

    fill_all_tables(session.connection())

    try:
        session.add_all(
            [
                Episodes(
                    series_id=2,
                    season_id=1,
                    episode_id=1,
                    title="Minimum Viable Product",
                    air_date=to_days("2014-04-06"),
                ),
                Episodes(
                    series_id=2,
                    season_id=1,
                    episode_id=2,
                    title="The Cap Table",
                    air_date=to_days("2014-04-13"),
                ),
                Episodes(
                    series_id=2,
                    season_id=1,
                    episode_id=3,
                    title="Articles of Incorporation",
                    air_date=to_days("2014-04-20"),
                ),
                Episodes(
                    series_id=2,
                    season_id=1,
                    episode_id=4,
                    title="Fiduciary Duties",
                    air_date=to_days("2014-04-27"),
                ),
                Episodes(
                    series_id=2,
                    season_id=1,
                    episode_id=5,
                    title="Signaling Risk",
                    air_date=to_days("2014-05-04"),
                ),
            ]
        )
        session.commit()
    except exc.DatabaseError:
        print("Episodes already added!")
        session.rollback()

    rs = session.query(Episodes).all()
    for e in rs:
        print(f"{e.episode_id}: {e.title}")

    rs = session.query(Episodes).filter(Episodes.title == "abc??").all()
    for e in rs:
        print(e.title)

    print("Episodes count:", session.query(Episodes).count())

    max_episode = session.query(sql.expression.func.max(Episodes.episode_id)).scalar()
    print("Maximum episodes id:", max_episode)

    session.add(
        Episodes(
            series_id=2,
            season_id=1,
            episode_id=max_episode + 1,
            title="Signaling Risk",
            air_date=to_days("2014-05-04"),
        )
    )

    print("Episodes count:", session.query(Episodes).count())


def run_example_core(engine):
    with engine.connect() as conn:
        # raw sql
        rs = conn.execute("SELECT 1 AS value")
        print(rs.fetchone()["value"])

        fill_all_tables(conn)

        for t in "series seasons episodes".split():
            describe_table(engine, t)

        tb = sa.Table("episodes", sa.MetaData(engine), autoload=True)
        stm = (
            sa.select([tb.c.title])
            .where(sa.and_(tb.c.series_id == 1, tb.c.season_id == 3))
            .where(tb.c.title.like("%"))
            .order_by(sa.asc(tb.c.title))
            # TODO: limit isn't working now
            # .limit(3)
        )
        rs = conn.execute(stm)
        print(rs.fetchall())

        simple_select(conn)

        simple_insert(conn)

        # simple join
        stm = sa.select(
            [Episodes.__table__.join(Series, Episodes.series_id == Series.series_id)]
        ).where(sa.and_(Series.series_id == 1, Episodes.season_id == 1))
        rs = conn.execute(stm)
        for row in rs:
            print(f"{row.series_title}({row.episode_id}): {row.title}")

        rs = conn.execute(sa.select(Episodes).where(Episodes.series_id == 3))
        print(rs.fetchall())

        # count
        cnt = conn.execute(sa.func.count(Episodes.episode_id)).scalar()
        print("Episodes cnt:", cnt)

        # simple delete
        conn.execute(sa.delete(Episodes).where(Episodes.title == "TBD"))
        cnt = conn.execute(sa.func.count(Episodes.episode_id)).scalar()
        print("Episodes cnt:", cnt)

        test_types(conn)


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\033[92mYandex.Database examples _sqlalchemy usage.\x1b[0m\n""",
    )
    parser.add_argument(
        "-d",
        "--database",
        help="Name of the database to use",
        default="/local",
    )
    parser.add_argument(
        "-e",
        "--endpoint",
        help="Endpoint url to use",
        default="grpc://localhost:2136",
    )

    args = parser.parse_args()
    register_dialect()
    engine = sa.create_engine(
        "yql:///ydb/",
        connect_args={"database": args.database, "endpoint": args.endpoint},
    )

    logging.basicConfig(level=logging.INFO)
    logging.getLogger("_sqlalchemy.engine").setLevel(logging.INFO)

    run_example_core(engine)
    # run_example_orm(engine)


if __name__ == "__main__":
    main()
