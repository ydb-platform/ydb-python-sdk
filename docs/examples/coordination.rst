Coordination Service
===================

.. warning::
   Coordination Service API is experimental and may change in future releases.

All examples in this section are parts of `coordination example <https://github.com/ydb-platform/ydb-python-sdk/tree/main/examples/coordination>`_.


Create node
-----------

.. code-block:: python

    driver.coordination_client.create_node("/local/my_node")

Create node with config
-----------------------

.. code-block:: python

    from ydb import NodeConfig, ConsistencyMode, RateLimiterCountersMode

    config = NodeConfig(
        attach_consistency_mode=ConsistencyMode.STRICT,
        read_consistency_mode=ConsistencyMode.STRICT,
        rate_limiter_counters_mode=RateLimiterCountersMode.AGGREGATED,
        self_check_period_millis=1000,
        session_grace_period_millis=10000
    )

    driver.coordination_client.create_node("/local/my_node", config)

Describe node
-------------

.. code-block:: python

    config = driver.coordination_client.describe_node("/local/my_node")

Alter node
----------

.. code-block:: python

    new_config = NodeConfig(
        attach_consistency_mode=ConsistencyMode.RELAXED,
        read_consistency_mode=ConsistencyMode.RELAXED,
        rate_limiter_counters_mode=RateLimiterCountersMode.DETAILED,
        self_check_period_millis=2000,
        session_grace_period_millis=15000
    )
    driver.coordination_client.alter_node("/local/my_node", new_config)

Delete node
-----------

.. code-block:: python

    driver.coordination_client.delete_node("/local/my_node")

Create session
--------------

.. code-block:: python

    with driver.coordination_client.session("/local/my_node") as session:
        pass

Use semaphore manually
----------------------

.. code-block:: python

    with driver.coordination_client.session("/local/my_node") as session:
        semaphore = session.semaphore("my_semaphore", limit=2)  # limit is optional, default is 1
        semaphore.acquire(count=2) # count is optional, default is 1
        try:
            pass
        finally:
            semaphore.release()

Use semaphore with context manager
----------------------------------

.. code-block:: python

    with driver.coordination_client.session("/local/my_node") as session:
        with session.semaphore("my_semaphore"):
            pass

Async usage
-----------

.. code-block:: python

    async with driver.coordination_client.session("/local/my_node") as session:
        async with session.semaphore("my_semaphore"):
            pass
