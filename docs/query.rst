Query Service
=============

The Query service is the primary API for executing YQL queries in YDB.
It supports DDL (``CREATE TABLE``, ``DROP TABLE``) and DML (``SELECT``, ``INSERT``,
``UPDATE``, ``DELETE``) in a single unified interface with full transaction support.


QuerySessionPool
----------------

:class:`~ydb.QuerySessionPool` manages a pool of server-side sessions and provides safe,
retriable execution of queries. This is the main entry point for the Query service.

**Create a pool:**

.. code-block:: python

    import ydb

    with ydb.Driver(endpoint="grpc://localhost:2136", database="/local") as driver:
        driver.wait(timeout=5, fail_fast=True)

        with ydb.QuerySessionPool(driver) as pool:
            # ... use pool

The pool is closed automatically when used as a context manager. Call ``pool.stop()``
explicitly if not using ``with``.

**Async pool:**

.. code-block:: python

    import asyncio
    import ydb

    async def main():
        async with ydb.aio.Driver(endpoint="grpc://localhost:2136", database="/local") as driver:
            await driver.wait(timeout=5, fail_fast=True)

            async with ydb.aio.QuerySessionPool(driver) as pool:
                # ... use pool


Session Acquire Timeout
^^^^^^^^^^^^^^^^^^^^^^^

When the pool is exhausted (all sessions are in use), ``acquire()`` and ``checkout()``
block until a session becomes free. The default behavior is to wait indefinitely.

**Wait indefinitely (default):**

.. code-block:: python

    session = pool.acquire()          # blocks until a session is available
    session = pool.acquire(timeout=None)  # explicit, same behavior

**Fail immediately if no session is available:**

.. code-block:: python

    from ydb import SessionPoolEmpty

    try:
        session = pool.acquire(timeout=0)
    except SessionPoolEmpty:
        # no session was available right now
        ...

**Fail after a deadline:**

.. code-block:: python

    try:
        session = pool.acquire(timeout=5.0)
    except SessionPoolEmpty:
        # no session became available within 5 seconds
        ...

The same ``timeout`` parameter is available on ``checkout()``:

.. code-block:: python

    with pool.checkout(timeout=5.0) as session:
        ...

When using the retry helpers, set ``max_session_acquire_timeout`` in
:class:`~ydb.RetrySettings` to apply a per-call timeout across all retry attempts:

.. code-block:: python

    import ydb

    settings = ydb.RetrySettings(max_session_acquire_timeout=5.0)
    pool.retry_tx_sync(callee, retry_settings=settings)

.. warning::

   **Never call a retry helper from inside another retry helper on the same pool.**
   Each retry helper holds a session for the duration of the call. If the inner call
   also needs a session and the pool is full, both sides wait for each other and the
   program deadlocks silently.

   .. code-block:: python

       # WRONG — if pool size == 1 (or all sessions are taken), this deadlocks:
       def outer(tx):
           pool.retry_tx_sync(inner)   # tries to acquire a second session while one is held

       pool.retry_tx_sync(outer)

   If you need auxiliary data, load it before entering the outer retry call, or use a
   separate pool.


execute_with_retries
--------------------

The simplest way to run a query. Buffers all results into memory, retries on transient
errors, and runs outside any transaction:

.. code-block:: python

    # DDL
    pool.execute_with_retries("CREATE TABLE users (id Uint64, name Utf8, PRIMARY KEY (id))")

    # DML
    pool.execute_with_retries(
        "INSERT INTO users (id, name) VALUES (1, 'Alice'), (2, 'Bob')"
    )

    # Query with results
    result_sets = pool.execute_with_retries("SELECT id, name FROM users")
    for row in result_sets[0].rows:
        print(row["id"], row["name"])

.. note::

   ``execute_with_retries`` loads the entire result set into memory before returning.
   For large result sets use ``retry_operation_sync`` with streaming iteration instead.

**Async:**

.. code-block:: python

    result_sets = await pool.execute_with_retries("SELECT id, name FROM users")


Parameterized Queries
---------------------

Always use parameters instead of string interpolation to avoid SQL injection and
to allow the server to cache query plans.

**Implicit types** — Python values are mapped to YDB types automatically:

.. code-block:: python

    pool.execute_with_retries(
        "DECLARE $id AS Uint64; SELECT * FROM users WHERE id = $id",
        parameters={"$id": 42},
    )

