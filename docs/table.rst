Table Service
=============

The Table service is the legacy API for schema management and bulk data operations.
Use it when you need operations that are not available through YQL — creating tables
with fine-grained partitioning, bulk loading data, streaming full table scans, or
managing secondary indexes programmatically.

For running queries use :doc:`query` instead. The Table service does not replace
the Query service; the two are complementary.

The Table service is accessed through ``driver.table_client``:

.. code-block:: python

    import ydb

    with ydb.Driver(endpoint="grpc://localhost:2136", database="/local") as driver:
        driver.wait(timeout=5, fail_fast=True)
        client = driver.table_client


Schema Management
-----------------

Creating a Table
^^^^^^^^^^^^^^^^

Build a :class:`~ydb.TableDescription` and pass it to ``create_table``:

.. code-block:: python

    driver.table_client.create_table(
        "/local/users",
        ydb.TableDescription()
        .with_columns(
            ydb.Column("id",   ydb.PrimitiveType.Uint64),
            ydb.Column("name", ydb.OptionalType(ydb.PrimitiveType.Utf8)),
            ydb.Column("age",  ydb.OptionalType(ydb.PrimitiveType.Uint32)),
        )
        .with_primary_keys("id"),
    )

Primary key columns must not be wrapped in :class:`~ydb.OptionalType` — they cannot be
``NULL``. All other columns should use :class:`~ydb.OptionalType` so rows with missing
values are accepted.

Dropping a Table
^^^^^^^^^^^^^^^^

.. code-block:: python

    driver.table_client.drop_table("/local/users")


Describing a Table
^^^^^^^^^^^^^^^^^^

``describe_table`` returns a :class:`~ydb.TableSchemeEntry` with column definitions, indexes,
TTL settings, and partition information:

.. code-block:: python

    entry = driver.table_client.describe_table("/local/users")

    for column in entry.columns:
        print(column.name, column.type)

    for index in entry.indexes:
        print(index.name, index.index_columns)

Pass :class:`~ydb.DescribeTableSettings` to request additional detail:

.. code-block:: python

    settings = ydb.DescribeTableSettings().with_include_shard_key_bounds(True)
    entry = driver.table_client.describe_table("/local/users", settings)


Altering a Table
^^^^^^^^^^^^^^^^

``alter_table`` accepts keyword arguments for each type of modification. Pass
only the arguments you need — unspecified arguments are left unchanged:

**Add or remove columns:**

.. code-block:: python

    driver.table_client.alter_table(
        "/local/users",
        add_columns=[ydb.Column("email", ydb.OptionalType(ydb.PrimitiveType.Utf8))],
        drop_columns=["age"],
    )

**Add or remove secondary indexes:**

.. code-block:: python

    driver.table_client.alter_table(
        "/local/users",
        add_indexes=[
            ydb.TableIndex("name_idx").with_index_columns("name"),
        ],
        drop_indexes=["old_idx"],
    )

**Modify TTL:**

.. code-block:: python

    driver.table_client.alter_table(
        "/local/users",
        set_ttl_settings=ydb.TtlSettings().with_date_type_column("expires_at"),
    )

    # Remove TTL
    driver.table_client.alter_table(
        "/local/users",
        drop_ttl_settings=ydb.DropTtl(),
    )

**Change partitioning settings:**

.. code-block:: python

    driver.table_client.alter_table(
        "/local/events",
        alter_partitioning_settings=(
            ydb.PartitioningSettings()
            .with_min_partitions_count(4)
            .with_max_partitions_count(256)
        ),
    )


Copying and Renaming Tables
^^^^^^^^^^^^^^^^^^^^^^^^^^^

``copy_table`` copies a single table:

.. code-block:: python

    driver.table_client.copy_table(
        "/local/users",
        "/local/users_backup",
    )

``copy_tables`` copies multiple tables atomically:

.. code-block:: python

    driver.table_client.copy_tables([
        ("/local/users",  "/local/backup/users"),
        ("/local/orders", "/local/backup/orders"),
    ])

``rename_tables`` renames (or moves) tables atomically:

.. code-block:: python

    driver.table_client.rename_tables([
        ("/local/users_new", "/local/users"),
    ])

If the destination already exists the call fails unless you add
``replace_destination=True`` to a ``RenameIndexItem`` — for table renames,
this replaces the destination atomically.


Secondary Indexes
-----------------

Indexes are defined via :class:`~ydb.TableIndex` when creating or altering a table.

**Global index** — built synchronously; the table is unavailable during index
construction when adding to an existing table:

.. code-block:: python

    ydb.TableIndex("name_idx").with_index_columns("name")

**Global async index** — built in the background; the table stays available:

.. code-block:: python

    ydb.TableIndex("name_idx").with_global_async_index().with_index_columns("name")

