Scheme Service
==============

The Scheme service manages the YDB path hierarchy — databases, directories, tables,
topics, and other named objects. It is available through ``driver.scheme_client`` on
both the synchronous and asynchronous driver.

A typical use case is ensuring that a directory tree exists before creating tables,
or introspecting the schema at runtime.


Directories
-----------

Create a Directory
^^^^^^^^^^^^^^^^^^

Directories work like filesystem folders. They are used to organise tables and other
objects within a database:

.. code-block:: python

    driver.scheme_client.make_directory("/local/my_app")

    # Nested directories must be created one level at a time
    driver.scheme_client.make_directory("/local/my_app/production")
    driver.scheme_client.make_directory("/local/my_app/staging")

A helper to ensure an entire path exists, creating each missing segment:

.. code-block:: python

    import os
    import ydb

    def ensure_path(driver: ydb.Driver, path: str) -> None:
        parts = []
        head = path.rstrip("/")
        while head:
            try:
                if driver.scheme_client.describe_path(head).is_directory_or_database():
                    break
            except ydb.SchemeError:
                pass
            parts.append(head)
            head = os.path.dirname(head).rstrip("/")

        for p in reversed(parts):
            driver.scheme_client.make_directory(p)

Remove a Directory
^^^^^^^^^^^^^^^^^^

The directory must be empty before it can be removed:

.. code-block:: python

    driver.scheme_client.remove_directory("/local/my_app/staging")


List a Directory
^^^^^^^^^^^^^^^^

``list_directory`` returns a :class:`~ydb.SchemeEntry` for each immediate child of the path,
plus a ``self`` entry describing the path itself:

.. code-block:: python

    listing = driver.scheme_client.list_directory("/local/my_app")

    # listing.self — SchemeEntry for /local/my_app itself
    print(listing.self.name, listing.self.type)

    # listing.children — list of SchemeEntry for immediate children
    for entry in listing.children:
        print(entry.name, entry.type)

Filter by type to find, for example, all tables in a directory:

.. code-block:: python

    listing = driver.scheme_client.list_directory("/local/my_app")
    tables = [e for e in listing.children if e.is_table()]
    topics = [e for e in listing.children if e.type == ydb.SchemeEntryType.TOPIC]


Describing Paths
----------------

``describe_path`` returns a :class:`~ydb.SchemeEntry` for any path — table, topic, directory,
coordination node, etc.:

.. code-block:: python

    entry = driver.scheme_client.describe_path("/local/my_app/users")

    print(entry.name)        # "users"
    print(entry.owner)       # owner login
    print(entry.type)        # SchemeEntryType.TABLE
    print(entry.size_bytes)  # approximate size


SchemeEntry
-----------

Every scheme object is described by a :class:`~ydb.SchemeEntry`:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Field
     - Description
   * - ``name``
     - Object name (last path component).
   * - ``type``
     - :class:`~ydb.SchemeEntryType` enum value.
   * - ``owner``
     - Login of the object owner.
   * - ``size_bytes``
     - Approximate on-disk size (tables only; 0 for directories).
   * - ``permissions``
     - Explicit ACL entries set on this object.
   * - ``effective_permissions``
     - Effective ACL entries (including inherited from parent).

**Convenience predicates:**

.. code-block:: python

    entry.is_directory()           # DIRECTORY
    entry.is_database()            # DATABASE
    entry.is_table()               # TABLE (row-oriented)
    entry.is_column_table()        # COLUMN_TABLE (column-oriented)
    entry.is_column_store()        # COLUMN_STORE
    entry.is_any_table()           # TABLE or COLUMN_TABLE
    entry.is_directory_or_database()
    entry.is_coordination_node()   # COORDINATION_NODE
    entry.is_external_table()      # EXTERNAL_TABLE
    entry.is_external_data_source() # EXTERNAL_DATA_SOURCE
    entry.is_view()                # VIEW
    entry.is_resource_pool()       # RESOURCE_POOL
    entry.is_sysview()             # SYS_VIEW

**SchemeEntryType enum values:**

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Value
     - Meaning
   * - ``SchemeEntryType.DIRECTORY``
     - Directory
   * - ``SchemeEntryType.DATABASE``
     - Database root
   * - ``SchemeEntryType.TABLE``
     - Row-oriented table
   * - ``SchemeEntryType.COLUMN_TABLE``
     - Column-oriented table
   * - ``SchemeEntryType.COLUMN_STORE``
     - Column store (groups column tables)
   * - ``SchemeEntryType.TOPIC``
     - Topic (message queue)
   * - ``SchemeEntryType.PERS_QUEUE_GROUP``
     - Legacy PersQueue group (predecessor of Topic)
   * - ``SchemeEntryType.COORDINATION_NODE``
     - Coordination service node
   * - ``SchemeEntryType.EXTERNAL_TABLE``
     - External table (federated query)
   * - ``SchemeEntryType.EXTERNAL_DATA_SOURCE``
     - External data source (federated query)
   * - ``SchemeEntryType.VIEW``
     - View
   * - ``SchemeEntryType.SEQUENCE``
     - Sequence (auto-increment counter)
   * - ``SchemeEntryType.REPLICATION``
     - Async replication object
   * - ``SchemeEntryType.TRANSFER``
     - Data transfer object
   * - ``SchemeEntryType.RESOURCE_POOL``
     - Resource pool (workload management)
   * - ``SchemeEntryType.SYS_VIEW``
     - System view
   * - ``SchemeEntryType.TYPE_UNSPECIFIED``
     - Unknown or unsupported type


Async Usage
-----------

The async scheme client has the same methods with ``await``:

.. code-block:: python

    import asyncio
    import ydb

    async def main():
        async with ydb.aio.Driver(
            endpoint="grpc://localhost:2136", database="/local"
        ) as driver:
            await driver.wait(timeout=5, fail_fast=True)

            await driver.scheme_client.make_directory("/local/my_app")

            listing = await driver.scheme_client.list_directory("/local")
            for entry in listing.children:
                print(entry.name, entry.type)

            entry = await driver.scheme_client.describe_path("/local/my_app")
            print(entry.is_directory())

            await driver.scheme_client.remove_directory("/local/my_app")

    asyncio.run(main())


Common Pattern: Idempotent Directory Setup
------------------------------------------

When initialising an application it is common to create the directory structure
once and tolerate the case where it already exists:

.. code-block:: python

    import ydb

    def setup_schema(driver: ydb.Driver, base_path: str) -> None:
        for subdir in ("tables", "topics", "coordination"):
            path = f"{base_path}/{subdir}"
            try:
                driver.scheme_client.make_directory(path)
            except ydb.SchemeError:
                pass  # already exists

        with ydb.QuerySessionPool(driver) as pool:
            pool.execute_with_retries(
                f"CREATE TABLE IF NOT EXISTS `{base_path}/tables/events` "
                "(id Uint64, payload Utf8, PRIMARY KEY (id))"
            )