**Explicit types via tuple** — pass ``(value, ydb_type)`` when the automatic mapping
is ambiguous or you need a specific type:

.. code-block:: python

    pool.execute_with_retries(
        "DECLARE $ids AS List<Int64>; SELECT * FROM users WHERE id IN $ids",
        parameters={"$ids": ([1, 2, 3], ydb.ListType(ydb.PrimitiveType.Int64))},
    )

**Explicit types via TypedValue:**

.. code-block:: python

    pool.execute_with_retries(
        "DECLARE $id AS Int64; SELECT * FROM users WHERE id = $id",
        parameters={"$id": ydb.TypedValue(42, ydb.PrimitiveType.Int64)},
    )

Common :class:`~ydb.PrimitiveType` values: ``Bool``, ``Int32``, ``Int64``, ``Uint32``,
``Uint64``, ``Float``, ``Double``, ``String``, ``Utf8``, ``Json``, ``Timestamp``,
``Date``, ``Datetime``.


retry_operation_sync
--------------------

Use this when you need manual control over a session — for example, to stream large
result sets or to execute multiple queries in sequence on the same session:

.. code-block:: python

    def callee(session: ydb.QuerySession):
        with session.execute("SELECT COUNT(*) AS cnt FROM users") as results:
            for result_set in results:
                print(result_set.rows[0]["cnt"])

    pool.retry_operation_sync(callee)

The pool acquires a session, calls ``callee(session)``, and retries the whole call on
retriable errors (e.g. ``UNAVAILABLE``, ``ABORTED``).

**Async:**

.. code-block:: python

    async def callee(session: ydb.aio.QuerySession):
        async with await session.execute("SELECT COUNT(*) AS cnt FROM users") as results:
            async for result_set in results:
                print(result_set.rows[0]["cnt"])

    await pool.retry_operation_async(callee)


retry_tx_sync
-------------

Use this to execute a group of queries atomically within a transaction.
The pool handles session acquisition, transaction begin, commit, and retries:

.. code-block:: python

    def callee(tx: ydb.QueryTxContext):
        with tx.execute("INSERT INTO users (id, name) VALUES (3, 'Carol')"):
            pass

    pool.retry_tx_sync(callee)

If ``callee`` raises a retriable error the whole function (including the transaction)
is re-executed from scratch — make sure ``callee`` is idempotent or relies on the
transaction's atomicity for correctness.

**Async:**

.. code-block:: python

    async def callee(tx: ydb.aio.QueryTxContext):
        async with await tx.execute("INSERT INTO users (id, name) VALUES (3, 'Carol')"):
            pass

    await pool.retry_tx_async(callee)

**With an explicit transaction mode:**

.. code-block:: python

    pool.retry_tx_sync(callee, tx_mode=ydb.QuerySnapshotReadOnly())


Transactions
------------

Transaction Modes
^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Mode
     - Description
   * - :class:`~ydb.QuerySerializableReadWrite`
     - Full ACID serializable isolation. Default. Supports reads and writes.
   * - :class:`~ydb.QuerySnapshotReadOnly`
     - Consistent read-only snapshot taken at transaction start.
   * - :class:`~ydb.QuerySnapshotReadWrite`
     - Snapshot reads with write support; write conflicts are possible.
   * - :class:`~ydb.QueryOnlineReadOnly`
     - Each read returns the most recent data at execution time. No cross-read consistency.
   * - :class:`~ydb.QueryOnlineReadOnly` ``(allow_inconsistent_reads=True)``
     - Fastest reads; even individual reads may be slightly inconsistent.
   * - :class:`~ydb.QueryStaleReadOnly`
     - Reads may lag by fractions of a second. Each individual read is consistent.

Manual Transaction Control
^^^^^^^^^^^^^^^^^^^^^^^^^^

Use ``session.transaction()`` when you need fine-grained control:

**Synchronous:**

.. code-block:: python

    def callee(session: ydb.QuerySession):
        with session.transaction() as tx:
            tx.begin()

            with tx.execute("INSERT INTO users (id, name) VALUES (4, 'Dave')"):
                pass

            with tx.execute("SELECT COUNT(*) AS cnt FROM users") as results:
                for result_set in results:
                    print("count:", result_set.rows[0]["cnt"])

            tx.commit()
            # tx.rollback() to discard changes instead

    pool.retry_operation_sync(callee)

