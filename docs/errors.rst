Errors and Retries
==================

The SDK maps every YDB server status code to a Python exception class. All exceptions
inherit from :class:`~ydb.Error`, so you can catch the whole hierarchy with a single
``except ydb.Error`` clause, or handle individual error types precisely.


Exception Hierarchy
-------------------

.. code-block:: text

    ydb.Error
    ├── ydb.BadRequest          — malformed query or invalid argument
    ├── ydb.Unauthorized        — authentication succeeded but operation not permitted
    ├── ydb.Unauthenticated     — authentication failed
    ├── ydb.InternalError       — server-side internal error (usually transient)
    ├── ydb.Aborted             — transaction aborted due to a conflict; safe to retry
    ├── ydb.Unavailable         — service temporarily unavailable; safe to retry
    ├── ydb.Overloaded          — server is overloaded; retry with backoff
    ├── ydb.SchemeError         — schema-related error (e.g. table not found, already exists)
    ├── ydb.GenericError        — unclassified server error
    ├── ydb.Timeout             — server-side deadline exceeded
    ├── ydb.BadSession          — session is invalid or expired; create a new one
    ├── ydb.PreconditionFailed  — operation precondition not met
    ├── ydb.AlreadyExists       — object already exists (DDL)
    ├── ydb.NotFound            — object not found
    ├── ydb.SessionExpired      — session TTL expired
    ├── ydb.Cancelled           — operation was cancelled
    ├── ydb.Undetermined        — outcome is unknown (e.g. network lost before ack)
    ├── ydb.Unsupported         — operation not supported by this server version
    ├── ydb.SessionBusy         — session is executing another request
    ├── ydb.ExternalError       — error in an external data source
    ├── ydb.TruncatedResponseError — result set was truncated by the server
    ├── ydb.SessionPoolEmpty    — all sessions are busy; pool exhausted
    ├── ydb.SessionPoolClosed   — session pool has been stopped
    ├── ydb.ConnectionError     — base class for transport-level errors
    │   ├── ydb.ConnectionFailure  — could not establish connection
    │   ├── ydb.ConnectionLost     — connection dropped mid-request
    │   └── ydb.Unimplemented      — server does not support this RPC
    └── ydb.DeadlineExceed      — client-side deadline exceeded


Catching Errors
---------------

.. code-block:: python

    import ydb

    try:
        pool.execute_with_retries("SELECT * FROM users")
    except ydb.SchemeError:
        print("table does not exist")
    except ydb.Unauthorized:
        print("access denied")
    except ydb.Unavailable:
        print("service temporarily unavailable")
    except ydb.Error as e:
        print(f"other YDB error: {e}")

Each exception exposes:

* ``str(e)`` — human-readable message from the server.
* ``e.issues`` — list of structured ``IssueMessage`` objects with ``message``,
  ``issue_code``, and ``severity``.
* ``e.status`` — the ``ydb.StatusCode`` enum value.

.. code-block:: python

    try:
        pool.execute_with_retries("BAD QUERY")
    except ydb.Error as e:
        print(e.status)    # e.g. StatusCode.BAD_REQUEST
        print(e.message)
        if e.issues:
            for issue in e.issues:
                print(issue.message, issue.severity)


Retriable vs Non-Retriable Errors
----------------------------------

Not every error is worth retrying. The SDK classifies errors into three groups:

**Always retriable (fast backoff):**

* :class:`~ydb.Unavailable` — service is temporarily unavailable.
* ``ClientInternalError`` — internal SDK error.
* ``SessionExpired`` — session TTL passed; the SDK opens a new one.
* :class:`~ydb.NotFound` — by default retried (configurable via ``retry_not_found``).
* ``Cancelled`` — only when ``retry_cancelled=True`` is set.

**Retriable with slow backoff:**

* :class:`~ydb.Aborted` — transaction conflict; the whole transaction must be replayed.
* :class:`~ydb.BadSession` — session is invalid; the SDK acquires a new one.
* :class:`~ydb.Overloaded` — server under heavy load; back off and try again.
* :class:`~ydb.SessionPoolEmpty` — all pool sessions busy; wait and retry.
* :class:`~ydb.ConnectionError` / :class:`~ydb.ConnectionLost` — network issues; reconnect and retry.

**Retriable only for idempotent operations (slow backoff):**

* :class:`~ydb.Undetermined` — outcome unknown; only safe to retry if the operation is idempotent
  (i.e. repeating it has the same effect as running it once). Set ``idempotent=True``
  in :class:`~ydb.RetrySettings` to enable.

**Never retried:**

* :class:`~ydb.BadRequest`, :class:`~ydb.Unauthorized`, ``Unauthenticated``,
  :class:`~ydb.SchemeError`, :class:`~ydb.AlreadyExists`, ``Unsupported``,
  :class:`~ydb.Timeout`, ``PreconditionFailed``, ``ExternalError`` — these indicate
  a problem with the query, credentials, or schema that won't resolve by retrying.


RetrySettings
-------------

