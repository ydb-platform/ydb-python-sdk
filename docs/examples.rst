Examples
===============

Basic example
^^^^^^^^^^^^^

All examples in this section are parts of `basic example <https://github.com/ydb-platform/ydb-python-sdk/tree/main/examples/basic_example_v2>`_.

For deeper upderstanding it is better to read the whole example.

Create table
------------

.. code-block:: python

    def create_tables(pool: ydb.QuerySessionPool):
        print("\nCreating table series...")
        pool.execute_with_retries(
            """
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
        pool.execute_with_retries(
            """
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
        pool.execute_with_retries(
            """
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


Upsert Simple
-------------

.. code-block:: python

    def upsert_simple(pool: ydb.QuerySessionPool):
        print("\nPerforming UPSERT into episodes...")

        pool.execute_with_retries(
            """
            UPSERT INTO episodes (series_id, season_id, episode_id, title) VALUES (2, 6, 1, "TBD");
            """
        )


Simple Select
----------

.. code-block:: python

    def select_simple(pool: ydb.QuerySessionPool):
        print("\nCheck series table...")
        result_sets = pool.execute_with_retries(
            """
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

Select With Parameters
----------------------

.. code-block:: python

    def select_with_parameters(pool: ydb.QuerySessionPool, series_id, season_id, episode_id):
        result_sets = pool.execute_with_retries(
            """
            DECLARE $seriesId AS Int64;
            DECLARE $seasonId AS Int64;
            DECLARE $episodeId AS Int64;

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

Huge Select
-----------

.. code-block:: python

    def huge_select(pool: ydb.QuerySessionPool):
        def callee(session: ydb.QuerySessionSync):
            query = """SELECT * from episodes;"""

            with session.transaction().execute(
                query,
                commit_tx=True,
            ) as result_sets:
                print("\n> Huge SELECT call")
                for result_set in result_sets:
                    for row in result_set.rows:
                        print("episode title:", row.title, ", air date:", row.air_date)

        return pool.retry_operation_sync(callee)