**Commit on last query** — avoids an extra round-trip:

.. code-block:: python

    def callee(session: ydb.QuerySession):
        with session.transaction() as tx:
            tx.begin()

            with tx.execute(
                "INSERT INTO users (id, name) VALUES (5, 'Eve')",
                commit_tx=True,
            ):
                pass

    pool.retry_operation_sync(callee)

**Async:**

.. code-block:: python

    async def callee(session: ydb.aio.QuerySession):
        async with session.transaction() as tx:
            await tx.begin()

            async with await tx.execute(
                "INSERT INTO users (id, name) VALUES (4, 'Dave')"
            ):
                pass

            async with await tx.execute(
                "SELECT COUNT(*) AS cnt FROM users"
            ) as results:
                async for result_set in results:
                    print("count:", result_set.rows[0]["cnt"])

            await tx.commit()

    await pool.retry_operation_async(callee)


.. note::

   The transaction context manager calls ``rollback()`` automatically on exit if you
   did not commit explicitly.


Working with Result Sets
------------------------

``session.execute()`` and ``tx.execute()`` return an iterator of ``ResultSet`` objects.
A single query may return multiple result sets (e.g. when it contains multiple ``SELECT``
statements).

**Synchronous iteration:**

.. code-block:: python

    with session.execute("SELECT id, name FROM users ORDER BY id") as results:
        for result_set in results:
            for row in result_set.rows:
                print(row["id"], row["name"].decode())

**Async iteration:**

.. code-block:: python

    async with await session.execute("SELECT id, name FROM users") as results:
        async for result_set in results:
            for row in result_set.rows:
                print(row["id"], row["name"].decode())

**ResultSet fields:**

.. code-block:: python

    result_set.rows      # list of Row objects — access columns by name: row["col"]
    result_set.columns   # list of column descriptors with .name and .type
    result_set.truncated # True if the server truncated results (use pagination)

.. note::

   ``String`` columns return ``bytes``; ``Utf8`` columns return ``str``.
   Decode as needed: ``row["name"].decode("utf-8")``.


DDL Queries
-----------

DDL is executed the same way as DML — through the pool or a session:

.. code-block:: python

    pool.execute_with_retries(
        """
        CREATE TABLE orders (
            order_id Uint64,
            user_id  Uint64,
            amount   Double,
            created  Timestamp,
            PRIMARY KEY (order_id)
        )
        """
    )

    pool.execute_with_retries("DROP TABLE IF EXISTS orders")


Complete Examples
-----------------

Synchronous
^^^^^^^^^^^

.. code-block:: python

    import ydb

    with ydb.Driver(endpoint="grpc://localhost:2136", database="/local") as driver:
        driver.wait(timeout=5, fail_fast=True)

        with ydb.QuerySessionPool(driver) as pool:

            # Schema
            pool.execute_with_retries("DROP TABLE IF EXISTS users")
            pool.execute_with_retries(
                "CREATE TABLE users (id Uint64, name Utf8, PRIMARY KEY (id))"
            )

            # Insert in a transaction
            def insert(tx: ydb.QueryTxContext):
                with tx.execute(
                    "INSERT INTO users (id, name) VALUES (1, 'Alice'), (2, 'Bob')",
                    commit_tx=True,
                ):
                    pass

            pool.retry_tx_sync(insert)

            # Read
            result_sets = pool.execute_with_retries("SELECT id, name FROM users")
            for row in result_sets[0].rows:
                print(row["id"], row["name"])


Asynchronous
^^^^^^^^^^^^

.. code-block:: python

    import asyncio
    import ydb

    async def main():
        async with ydb.aio.Driver(
            endpoint="grpc://localhost:2136", database="/local"
        ) as driver:
            await driver.wait(timeout=5, fail_fast=True)

            async with ydb.aio.QuerySessionPool(driver) as pool:

                # Schema
                await pool.execute_with_retries("DROP TABLE IF EXISTS users")
                await pool.execute_with_retries(
                    "CREATE TABLE users (id Uint64, name Utf8, PRIMARY KEY (id))"
                )

                # Insert in a transaction
                async def insert(tx: ydb.aio.QueryTxContext):
                    async with await tx.execute(
                        "INSERT INTO users (id, name) VALUES (1, 'Alice'), (2, 'Bob')",
                        commit_tx=True,
                    ):
                        pass

                await pool.retry_tx_async(insert)

                # Read
                result_sets = await pool.execute_with_retries(
                    "SELECT id, name FROM users"
                )
                for row in result_sets[0].rows:
                    print(row["id"], row["name"])

    asyncio.run(main())


