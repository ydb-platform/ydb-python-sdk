# -*- coding: utf-8 -*-
import os

from kikimr.public.sdk.python import client as ydb
from concurrent.futures import TimeoutError
import basic_example_data

FillDataQuery = """PRAGMA TablePathPrefix("{}");

DECLARE $seriesData AS "List<Struct<
    series_id: Uint64,
    title: Utf8,
    series_info: Utf8,
    release_date: Date>>";

DECLARE $seasonsData AS "List<Struct<
    series_id: Uint64,
    season_id: Uint64,
    title: Utf8,
    first_aired: Date,
    last_aired: Date>>";

DECLARE $episodesData AS "List<Struct<
    series_id: Uint64,
    season_id: Uint64,
    episode_id: Uint64,
    title: Utf8,
    air_date: Date>>";

REPLACE INTO series
SELECT
    series_id,
    title,
    series_info,
    CAST(release_date AS Uint64) AS release_date
FROM AS_TABLE($seriesData);

REPLACE INTO seasons
SELECT
    series_id,
    season_id,
    title,
    CAST(first_aired AS Uint64) AS first_aired,
    CAST(last_aired AS Uint64) AS last_aired
FROM AS_TABLE($seasonsData);

REPLACE INTO episodes
SELECT
    series_id,
    season_id,
    episode_id,
    title,
    CAST(air_date AS Uint64) AS air_date
FROM AS_TABLE($episodesData);
"""


def fill_tables_with_data(session, path):
    global FillDataQuery

    prepared_query = session.prepare(FillDataQuery.format(path))
    session.transaction(ydb.SerializableReadWrite()).execute(
        prepared_query, {
            '$seriesData': basic_example_data.get_series_data(),
            '$seasonsData': basic_example_data.get_seasons_data(),
            '$episodesData': basic_example_data.get_episodes_data(),
        },
        commit_tx=True,
    )


def select_simple(session, path):
    # new transaction in serializable read write mode
    # if query successfully completed you will get result sets.
    # otherwise exception will be raised
    result_sets = session.transaction(ydb.SerializableReadWrite()).execute(
        """
        PRAGMA TablePathPrefix("{}");
        SELECT series_id,
               title,
               DateTime::ToDate(DateTime::TimestampFromDays(release_date)) AS release_date
        FROM series
        WHERE series_id = 1;
        """.format(path),
        commit_tx=True,
    )
    print("\n> select_simple_transaction:")
    for row in result_sets[0].rows:
        print("series, id: ", row.series_id, ", title: ", row.title, ", release date: ", row.release_date)

    return result_sets[0]


def upsert_simple(session, path):
    session.transaction().execute(
        """
        PRAGMA TablePathPrefix("{}");
        UPSERT INTO episodes (series_id, season_id, episode_id, title) VALUES
            (2, 6, 1, "TBD");
        """.format(path),
        commit_tx=True,
    )


def select_prepared(session, path, series_id, season_id, episode_id):
    query = """
    PRAGMA TablePathPrefix("{}");

    DECLARE $seriesId AS Uint64;
    DECLARE $seasonId AS Uint64;
    DECLARE $episodeId AS Uint64;

    SELECT title,
           DateTime::ToDate(DateTime::TimestampFromDays(air_date)) AS air_date
    FROM episodes
    WHERE series_id = $seriesId AND season_id = $seasonId AND episode_id = $episodeId;
    """.format(path)

    prepared_query = session.prepare(query)
    result_sets = session.transaction(ydb.SerializableReadWrite()).execute(
        prepared_query, {
            '$seriesId': series_id,
            '$seasonId': season_id,
            '$episodeId': episode_id,
        },
        commit_tx=True
    )
    print("\n> select_prepared_transaction:")
    for row in result_sets[0].rows:
        print("episode title:", row.title, ", air date:", row.air_date)

    return result_sets[0]


# Show usage of explicit Begin/Commit transaction control calls.
# In most cases it's better to use transaction control settings in session.transaction
# calls instead to avoid additional hops to YDB cluster and allow more efficient
# execution of queries.
def explicit_tcl(session, path, series_id, season_id, episode_id):
    query = """
    PRAGMA TablePathPrefix("{}");

    DECLARE $seriesId AS Uint64;
    DECLARE $seasonId AS Uint64;
    DECLARE $episodeId AS Uint64;

    UPDATE episodes
    SET air_date = CAST(CurrentUtcDate() AS Uint64)
    WHERE series_id = $seriesId AND season_id = $seasonId AND episode_id = $episodeId;
    """.format(path)
    prepared_query = session.prepare(query)

    # Get newly created transaction id
    tx = session.transaction(ydb.SerializableReadWrite()).begin()

    # Execute data query.
    # Transaction control settings continues active transaction (tx)
    tx.execute(
        prepared_query, {
            '$seriesId': series_id,
            '$seasonId': season_id,
            '$episodeId': episode_id
        }
    )

    print("\n> explicit TCL call")

    # Commit active transaction(tx)
    tx.commit()