All pool methods that perform retries (``execute_with_retries``, ``retry_operation_sync``,
``retry_tx_sync``) accept an optional :class:`~ydb.RetrySettings` object:

.. code-block:: python

    import ydb

    retry = ydb.RetrySettings(
        max_retries=5,               # max retry attempts (default: 10)
        idempotent=False,            # set True to also retry Undetermined errors
        retry_cancelled=False,       # set True to retry Cancelled errors
    )

    pool.execute_with_retries("SELECT 1", retry_settings=retry)


BackoffSettings
^^^^^^^^^^^^^^^

:class:`~ydb.RetrySettings` uses two separate backoff curves:

* **fast backoff** — used for errors expected to clear quickly (:class:`~ydb.Unavailable`,
  ``SessionExpired``, etc.).
* **slow backoff** — used for errors where the server needs more breathing room
  (:class:`~ydb.Overloaded`, :class:`~ydb.Aborted`, connection failures, etc.).

Both are instances of :class:`~ydb.BackoffSettings`:

.. code-block:: python

    fast = ydb.BackoffSettings(
        ceiling=10,           # exponent cap: max wait slot = 2^ceiling * slot_duration
        slot_duration=0.005,  # base time unit in seconds (default: 5 ms)
        uncertain_ratio=0.5,  # fraction of the window that is randomised (jitter)
    )

    slow = ydb.BackoffSettings(
        ceiling=6,
        slot_duration=1.0,    # 1 second base (default)
        uncertain_ratio=0.5,
    )

    retry = ydb.RetrySettings(
        max_retries=10,
        fast_backoff_settings=fast,
        slow_backoff_settings=slow,
    )

The actual sleep duration for retry ``n`` is:

.. code-block:: text

    slots  = 2 ^ min(n, ceiling)
    max_ms = slots * slot_duration * 1000
    sleep  = max_ms * (random() * uncertain_ratio + (1 - uncertain_ratio)) / 1000


Error Callback
^^^^^^^^^^^^^^

To log or instrument every retry attempt, pass ``on_ydb_error_callback``:

.. code-block:: python

    import logging

    logger = logging.getLogger(__name__)

    def log_retry(err: ydb.Error):
        logger.warning("YDB error, will retry: %s", err)

    retry = ydb.RetrySettings(
        max_retries=10,
        on_ydb_error_callback=log_retry,
    )

    pool.execute_with_retries("SELECT 1", retry_settings=retry)


``@ydb_retry`` Decorator
------------------------

For functions that run outside a session pool, use the ``@ydb.ydb_retry`` decorator.
It wraps both synchronous and asynchronous functions:

.. code-block:: python

    import ydb

    @ydb.ydb_retry(max_retries=5, idempotent=True)
    def fetch_user(driver: ydb.Driver, user_id: int):
        with ydb.QuerySessionPool(driver) as pool:
            result = pool.execute_with_retries(
                "SELECT name FROM users WHERE id = $id",
                parameters={"$id": user_id},
            )
            return result[0].rows[0]["name"]

    # Async version — the decorator detects coroutines automatically:
    @ydb.ydb_retry(max_retries=5, idempotent=True)
    async def fetch_user_async(driver: ydb.aio.Driver, user_id: int):
        async with ydb.aio.QuerySessionPool(driver) as pool:
            result = await pool.execute_with_retries(
                "SELECT name FROM users WHERE id = $id",
                parameters={"$id": user_id},
            )
            return result[0].rows[0]["name"]

.. note::

   The decorator retries the **entire function** on failure, not just the individual
   query. Only use ``idempotent=True`` when repeating the full function body is safe.


Handling ``Undetermined``
--------------------------

:class:`~ydb.Undetermined` means the network was lost before the server could confirm whether
the operation succeeded or failed. The server may have applied the write — or not.

For **read-only** queries this is always safe to retry. For **writes**, only retry if
you can tolerate duplicates or the query is naturally idempotent (e.g. ``UPSERT``):

.. code-block:: python

    retry = ydb.RetrySettings(
        max_retries=10,
        idempotent=True,  # enables retry on Undetermined
    )

    # Safe: UPSERT is idempotent
    pool.execute_with_retries(
        "UPSERT INTO events (id, data) VALUES (42, 'payload')",
        retry_settings=retry,
    )

    # Unsafe: INSERT will fail with AlreadyExists on the second attempt —
    # but that error is not retriable, so at worst you get an exception.
    pool.execute_with_retries(
        "INSERT INTO events (id, data) VALUES (42, 'payload')",
        retry_settings=retry,
    )


Common Patterns
---------------

Fail fast on connection errors during startup:

.. code-block:: python

    try:
        driver.wait(timeout=5, fail_fast=True)
    except TimeoutError:
        raise SystemExit("Could not reach YDB — check endpoint and credentials")

Distinguish schema errors (fix the code) from transient errors (retry):

.. code-block:: python

    try:
        pool.execute_with_retries("SELECT * FROM nonexistent_table")
    except ydb.SchemeError as e:
        raise RuntimeError(f"Schema problem: {e}") from e
    except ydb.Error:
        pass  # handled by retry logic inside execute_with_retries