Apache Arrow Format
-------------------

By default query results are returned as YDB value objects. For analytics workloads
you can request results in `Apache Arrow <https://arrow.apache.org/>`_ IPC format,
which integrates directly with pandas, polars, and other columnar tools. Requires
``pyarrow`` to be installed (``pip install pyarrow``).

.. code-block:: python

    import pyarrow as pa
    import ydb

    result_sets = pool.execute_with_retries(
        "SELECT id, name, score FROM users ORDER BY id LIMIT 1000",
        result_set_format=ydb.QueryResultSetFormat.ARROW,
    )

    for result_set in result_sets:
        schema = pa.ipc.read_schema(pa.py_buffer(result_set.arrow_format_meta.schema))
        batch  = pa.ipc.read_record_batch(pa.py_buffer(result_set.data), schema)
        df = batch.to_pandas()
        print(df.head())

Arrow results can also be compressed on the wire. Pass ``arrow_format_settings`` to
choose a codec:

.. code-block:: python

    settings = ydb.ArrowFormatSettings(
        compression_codec=ydb.ArrowCompressionCodec(
            ydb.ArrowCompressionCodecType.ZSTD,
            level=10,
        )
    )

    result_sets = pool.execute_with_retries(
        "SELECT * FROM events LIMIT 100000",
        result_set_format=ydb.QueryResultSetFormat.ARROW,
        arrow_format_settings=settings,
    )

.. note::

   Arrow format is only useful when you process results with a columnar library.
   For regular row-by-row processing use the default ``VALUE`` format — it has
   no extra dependencies and lower overhead for small result sets.


Query Stats and Explain
-----------------------

Query Stats
^^^^^^^^^^^

YDB can return execution statistics alongside query results. Pass a :class:`~ydb.QueryStatsMode`
value as ``stats_mode`` to ``session.execute()`` or ``tx.execute()``, then read
``last_query_stats`` after the iterator is consumed:

.. code-block:: python

    def callee(session: ydb.QuerySession):
        with session.execute(
            "SELECT * FROM users",
            stats_mode=ydb.QueryStatsMode.BASIC,
        ):
            pass  # must iterate to completion for stats to be populated

        print(session.last_query_stats)

    pool.retry_operation_sync(callee)

The same works inside a transaction — stats reflect the last executed statement:

.. code-block:: python

    def callee(tx: ydb.QueryTxContext):
        with tx.execute(
            "SELECT COUNT(*) AS cnt FROM users",
            stats_mode=ydb.QueryStatsMode.FULL,
        ) as results:
            for result_set in results:
                print(result_set.rows[0]["cnt"])

        print(tx.last_query_stats)

    pool.retry_tx_sync(callee)

**Stats modes:**

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - :class:`~ydb.QueryStatsMode` value
     - What is returned
   * - ``QueryStatsMode.NONE``
     - No statistics (default).
   * - ``QueryStatsMode.BASIC``
     - Row counts and execution time per stage.
   * - ``QueryStatsMode.FULL``
     - Full per-operator statistics.
   * - ``QueryStatsMode.PROFILE``
     - Full statistics plus the query execution plan. Use this for performance
       investigations.


Explain
^^^^^^^

``explain`` returns the query execution plan without actually running the query.
Use it to understand how YDB will execute a statement before sending it to
production:

.. code-block:: python

    # Returns a JSON string
    plan = pool.explain_with_retries("SELECT * FROM users WHERE id = 1")
    print(plan)

    # Returns a parsed dict
    plan_dict = pool.explain_with_retries(
        "SELECT * FROM users WHERE id = 1",
        result_format=ydb.QueryExplainResultFormat.DICT,
    )
    print(plan_dict["Plan"])

You can also call ``explain`` directly on a session:

.. code-block:: python

    def callee(session: ydb.QuerySession):
        plan = session.explain("SELECT * FROM users WHERE id = 1")
        print(plan)

    pool.retry_operation_sync(callee)