**Covered index** — stores extra columns in the index so queries can be answered
without a primary-key lookup:

.. code-block:: python

    ydb.TableIndex("name_age_idx") \
        .with_index_columns("name") \
        .with_data_columns("age", "email")

Full example — create a table with a covered index from the start:

.. code-block:: python

    driver.table_client.create_table(
        "/local/users",
        ydb.TableDescription()
        .with_columns(
            ydb.Column("id",    ydb.PrimitiveType.Uint64),
            ydb.Column("name",  ydb.OptionalType(ydb.PrimitiveType.Utf8)),
            ydb.Column("email", ydb.OptionalType(ydb.PrimitiveType.Utf8)),
            ydb.Column("age",   ydb.OptionalType(ydb.PrimitiveType.Uint32)),
        )
        .with_primary_keys("id")
        .with_indexes(
            ydb.TableIndex("name_idx")
            .with_index_columns("name")
            .with_data_columns("email"),
        ),
    )


TTL Settings
------------

YDB can automatically delete rows when a column value indicates the row has
expired. Two modes are available.

**Date-type column mode** — use a ``Date``, ``Datetime``, or ``Timestamp`` column
whose value is the expiry time. Rows with a value in the past are deleted:

.. code-block:: python

    ydb.TtlSettings().with_date_type_column("expires_at")

    # Optional: delay deletion by N seconds after expiry
    ydb.TtlSettings().with_date_type_column("expires_at", expire_after_seconds=3600)

**Value-since-unix-epoch mode** — use an integer column that stores time as a
Unix timestamp in the specified unit:

.. code-block:: python

    ydb.TtlSettings().with_value_since_unix_epoch(
        "created_ts",
        ydb.ColumnUnit.UNIT_SECONDS,
        expire_after_seconds=86400,   # delete rows 24 h after created_ts
    )

:class:`~ydb.ColumnUnit` values: ``UNIT_SECONDS``, ``UNIT_MILLISECONDS``,
``UNIT_MICROSECONDS``, ``UNIT_NANOSECONDS``.

Example — create a table where rows expire 7 days after creation:

.. code-block:: python

    driver.table_client.create_table(
        "/local/events",
        ydb.TableDescription()
        .with_columns(
            ydb.Column("id",         ydb.PrimitiveType.Uint64),
            ydb.Column("data",       ydb.OptionalType(ydb.PrimitiveType.Utf8)),
            ydb.Column("created_at", ydb.OptionalType(ydb.PrimitiveType.Timestamp)),
        )
        .with_primary_keys("id")
        .with_ttl(
            ydb.TtlSettings().with_date_type_column(
                "created_at",
                expire_after_seconds=7 * 24 * 3600,
            )
        ),
    )


Partitioning Settings
---------------------

:class:`~ydb.PartitioningSettings` controls how the table is split into shards and how
that split evolves over time:

.. code-block:: python

    ydb.PartitioningSettings() \
        .with_min_partitions_count(4) \
        .with_max_partitions_count(256) \
        .with_partition_size_mb(512) \
        .with_partitioning_by_load(ydb.FeatureFlag.ENABLED) \
        .with_partitioning_by_size(ydb.FeatureFlag.ENABLED)

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Method
     - Effect
   * - ``with_min_partitions_count(n)``
     - Table always has at least *n* shards.
   * - ``with_max_partitions_count(n)``
     - Table never exceeds *n* shards.
   * - ``with_partition_size_mb(mb)``
     - Target shard size; triggers a split when exceeded (requires by-size enabled).
   * - ``with_partitioning_by_size(flag)``
     - Auto-split when a shard grows beyond the target size.
   * - ``with_partitioning_by_load(flag)``
     - Auto-split hot shards and merge idle ones based on load.

:class:`~ydb.FeatureFlag` values: ``ENABLED``, ``DISABLED``, ``UNSPECIFIED``.

Pass ``PartitioningSettings`` to ``TableDescription.with_partitioning_settings``:

.. code-block:: python

    driver.table_client.create_table(
        "/local/events",
        ydb.TableDescription()
        .with_columns(
            ydb.Column("id",   ydb.PrimitiveType.Uint64),
            ydb.Column("data", ydb.OptionalType(ydb.PrimitiveType.Utf8)),
        )
        .with_primary_keys("id")
        .with_partitioning_settings(
            ydb.PartitioningSettings()
            .with_min_partitions_count(4)
            .with_max_partitions_count(64)
            .with_partitioning_by_load(ydb.FeatureFlag.ENABLED)
        ),
    )

**Pre-split at specific keys** — useful when the key distribution is known upfront:

