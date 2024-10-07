Quick Start
===========

Installation
------------

Prerequisites
^^^^^^^^^^^^^

* Python 3.8 or higher;
* ``pip`` version 9.0.1 or higher;

If necessary, upgrade your version of ``pip``::

    python -m pip install --upgrade pip

If you cannot upgrade `pip` due to a system-owned installation, you can run the example in a virtualenv::

    python -m pip install virtualenv
    virtualenv venv
    source venv/bin/activate
    python -m pip install --upgrade pip

Installation via Pypi
^^^^^^^^^^^^^^^^^^^^^

To install YDB Python SDK through Pypi execute the following command::

    pip install ydb


Installation From Sources
^^^^^^^^^^^^^^^^^^^^^^^^^

To install YDB Python SDK from sources execute the following command from the root of repository::

    pip install -e .


Usage
-----

Import Package
^^^^^^^^^^^^^^

.. code-block:: python

    import ydb

Driver Initialization
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    endpoint = "grpc://localhost:2136"  # your ydb endpoint
    database = "/local"  # your ydb database

    with ydb.Driver(
        endpoint=endpoint,
        database=database,
        credentials=ydb.credentials_from_env_variables(),
    ) as driver:
        driver.wait(timeout=5, fail_fast=True)

SessionPool Initialization
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    with ydb.QuerySessionPool(driver) as pool:
        pass

Query Execution
^^^^^^^^^^^^^^^

Python SDK supports queries described by YQL syntax.
There are two primary methods for executing queries, each with different properties and use cases:

* ``pool.execute_with_retries``:

  * Buffers the entire result set in client memory.
  * Automatically retries execution in case of retriable issues.
  * Does not allow specifying a transaction execution mode.
  * Recommended for one-off queries that are expected to produce small result sets.

* ``tx.execute``:

  * Returns an iterator over the query results, allowing processing of results that may not fit into client memory.
  * Retries must be handled manually via `pool.retry_operation_sync`.
  * Allows specifying a transaction execution mode.
  * Recommended for scenarios where `pool.execute_with_retries` is insufficient.


Usage of ``pool.execute_with_retries()``:

.. code-block:: python

    pool.execute_with_retries("DROP TABLE IF EXISTS example")
    pool.execute_with_retries("CREATE TABLE example(key UInt64, value String, PRIMARY KEY (key))")

    pool.execute_with_retries("INSERT INTO example (key, value) VALUES (1, 'luffy')")

    res = pool.execute_with_retries("SELECT COUNT(*) AS rows_count FROM example")

>>> res[0].rows_count
1

Example of ``tx.execute()``:

.. code-block:: python

    def callee(session: ydb.QuerySessionSync):
        with session.transaction() as tx:
            with tx.execute(
                "INSERT INTO example (key, value) VALUES (2, 'zoro')"
            ):
                pass

            with tx.execute(
                "INSERT INTO example (key, value) VALUES (3, 'sanji')",
                commit_tx=True,
            ):
                pass

    pool.retry_operation_sync(callee)