def create_tables(session, path):
    # Creating Series table
    session.create_table(
        os.path.join(path, 'series'),
        ydb.TableDescription()
        .with_column(ydb.Column('series_id', ydb.OptionalType(ydb.PrimitiveType.Uint64)))
        .with_column(ydb.Column('title', ydb.OptionalType(ydb.PrimitiveType.Utf8)))
        .with_column(ydb.Column('series_info', ydb.OptionalType(ydb.PrimitiveType.Utf8)))
        .with_column(ydb.Column('release_date', ydb.OptionalType(ydb.PrimitiveType.Uint64)))
        .with_primary_key('series_id')
    )

    # Creating Seasons table
    session.create_table(
        os.path.join(path, 'seasons'),
        ydb.TableDescription()
        .with_column(ydb.Column('series_id', ydb.OptionalType(ydb.PrimitiveType.Uint64)))
        .with_column(ydb.Column('season_id', ydb.OptionalType(ydb.PrimitiveType.Uint64)))
        .with_column(ydb.Column('title', ydb.OptionalType(ydb.PrimitiveType.Utf8)))
        .with_column(ydb.Column('first_aired', ydb.OptionalType(ydb.PrimitiveType.Uint64)))
        .with_column(ydb.Column('last_aired', ydb.OptionalType(ydb.PrimitiveType.Uint64)))
        .with_primary_keys('series_id', 'season_id')
    )

    # Creating Episodes table
    session.create_table(
        os.path.join(path, 'episodes'),
        ydb.TableDescription()
        .with_column(ydb.Column('series_id', ydb.OptionalType(ydb.PrimitiveType.Uint64)))
        .with_column(ydb.Column('season_id', ydb.OptionalType(ydb.PrimitiveType.Uint64)))
        .with_column(ydb.Column('episode_id', ydb.OptionalType(ydb.PrimitiveType.Uint64)))
        .with_column(ydb.Column('title', ydb.OptionalType(ydb.PrimitiveType.Utf8)))
        .with_column(ydb.Column('air_date', ydb.OptionalType(ydb.PrimitiveType.Uint64)))
        .with_primary_keys('series_id', 'season_id', 'episode_id')
    )


def describe_table(session, path, name):
    result = session.describe_table(os.path.join(path, name))
    print("\n> describe table: series")
    for column in result.columns:
        print("column, name:", column.name, ",", str(column.type.item).strip())


def bulk_upsert(table_client, path):
    print("\n> bulk upsert: episodes")
    column_types = ydb.BulkUpsertColumns() \
        .add_column('series_id', ydb.OptionalType(ydb.PrimitiveType.Uint64)) \
        .add_column('season_id', ydb.OptionalType(ydb.PrimitiveType.Uint64)) \
        .add_column('episode_id', ydb.OptionalType(ydb.PrimitiveType.Uint64)) \
        .add_column('title', ydb.OptionalType(ydb.PrimitiveType.Utf8)) \
        .add_column('air_date', ydb.OptionalType(ydb.PrimitiveType.Uint64))
    rows = basic_example_data.get_episodes_data_for_bulk_upsert()
    table_client.bulk_upsert(os.path.join(path, "episodes"), rows, column_types)


def is_directory_exists(driver, path):
    try:
        return driver.scheme_client.describe_path(path).is_directory()
    except ydb.SchemeError:
        return False


def ensure_path_exists(driver, database, path):
    paths_to_create = list()
    path = path.rstrip("/")
    while path not in ("", database):
        full_path = os.path.join(database, path)
        if is_directory_exists(driver, full_path):
            break
        paths_to_create.append(full_path)
        path = os.path.dirname(path).rstrip("/")

    while len(paths_to_create) > 0:
        full_path = paths_to_create.pop(-1)
        driver.scheme_client.make_directory(full_path)


def run(endpoint, database, path):
    driver_config = ydb.DriverConfig(
        endpoint, database, credentials=ydb.construct_credentials_from_environ(),
        root_certificates=ydb.load_ydb_root_certificate(),
    )
    with ydb.Driver(driver_config) as driver:
        try:
            driver.wait(timeout=5)
        except TimeoutError:
            print("Connect failed to YDB")
            print("Last reported errors by discovery:")
            print(driver.discovery_debug_details())
            exit(1)

        session = driver.table_client.session().create()
        ensure_path_exists(driver, database, path)

        full_path = os.path.join(database, path)

        create_tables(session, full_path)

        describe_table(session, full_path, "series")

        fill_tables_with_data(session, full_path)

        select_simple(session, full_path)

        upsert_simple(session, full_path)

        bulk_upsert(driver.table_client, full_path)

        select_prepared(session, full_path, 2, 3, 7)
        select_prepared(session, full_path, 2, 3, 8)

        explicit_tcl(session, full_path, 2, 6, 1)
        select_prepared(session, full_path, 2, 6, 1)
