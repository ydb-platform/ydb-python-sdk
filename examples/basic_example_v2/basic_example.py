# -*- coding: utf-8 -*-
import posixpath
import ydb
import basic_example_data

# Table path prefix allows to put the working tables into the specific directory
# inside the YDB database. Putting `PRAGMA TablePathPrefix("some/path")`
# at the beginning of the query allows to reference the tables through
# their names "under" the specified directory.
#
# TablePathPrefix has to be defined as an absolute path, which has to be started
# with the current database location.
#
# https://ydb.tech/ru/docs/yql/reference/syntax/pragma#table-path-prefix

DropTablesQuery = """PRAGMA TablePathPrefix("{}");
DROP TABLE IF EXISTS series;
DROP TABLE IF EXISTS seasons;
DROP TABLE IF EXISTS episodes;
"""

FillDataQuery = """PRAGMA TablePathPrefix("{}");

DECLARE $seriesData AS List<Struct<
    series_id: Uint64,
    title: Utf8,
    series_info: Utf8,
    release_date: Date>>;

DECLARE $seasonsData AS List<Struct<
    series_id: Uint64,
    season_id: Uint64,
    title: Utf8,
    first_aired: Date,
    last_aired: Date>>;

DECLARE $episodesData AS List<Struct<
    series_id: Uint64,
    season_id: Uint64,
    episode_id: Uint64,
    title: Utf8,
    air_date: Date>>;

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


def fill_tables_with_data(pool, path):
    print("\nFilling tables with data...")

    global FillDataQuery

    def callee(session):

        prepared_query = FillDataQuery.format(path)
        with session.transaction(ydb.QuerySerializableReadWrite()).execute(
            prepared_query,
            {
                "$seriesData": (basic_example_data.get_series_data(), basic_example_data.get_series_data_type()),
                "$seasonsData": (basic_example_data.get_seasons_data(), basic_example_data.get_seasons_data_type()),
                "$episodesData": (basic_example_data.get_episodes_data(), basic_example_data.get_episodes_data_type()),
            },
            commit_tx=True,
        ) as result_sets:
            pass

    return pool.retry_operation_sync(callee)


def select_simple(pool, path):
    print("\nCheck series table...")

    def callee(session):
        # new transaction in serializable read write mode
        # if query successfully completed you will get result sets.
        # otherwise exception will be raised
        with session.transaction(ydb.QuerySerializableReadWrite()).execute(
            """
            PRAGMA TablePathPrefix("{}");
            $format = DateTime::Format("%Y-%m-%d");
            SELECT
                series_id,
                title,
                $format(DateTime::FromSeconds(CAST(DateTime::ToSeconds(DateTime::IntervalFromDays(CAST(release_date AS Int16))) AS Uint32))) AS release_date
            FROM series
            WHERE series_id = 1;
            """.format(
                path
            ),
            commit_tx=True,
        ) as result_sets:
            first_set = next(result_sets)
            for row in first_set.rows:
                print(
                    "series, id: ",
                    row.series_id,
                    ", title: ",
                    row.title,
                    ", release date: ",
                    row.release_date,
                )

            return first_set

    return pool.retry_operation_sync(callee)


def upsert_simple(pool, path):
    print(f"\nPerforming UPSERT into episodes...")

    def callee(session):
        with session.transaction().execute(
            """
            PRAGMA TablePathPrefix("{}");

            DECLARE $seriesId AS Uint64;
            DECLARE $seasonId AS Uint64;
            DECLARE $episodeId AS Uint64;
            DECLARE $title AS Utf8;

            UPSERT INTO episodes (series_id, season_id, episode_id, title) VALUES (2, 6, 1, "TBD");
            """.format(
                path
            ),
            commit_tx=True,
        ) as result_sets:
            pass

    return pool.retry_operation_sync(callee)


def select_with_parameters(pool, path, series_id, season_id, episode_id):
    def callee(session):
        query = """
        PRAGMA TablePathPrefix("{}");

        DECLARE $seriesId AS Uint64;
        DECLARE $seasonId AS Uint64;
        DECLARE $episodeId AS Uint64;

        $format = DateTime::Format("%Y-%m-%d");
        SELECT
            title,
            $format(DateTime::FromSeconds(CAST(DateTime::ToSeconds(DateTime::IntervalFromDays(CAST(air_date AS Int16))) AS Uint32))) AS air_date
        FROM episodes
        WHERE series_id = $seriesId AND season_id = $seasonId AND episode_id = $episodeId;
        """.format(
            path
        )

        with session.transaction(ydb.QuerySerializableReadWrite()).execute(
            query,
            {
                "$seriesId": series_id,  # could be defined implicit in case of int, str, bool
                "$seasonId": (season_id, ydb.PrimitiveType.Uint64),  # could be defined via tuple
                "$episodeId": ydb.TypedValue(
                    episode_id, ydb.PrimitiveType.Uint64
                ),  # could be defined via special class
            },
            commit_tx=True,
        ) as result_sets:
            print("\n> select_prepared_transaction:")
            first_set = next(result_sets)
            for row in first_set.rows:
                print("episode title:", row.title, ", air date:", row.air_date)

            return first_set

    return pool.retry_operation_sync(callee)


# Show usage of explicit Begin/Commit transaction control calls.
# In most cases it's better to use transaction control settings in session.transaction
# calls instead to avoid additional hops to YDB cluster and allow more efficient
# execution of queries.
def explicit_tcl(pool, path, series_id, season_id, episode_id):
    def callee(session):
        query = """
        PRAGMA TablePathPrefix("{}");

        DECLARE $seriesId AS Uint64;
        DECLARE $seasonId AS Uint64;
        DECLARE $episodeId AS Uint64;

        UPDATE episodes
        SET air_date = CAST(CurrentUtcDate() AS Uint64)
        WHERE series_id = $seriesId AND season_id = $seasonId AND episode_id = $episodeId;
        """.format(
            path
        )

        # Get newly created transaction id
        tx = session.transaction(ydb.QuerySerializableReadWrite()).begin()

        # Execute data query.
        # Transaction control settings continues active transaction (tx)
        with tx.execute(
            query,
            {"$seriesId": series_id, "$seasonId": season_id, "$episodeId": episode_id},
        ) as result_sets:
            pass

        print("\n> explicit TCL call")

        # Commit active transaction(tx)
        tx.commit()

    return pool.retry_operation_sync(callee)


def drop_tables(pool, path):
    print("\nCleaning up existing tables...")
    pool.execute_with_retries(DropTablesQuery.format(path))


def create_tables(pool, path):
    print("\nCreating table series...")
    pool.execute_with_retries(
        """
            PRAGMA TablePathPrefix("{}");
            CREATE table `series` (
                `series_id` Uint64,
                `title` Utf8,
                `series_info` Utf8,
                `release_date` Uint64,
                PRIMARY KEY (`series_id`)
            )
            """.format(
            path
        )
    )

    print("\nCreating table seasons...")
    pool.execute_with_retries(
        """
            PRAGMA TablePathPrefix("{}");
            CREATE table `seasons` (
                `series_id` Uint64,
                `season_id` Uint64,
                `title` Utf8,
                `first_aired` Uint64,
                `last_aired` Uint64,
                PRIMARY KEY (`series_id`, `season_id`)
            )
            """.format(
            path
        )
    )

    print("\nCreating table episodes...")
    pool.execute_with_retries(
        """
            PRAGMA TablePathPrefix("{}");
            CREATE table `episodes` (
                `series_id` Uint64,
                `season_id` Uint64,
                `episode_id` Uint64,
                `title` Utf8,
                `air_date` Uint64,
                PRIMARY KEY (`series_id`, `season_id`, `episode_id`)
            )
            """.format(
            path
        )
    )


def is_directory_exists(driver, path):
    try:
        return driver.scheme_client.describe_path(path).is_directory()
    except ydb.SchemeError:
        return False


def ensure_path_exists(driver, database, path):
    paths_to_create = list()
    path = path.rstrip("/")
    while path not in ("", database):
        full_path = posixpath.join(database, path)
        if is_directory_exists(driver, full_path):
            break
        paths_to_create.append(full_path)
        path = posixpath.dirname(path).rstrip("/")

    while len(paths_to_create) > 0:
        full_path = paths_to_create.pop(-1)
        driver.scheme_client.make_directory(full_path)


def run(endpoint, database, path):
    with ydb.Driver(
        endpoint=endpoint,
        database=database,
        # credentials=ydb.credentials_from_env_variables()
    ) as driver:
        driver.wait(timeout=5, fail_fast=True)

        with ydb.QuerySessionPool(driver) as pool:

            ensure_path_exists(driver, database, path)

            # absolute path - prefix to the table's names,
            # including the database location
            full_path = posixpath.join(database, path)

            drop_tables(pool, full_path)

            create_tables(pool, full_path)

            fill_tables_with_data(pool, full_path)

            select_simple(pool, full_path)

            upsert_simple(pool, full_path)

            select_with_parameters(pool, full_path, 2, 3, 7)
            select_with_parameters(pool, full_path, 2, 3, 8)

            explicit_tcl(pool, full_path, 2, 6, 1)
            select_with_parameters(pool, full_path, 2, 6, 1)
