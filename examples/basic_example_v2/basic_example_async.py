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
    series_id: Int64,
    title: Utf8,
    series_info: Utf8,
    release_date: Date>>;

DECLARE $seasonsData AS List<Struct<
    series_id: Int64,
    season_id: Int64,
    title: Utf8,
    first_aired: Date,
    last_aired: Date>>;

DECLARE $episodesData AS List<Struct<
    series_id: Int64,
    season_id: Int64,
    episode_id: Int64,
    title: Utf8,
    air_date: Date>>;

REPLACE INTO series
SELECT
    series_id,
    title,
    series_info,
    release_date
FROM AS_TABLE($seriesData);

REPLACE INTO seasons
SELECT
    series_id,
    season_id,
    title,
    first_aired,
    last_aired
FROM AS_TABLE($seasonsData);

REPLACE INTO episodes
SELECT
    series_id,
    season_id,
    episode_id,
    title,
    air_date
FROM AS_TABLE($episodesData);
"""


async def fill_tables_with_data(pool: ydb.aio.QuerySessionPoolAsync, path: str):
    print("\nFilling tables with data...")

    query = FillDataQuery.format(path)

    await pool.execute_with_retries(
        query,
        {
            "$seriesData": (basic_example_data.get_series_data(), basic_example_data.get_series_data_type()),
            "$seasonsData": (basic_example_data.get_seasons_data(), basic_example_data.get_seasons_data_type()),
            "$episodesData": (basic_example_data.get_episodes_data(), basic_example_data.get_episodes_data_type()),
        },
    )


async def select_simple(pool: ydb.aio.QuerySessionPoolAsync, path: str):
    print("\nCheck series table...")
    result_sets = await pool.execute_with_retries(
        f"""
        PRAGMA TablePathPrefix("{path}");
        SELECT
            series_id,
            title,
            release_date
        FROM series
        WHERE series_id = 1;
        """,
    )
    first_set = result_sets[0]
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


async def upsert_simple(pool: ydb.aio.QuerySessionPoolAsync, path: str):
    print("\nPerforming UPSERT into episodes...")

    await pool.execute_with_retries(
        f"""
        PRAGMA TablePathPrefix("{path}");
        UPSERT INTO episodes (series_id, season_id, episode_id, title) VALUES (2, 6, 1, "TBD");
        """
    )


async def select_with_parameters(pool: ydb.aio.QuerySessionPoolAsync, path: str, series_id, season_id, episode_id):
    result_sets = await pool.execute_with_retries(
        f"""
        PRAGMA TablePathPrefix("{path}");
        SELECT
            title,
            air_date
        FROM episodes
        WHERE series_id = $seriesId AND season_id = $seasonId AND episode_id = $episodeId;
        """,
        {
            "$seriesId": series_id,  # could be defined implicit
            "$seasonId": (season_id, ydb.PrimitiveType.Int64),  # could be defined via tuple
            "$episodeId": ydb.TypedValue(episode_id, ydb.PrimitiveType.Int64),  # could be defined via special class
        },
    )

    print("\n> select_with_parameters:")
    first_set = result_sets[0]
    for row in first_set.rows:
        print("episode title:", row.title, ", air date:", row.air_date)

    return first_set


# Show usage of explicit Begin/Commit transaction control calls.
# In most cases it's better to use transaction control settings in session.transaction
# calls instead to avoid additional hops to YDB cluster and allow more efficient
# execution of queries.
async def explicit_transaction_control(
    pool: ydb.aio.QuerySessionPoolAsync, path: str, series_id, season_id, episode_id
):
    async def callee(session: ydb.aio.QuerySessionAsync):
        query = f"""
        PRAGMA TablePathPrefix("{path}");
        UPDATE episodes
        SET air_date = CurrentUtcDate()
        WHERE series_id = $seriesId AND season_id = $seasonId AND episode_id = $episodeId;
        """

        # Get newly created transaction id
        tx = await session.transaction(ydb.QuerySerializableReadWrite()).begin()

        # Execute data query.
        # Transaction control settings continues active transaction (tx)
        async with await tx.execute(
            query,
            {
                "$seriesId": (series_id, ydb.PrimitiveType.Int64),
                "$seasonId": (season_id, ydb.PrimitiveType.Int64),
                "$episodeId": (episode_id, ydb.PrimitiveType.Int64),
            },
        ) as _:
            pass

        print("\n> explicit TCL call")

        # Commit active transaction(tx)
        await tx.commit()

    return await pool.retry_operation_async(callee)


async def huge_select(pool: ydb.aio.QuerySessionPoolAsync, path: str):
    async def callee(session: ydb.aio.QuerySessionAsync):
        query = f"""
        PRAGMA TablePathPrefix("{path}");
        SELECT * from episodes;
        """

        async with await session.transaction().execute(
            query,
            commit_tx=True,
        ) as result_sets:
            print("\n> Huge SELECT call")
            async for result_set in result_sets:
                for row in result_set.rows:
                    print("episode title:", row.title, ", air date:", row.air_date)

    return await pool.retry_operation_async(callee)


async def drop_tables(pool: ydb.aio.QuerySessionPoolAsync, path: str):
    print("\nCleaning up existing tables...")
    await pool.execute_with_retries(DropTablesQuery.format(path))


async def create_tables(pool: ydb.aio.QuerySessionPoolAsync, path: str):
    print("\nCreating table series...")
    await pool.execute_with_retries(
        f"""
        PRAGMA TablePathPrefix("{path}");
        CREATE table `series` (
            `series_id` Int64,
            `title` Utf8,
            `series_info` Utf8,
            `release_date` Date,
            PRIMARY KEY (`series_id`)
        )
        """
    )

    print("\nCreating table seasons...")
    await pool.execute_with_retries(
        f"""
        PRAGMA TablePathPrefix("{path}");
        CREATE table `seasons` (
            `series_id` Int64,
            `season_id` Int64,
            `title` Utf8,
            `first_aired` Date,
            `last_aired` Date,
            PRIMARY KEY (`series_id`, `season_id`)
        )
        """
    )

    print("\nCreating table episodes...")
    await pool.execute_with_retries(
        f"""
        PRAGMA TablePathPrefix("{path}");
        CREATE table `episodes` (
            `series_id` Int64,
            `season_id` Int64,
            `episode_id` Int64,
            `title` Utf8,
            `air_date` Date,
            PRIMARY KEY (`series_id`, `season_id`, `episode_id`)
        )
        """
    )


async def is_directory_exists(driver: ydb.aio.Driver, path: str):
    try:
        return await driver.scheme_client.describe_path(path).is_directory()
    except ydb.SchemeError:
        return False


async def ensure_path_exists(driver: ydb.aio.Driver, database, path):
    paths_to_create = list()
    path = path.rstrip("/")
    while path not in ("", database):
        full_path = posixpath.join(database, path)
        if await is_directory_exists(driver, full_path):
            break
        paths_to_create.append(full_path)
        path = posixpath.dirname(path).rstrip("/")

    while len(paths_to_create) > 0:
        full_path = paths_to_create.pop(-1)
        await driver.scheme_client.make_directory(full_path)


async def run(endpoint, database, path):
    async with ydb.aio.Driver(
        endpoint=endpoint,
        database=database,
        credentials=ydb.credentials_from_env_variables(),
    ) as driver:
        await driver.wait(timeout=5, fail_fast=True)

        async with ydb.aio.QuerySessionPoolAsync(driver) as pool:

            await ensure_path_exists(driver, database, path)

            # absolute path - prefix to the table's names,
            # including the database location
            full_path = posixpath.join(database, path)

            await drop_tables(pool, full_path)

            await create_tables(pool, full_path)

            await fill_tables_with_data(pool, full_path)

            await select_simple(pool, full_path)

            await upsert_simple(pool, full_path)

            await select_with_parameters(pool, full_path, 2, 3, 7)
            await select_with_parameters(pool, full_path, 2, 3, 8)

            await explicit_transaction_control(pool, full_path, 2, 6, 1)
            await select_with_parameters(pool, full_path, 2, 6, 1)
            await huge_select(pool, full_path)