.. code-block:: python

    driver.table_client.create_table(
        "/local/events",
        ydb.TableDescription()
        .with_columns(
            ydb.Column("id",   ydb.PrimitiveType.Uint64),
            ydb.Column("data", ydb.OptionalType(ydb.PrimitiveType.Utf8)),
        )
        .with_primary_keys("id")
        .with_partition_at_keys(
            ydb.ExplicitPartitions(
                [ydb.SplitPoint(1000), ydb.SplitPoint(2000), ydb.SplitPoint(3000)]
            )
        ),
    )


Column Families
---------------

Column families group columns for independent storage and compression settings.
Useful when a table has both hot (frequently read) and cold (rarely read) columns:

.. code-block:: python

    driver.table_client.create_table(
        "/local/users",
        ydb.TableDescription()
        .with_columns(
            ydb.Column("id",       ydb.PrimitiveType.Uint64),
            ydb.Column("name",     ydb.OptionalType(ydb.PrimitiveType.Utf8)),
            ydb.Column("bio",      ydb.OptionalType(ydb.PrimitiveType.Utf8),    family="blobs"),
            ydb.Column("avatar",   ydb.OptionalType(ydb.PrimitiveType.String),  family="blobs"),
        )
        .with_primary_keys("id")
        .with_column_families(
            ydb.ColumnFamily()
            .with_name("blobs")
            .with_compression(ydb.Compression.LZ4),
        ),
    )

:class:`~ydb.Compression` values: ``NONE``, ``LZ4``, ``UNSPECIFIED``.


Bulk Upsert
-----------

``bulk_upsert`` loads rows without going through a transaction. It is faster than
individual ``INSERT``/``UPSERT`` statements for large batches and is idempotent
(safe to retry on failure).

Build a :class:`~ydb.BulkUpsertColumns` descriptor that lists the columns and their types,
then pass it together with the rows:

.. code-block:: python

    from collections import namedtuple

    User = namedtuple("User", ["id", "name", "age"])

    rows = [
        User(id=1, name="Alice", age=30),
        User(id=2, name="Bob",   age=25),
        User(id=3, name="Carol", age=28),
    ]

    column_types = (
        ydb.BulkUpsertColumns()
        .add_column("id",   ydb.PrimitiveType.Uint64)
        .add_column("name", ydb.OptionalType(ydb.PrimitiveType.Utf8))
        .add_column("age",  ydb.OptionalType(ydb.PrimitiveType.Uint32))
    )

    driver.table_client.bulk_upsert("/local/users", rows, column_types)

Each row must be an object (named tuple, dataclass, or any object) whose
attributes match the column names in ``BulkUpsertColumns``.

.. note::

   ``bulk_upsert`` bypasses transaction guarantees. All rows in a single call
   are applied atomically, but there is no cross-call ordering. Prefer ``UPSERT``
   via the Query service when transactional semantics matter.


Streaming Reads
---------------

read_table
^^^^^^^^^^

``read_table`` streams all rows (or a key range) of a table without a
transaction. It is efficient for full-table exports and ETL pipelines:

.. code-block:: python

    def callee(session: ydb.table.Session):
        with session.read_table("/local/users", columns=("id", "name")) as it:
            for result_set in it:
                for row in result_set.rows:
                    print(row.id, row.name)

    driver.table_client.retry_operation_sync(callee)

``read_table`` is called on a ``Session`` object. Access a session through
``retry_operation_sync``, which handles session lifecycle and retries.

**Read a key range:**

.. code-block:: python

    key_type = ydb.TupleType().add_element(ydb.PrimitiveType.Uint64)

    key_range = ydb.KeyRange(
        from_bound=ydb.KeyBound.inclusive([1],    key_type),
        to_bound=ydb.KeyBound.exclusive([1000],   key_type),
    )

    def callee(session):
        with session.read_table(
            "/local/users",
            key_range=key_range,
            columns=("id", "name"),
            ordered=True,
        ) as it:
            for result_set in it:
                for row in result_set.rows:
                    print(row.id, row.name)

    driver.table_client.retry_operation_sync(callee)

:class:`~ydb.KeyBound`\ ``.inclusive([value], type)`` — the bound row is included.
:class:`~ydb.KeyBound`\ ``.exclusive([value], type)`` — the bound row is excluded.

Pass ``None`` to ``from_bound`` or ``to_bound`` of :class:`~ydb.KeyRange` to mean
"from the beginning" or "to the end" of the table.

**Parameters for read_table:**

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Parameter
     - Description
   * - ``path``
     - Full path to the table.
   * - ``key_range``
     - ``KeyRange`` to read; ``None`` reads the whole table.
   * - ``columns``
     - Tuple of column names to return; empty tuple returns all columns.
   * - ``ordered``
     - If ``True``, rows are returned in primary-key order (slower).
   * - ``row_limit``
     - Maximum number of rows to return.
   * - ``use_snapshot``
     - ``True`` to read a consistent snapshot (default server behaviour).

