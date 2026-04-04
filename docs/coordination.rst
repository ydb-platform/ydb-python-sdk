Coordination Service
====================

.. warning::

   Coordination Service API is experimental and may contain bugs.
   The interface may change in future releases.

The Coordination Service provides distributed primitives for managing shared state
across multiple processes or hosts:

* **Semaphores** — counting semaphores that work as distributed mutexes or
  concurrency limiters. A semaphore with ``limit=1`` acts as an exclusive distributed lock.
* **Sessions** — persistent connections to a coordination node. The server tracks
  session liveness; if a session drops without explicitly releasing a semaphore, the
  server releases it automatically after the grace period expires.

A typical use case is leader election or limiting the number of concurrent workers
across a cluster.


Concepts
--------

**Coordination node** — a named entity in the YDB schema tree (like a table path)
that holds configuration and state for sessions and semaphores attached to it.
Think of it as a namespace for a set of semaphores.

**Session** — a stateful connection to a coordination node. Sessions survive
transient network failures through automatic reconnection. When a session ends
(gracefully or via timeout), all semaphores it holds are released automatically.

**Semaphore** — a server-side counter with a configurable ``limit``. A call to
``acquire(count=N)`` blocks until ``N`` units are available. ``acquire()`` with
the default ``count=1`` against a ``limit=1`` semaphore behaves as a mutex.


Node Management
---------------

Create a Node
^^^^^^^^^^^^^

A coordination node must exist before sessions can attach to it.

.. code-block:: python

    # Minimal creation — default config
    driver.coordination_client.create_node("/local/my_node")

Create a node with explicit configuration:

.. code-block:: python

    import ydb.coordination

    config = ydb.coordination.NodeConfig(
        attach_consistency_mode=ydb.coordination.ConsistencyMode.STRICT,
        read_consistency_mode=ydb.coordination.ConsistencyMode.STRICT,
        rate_limiter_counters_mode=ydb.coordination.RateLimiterCountersMode.AGGREGATED,
        self_check_period_millis=1000,
        session_grace_period_millis=10000,
    )
    driver.coordination_client.create_node("/local/my_node", config)

:class:`~ydb.coordination.NodeConfig` parameters:

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Parameter
     - Description
   * - ``attach_consistency_mode``
     - :class:`~ydb.coordination.ConsistencyMode` for session attach operations.
       ``STRICT`` — strong consistency; ``RELAXED`` — may read slightly stale state
       but lower latency.
   * - ``read_consistency_mode``
     - :class:`~ydb.coordination.ConsistencyMode` for semaphore describe/watch operations.
   * - ``rate_limiter_counters_mode``
     - :class:`~ydb.coordination.RateLimiterCountersMode` for metrics collection:
       ``AGGREGATED`` (single counter per semaphore) or ``DETAILED`` (per-owner breakdown).
   * - ``self_check_period_millis``
     - How often (ms) the server checks its own liveness. Lower values detect
       failures faster but increase server load.
   * - ``session_grace_period_millis``
     - How long (ms) the server keeps a session alive after losing contact with the
       client before forcibly releasing all its semaphores.


Describe and Alter a Node
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    # Read current config
    config = driver.coordination_client.describe_node("/local/my_node")
    print(config.attach_consistency_mode)
    print(config.session_grace_period_millis)

    # Change config
    new_config = NodeConfig(
        attach_consistency_mode=ConsistencyMode.RELAXED,
        read_consistency_mode=ConsistencyMode.RELAXED,
        rate_limiter_counters_mode=RateLimiterCountersMode.DETAILED,
        self_check_period_millis=2000,
        session_grace_period_millis=15000,
    )
    driver.coordination_client.alter_node("/local/my_node", new_config)


Delete a Node
^^^^^^^^^^^^^

.. code-block:: python

    driver.coordination_client.delete_node("/local/my_node")


Sessions
--------

A session binds a client to a coordination node. All semaphore operations go through
a session. Sessions reconnect automatically after transient network errors.

.. code-block:: python

    # Use as context manager — session is closed on exit
    with driver.coordination_client.session("/local/my_node") as session:
        # ... work with semaphores
        pass

    # Or manage lifecycle manually
    session = driver.coordination_client.session("/local/my_node")
    try:
        # ... work with semaphores
        pass
    finally:
        session.close()

If the process crashes or the network drops, the server waits
``session_grace_period_millis`` before releasing the session's semaphores. This window
gives the client time to reconnect and reclaim ownership.


Semaphores
----------

Basic Usage (Mutex Pattern)
^^^^^^^^^^^^^^^^^^^^^^^^^^^

A semaphore with ``limit=1`` acts as an exclusive distributed lock:

.. code-block:: python

    with driver.coordination_client.session("/local/my_node") as session:
        # Acquire returns when no other holder exists (blocks otherwise)
        semaphore = session.semaphore("my_lock")
        semaphore.acquire()
        try:
            # critical section
            do_work()
        finally:
            semaphore.release()

The context manager form is more concise:

.. code-block:: python

    with driver.coordination_client.session("/local/my_node") as session:
        with session.semaphore("my_lock"):
            do_work()   # lock is held for the duration of the block

Counting Semaphore
^^^^^^^^^^^^^^^^^^

Set ``limit > 1`` to allow multiple concurrent holders — useful for limiting
the number of parallel workers:

.. code-block:: python

    with driver.coordination_client.session("/local/my_node") as session:
        # Allow up to 3 concurrent holders
        semaphore = session.semaphore("worker_slots", limit=3)
        semaphore.acquire()   # acquire 1 slot (default count=1)
        try:
            do_work()
        finally:
            semaphore.release()

    # Acquire multiple slots at once
    semaphore.acquire(count=2)   # hold 2 of the 3 slots

Inspecting a Semaphore
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    with driver.coordination_client.session("/local/my_node") as session:
        semaphore = session.semaphore("my_lock")
        info = semaphore.describe()

        print("limit:   ", info.limit)    # max count
        print("count:   ", info.count)    # currently acquired count
        print("owners:  ", info.owners)   # list of current holders
        print("waiters: ", info.waiters)  # list of processes waiting to acquire

Attaching Metadata
^^^^^^^^^^^^^^^^^^

Each semaphore can hold an opaque ``bytes`` payload. This is useful for the leader
to publish its address or other metadata so that followers can discover it:

.. code-block:: python

    with driver.coordination_client.session("/local/my_node") as session:
        semaphore = session.semaphore("leader_lock")
        semaphore.acquire()
        # Publish this process's address as leader metadata
        semaphore.update(b"host=worker-1.internal:8080")


Async Usage
-----------

The async client mirrors the synchronous API with ``async with`` and ``await``:

.. code-block:: python

    import asyncio
    import ydb

    async def main():
        async with ydb.aio.Driver(
            endpoint="grpc://localhost:2136",
            database="/local",
        ) as driver:
            await driver.wait(timeout=5, fail_fast=True)

            await driver.coordination_client.create_node("/local/my_node")

            async with driver.coordination_client.session("/local/my_node") as session:
                async with session.semaphore("my_lock"):
                    await do_async_work()

    asyncio.run(main())

Async is well suited for running multiple independent workers concurrently:

.. code-block:: python

    async def worker(client, worker_id: int):
        async with client.session("/local/my_node") as session:
            for i in range(5):
                async with session.semaphore("shared_resource"):
                    print(f"worker {worker_id}: step {i}")
                    await asyncio.sleep(0.1)

    async def main():
        async with ydb.aio.Driver(...) as driver:
            await driver.wait(timeout=5, fail_fast=True)
            await driver.coordination_client.create_node("/local/my_node")
            await asyncio.gather(*(worker(driver.coordination_client, i) for i in range(4)))


Multi-threaded Sync Usage
--------------------------

The synchronous client is thread-safe. Multiple threads can share the same
``coordination_client`` and create independent sessions:

.. code-block:: python

    import threading
    import ydb

    def worker(client, worker_id: int):
        with client.session("/local/my_node") as session:
            for i in range(5):
                with session.semaphore("shared_resource"):
                    print(f"worker {worker_id}: step {i}")

    with ydb.Driver(endpoint="grpc://localhost:2136", database="/local") as driver:
        driver.wait(timeout=5, fail_fast=True)
        driver.coordination_client.create_node("/local/my_node")

        threads = [
            threading.Thread(target=worker, args=(driver.coordination_client, i))
            for i in range(4)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()


Leader Election Pattern
-----------------------

A common use case is electing a leader among a set of replicas. The replica that
acquires the semaphore becomes the leader; others block in ``acquire()`` and take
over if the leader's session expires:

.. code-block:: python

    import socket
    import ydb

    def run_replica(driver: ydb.Driver):
        my_address = socket.gethostname()

        with driver.coordination_client.session("/local/election") as session:
            semaphore = session.semaphore("leader", limit=1)

            while True:
                semaphore.acquire()          # blocks until we become leader
                semaphore.update(my_address.encode())   # publish our address

                print(f"{my_address}: I am the leader")
                try:
                    serve_as_leader()        # run until an error or shutdown
                except Exception:
                    pass
                finally:
                    semaphore.release()      # step down voluntarily