scan_query
^^^^^^^^^^

``scan_query`` executes a YQL query in streaming mode — the server sends result
chunks as they are produced without buffering the entire result set:

.. code-block:: python

    for result_set in driver.table_client.async_scan_query(
        "SELECT id, name FROM users WHERE age > 25"
    ):
        for row in result_set.rows:
            print(row.id, row.name)

Unlike ``execute_with_retries`` from the Query service, ``scan_query`` does not
buffer results and cannot be used inside a transaction.

Pass parameters with a ``ScanQueryParameters`` object or a plain dict:

.. code-block:: python

    for result_set in driver.table_client.async_scan_query(
        "DECLARE $min_age AS Uint32; SELECT id, name FROM users WHERE age > $min_age",
        parameters={"$min_age": (25, ydb.PrimitiveType.Uint32)},
    ):
        for row in result_set.rows:
            print(row.id, row.name)


Async Usage
-----------

The async table client is accessed the same way via ``driver.table_client``
on an async driver. All I/O methods become coroutines:

.. code-block:: python

    import asyncio
    import ydb

    async def main():
        async with ydb.aio.Driver(
            endpoint="grpc://localhost:2136", database="/local"
        ) as driver:
            await driver.wait(timeout=5, fail_fast=True)

            # Schema operations
            await driver.table_client.create_table(
                "/local/users",
                ydb.TableDescription()
                .with_columns(
                    ydb.Column("id",   ydb.PrimitiveType.Uint64),
                    ydb.Column("name", ydb.OptionalType(ydb.PrimitiveType.Utf8)),
                )
                .with_primary_keys("id"),
            )

            # Bulk upsert
            column_types = (
                ydb.BulkUpsertColumns()
                .add_column("id",   ydb.PrimitiveType.Uint64)
                .add_column("name", ydb.OptionalType(ydb.PrimitiveType.Utf8))
            )
            rows = [...]
            await driver.table_client.bulk_upsert("/local/users", rows, column_types)

            # Describe
            entry = await driver.table_client.describe_table("/local/users")
            for col in entry.columns:
                print(col.name, col.type)

            await driver.table_client.drop_table("/local/users")

    asyncio.run(main())


Complete Example
----------------

Create a table with TTL, a secondary index, and custom partitioning; load data
with ``bulk_upsert``; stream it back with ``read_table``:

.. code-block:: python

    import ydb
    from collections import namedtuple

    Event = namedtuple("Event", ["id", "user_id", "kind", "created_at"])

    with ydb.Driver(endpoint="grpc://localhost:2136", database="/local") as driver:
        driver.wait(timeout=5, fail_fast=True)

        # Create table
        driver.table_client.create_table(
            "/local/events",
            ydb.TableDescription()
            .with_columns(
                ydb.Column("id",         ydb.PrimitiveType.Uint64),
                ydb.Column("user_id",    ydb.OptionalType(ydb.PrimitiveType.Uint64)),
                ydb.Column("kind",       ydb.OptionalType(ydb.PrimitiveType.Utf8)),
                ydb.Column("created_at", ydb.OptionalType(ydb.PrimitiveType.Timestamp)),
            )
            .with_primary_keys("id")
            .with_indexes(
                ydb.TableIndex("user_idx").with_index_columns("user_id")
            )
            .with_ttl(
                ydb.TtlSettings().with_date_type_column(
                    "created_at",
                    expire_after_seconds=30 * 24 * 3600,
                )
            )
            .with_partitioning_settings(
                ydb.PartitioningSettings()
                .with_min_partitions_count(4)
                .with_max_partitions_count(64)
                .with_partitioning_by_load(ydb.FeatureFlag.ENABLED)
            ),
        )

        # Bulk load
        import datetime
        now = datetime.datetime.now(tz=datetime.timezone.utc)

        column_types = (
            ydb.BulkUpsertColumns()
            .add_column("id",         ydb.PrimitiveType.Uint64)
            .add_column("user_id",    ydb.OptionalType(ydb.PrimitiveType.Uint64))
            .add_column("kind",       ydb.OptionalType(ydb.PrimitiveType.Utf8))
            .add_column("created_at", ydb.OptionalType(ydb.PrimitiveType.Timestamp))
        )

        rows = [Event(i, i % 10, "click", now) for i in range(10000)]
        driver.table_client.bulk_upsert("/local/events", rows, column_types)

        # Stream all rows back
        def read_all(session):
            with session.read_table("/local/events", columns=("id", "user_id", "kind")) as it:
                for result_set in it:
                    for row in result_set.rows:
                        print(row.id, row.user_id, row.kind)

        driver.table_client.retry_operation_sync(read_all)

        # Clean up
        driver.table_client.drop_table("/local/events")
