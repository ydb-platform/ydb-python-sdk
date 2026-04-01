Driver
======

The driver is the entry point for all YDB operations. It manages endpoint discovery,
connection pooling, and load balancing. All service clients (query, topic, table) are
obtained through the driver.


DriverConfig
------------

``DriverConfig`` holds all settings needed to initialize a driver. Pass it to the
``Driver`` constructor, or use shorthand keyword arguments directly on the ``Driver``.

**Constructor parameters:**

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Parameter
     - Default
     - Description
   * - ``endpoint``
     - *required*
     - gRPC endpoint: ``grpc://host:port`` (plain) or ``grpcs://host:port`` (TLS).
   * - ``database``
     - ``None``
     - Full database path, e.g. ``/local`` or ``/ru-central1/b1g.../etn...``.
   * - ``credentials``
     - ``None``
     - Credentials instance. Falls back to :class:`~ydb.AnonymousCredentials` if ``None``.
   * - ``root_certificates``
     - ``None``
     - PEM-encoded CA certificate(s) as ``bytes`` for TLS verification.
   * - ``certificate_chain``
     - ``None``
     - PEM-encoded client certificate chain as ``bytes`` (mutual TLS).
   * - ``private_key``
     - ``None``
     - PEM-encoded client private key as ``bytes`` (mutual TLS).
   * - ``grpc_keep_alive_timeout``
     - ``None``
     - gRPC KeepAlive timeout in milliseconds.
   * - ``disable_discovery``
     - ``False``
     - If ``True``, skip endpoint discovery and use only the initial endpoint.
   * - ``discovery_request_timeout``
     - ``10``
     - Timeout in seconds for each discovery request.
   * - ``table_client_settings``
     - ``None``
     - :class:`~ydb.TableClientSettings` instance to configure the Table service client.
   * - ``topic_client_settings``
     - ``None``
     - :class:`~ydb.TopicClientSettings` instance to configure the Topic service client.
   * - ``query_client_settings``
     - ``None``
     - :class:`~ydb.QueryClientSettings` instance to configure the Query service client.
   * - ``compression``
     - ``None``
     - gRPC-level compression (e.g. ``grpc.Compression.Gzip``).


Creating a Driver
-----------------

There are three equivalent ways to specify the connection target:

**Using a DriverConfig object:**

.. code-block:: python

    import ydb

    config = ydb.DriverConfig(
        endpoint="grpc://localhost:2136",
        database="/local",
        credentials=ydb.credentials_from_env_variables(),
    )
    driver = ydb.Driver(config)

**Using keyword arguments directly on Driver:**

.. code-block:: python

    driver = ydb.Driver(
        endpoint="grpc://localhost:2136",
        database="/local",
        credentials=ydb.credentials_from_env_variables(),
    )

**Using a connection string:**

.. code-block:: python

    driver = ydb.Driver(
        connection_string="grpc://localhost:2136/?database=/local",
    )

The connection string format is ``<protocol>://<host>:<port>/?database=<path>``.


Waiting for the Driver to Connect
----------------------------------

After construction the driver starts endpoint discovery in the background.
Call ``wait()`` before issuing any requests:

.. code-block:: python

    try:
        driver.wait(timeout=5, fail_fast=True)
    except TimeoutError:
        raise RuntimeError("Could not connect to YDB")

* ``timeout`` — how long to wait in seconds.
* ``fail_fast=True`` — raise immediately if discovery fails instead of retrying until timeout.


Closing the Driver
------------------

Always close the driver when done to release gRPC connections:

.. code-block:: python

    driver.stop()

Using the driver as a context manager is the recommended pattern — ``stop()`` is called
automatically on exit:

.. code-block:: python

    with ydb.Driver(endpoint="grpc://localhost:2136", database="/local") as driver:
        driver.wait(timeout=5, fail_fast=True)
        # ... use driver


Async Driver
------------

``ydb.aio.Driver`` mirrors the synchronous ``Driver`` with async methods:

.. code-block:: python

    import asyncio
    import ydb

    async def main():
        async with ydb.aio.Driver(
            endpoint="grpc://localhost:2136",
            database="/local",
            credentials=ydb.credentials_from_env_variables(),
        ) as driver:
            await driver.wait(timeout=5, fail_fast=True)
            # ... use driver

    asyncio.run(main())


Credentials
-----------

AnonymousCredentials
^^^^^^^^^^^^^^^^^^^^

No authentication. Use for local or unauthenticated deployments
(`full example <https://github.com/ydb-platform/ydb-python-sdk/tree/main/examples/anonymous-credentials>`_):

.. code-block:: python

    credentials = ydb.AnonymousCredentials()

AccessTokenCredentials
^^^^^^^^^^^^^^^^^^^^^^

Pass a static IAM token or API key directly
(`full example <https://github.com/ydb-platform/ydb-python-sdk/tree/main/examples/access-token-credentials>`_):

.. code-block:: python

    credentials = ydb.AccessTokenCredentials("your-token")

StaticCredentials (username/password)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

(`full example <https://github.com/ydb-platform/ydb-python-sdk/tree/main/examples/static-credentials>`_)

.. code-block:: python

    credentials = ydb.StaticCredentials.from_user_password("user", "password")

Service Account Credentials
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Authenticate as a Yandex Cloud service account using a key file. Requires the ``ydb[yc]``
extra (``pip install ydb[yc]``)
(`full example <https://github.com/ydb-platform/ydb-python-sdk/tree/main/examples/service-account-credentials>`_):

.. code-block:: python

    import os
    import ydb.iam

    credentials = ydb.iam.ServiceAccountCredentials.from_file(
        os.getenv("SA_KEY_FILE"),
    )

Metadata Credentials
^^^^^^^^^^^^^^^^^^^^^

Picks up credentials from the instance metadata service when running inside Yandex Cloud
(Compute VM, Cloud Functions, etc.). Requires ``ydb[yc]``
(`full example <https://github.com/ydb-platform/ydb-python-sdk/tree/main/examples/metadata-credentials>`_):

.. code-block:: python

    import ydb.iam

    credentials = ydb.iam.MetadataUrlCredentials()

OAuth 2.0 Token Exchange
^^^^^^^^^^^^^^^^^^^^^^^^^

For federated identity scenarios. Exchanges a subject token (e.g. a signed JWT) for a
YDB access token via an OAuth 2.0 token exchange endpoint
(`full example <https://github.com/ydb-platform/ydb-python-sdk/tree/main/examples/oauth2-token-exchange-credentials>`_):

.. code-block:: python

    import ydb.oauth2_token_exchange

    credentials = ydb.oauth2_token_exchange.Oauth2TokenExchangeCredentials(
        token_endpoint="https://auth.example.com/oauth/token",
        audience="ydb",
        subject_token_source=ydb.oauth2_token_exchange.JwtTokenSource(
            signing_method="RS256",
            private_key_file="/path/to/private.pem",
            key_id="my-key-id",
            issuer="my-issuer",
            subject="my-subject",
            audience="ydb",
        ),
    )

Credentials from environment variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The recommended option for cloud deployments — the SDK auto-selects the appropriate
provider based on which environment variable is set:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Environment variable
     - Credentials type selected
   * - ``YDB_ACCESS_TOKEN_CREDENTIALS``
     - ``AccessTokenCredentials``
   * - ``YDB_ANONYMOUS_CREDENTIALS``
     - ``AnonymousCredentials``
   * - ``YDB_METADATA_CREDENTIALS``
     - ``MetadataUrlCredentials``
   * - ``YDB_SERVICE_ACCOUNT_KEY_FILE_CREDENTIALS``
     - ``ServiceAccountCredentials``

.. code-block:: python

    credentials = ydb.credentials_from_env_variables()

.. note::

   ``ServiceAccountCredentials`` and ``MetadataUrlCredentials`` require the ``ydb[yc]``
   extra:

   .. code-block:: sh

       pip install ydb[yc]

TLS / Secure Connections
-------------------------

For TLS endpoints (``grpcs://``), the SDK uses the system CA bundle by default.
To supply a custom CA certificate:

.. code-block:: python

    with open("ca.pem", "rb") as f:
        ca_cert = f.read()

    driver = ydb.Driver(
        endpoint="grpcs://ydb.example.com:2135",
        database="/production/mydb",
        credentials=ydb.credentials_from_env_variables(),
        root_certificates=ca_cert,
    )

For mutual TLS (client certificate authentication):

.. code-block:: python

    driver = ydb.Driver(
        endpoint="grpcs://ydb.example.com:2135",
        database="/production/mydb",
        root_certificates=ca_cert,
        certificate_chain=client_cert_pem,
        private_key=client_key_pem,
    )


Service Clients
---------------

Once the driver is ready, access service clients via its properties:

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Attribute
     - Type
     - Purpose
   * - ``driver.table_client``
     - :class:`~ydb.TableClient`
     - Schema management, bulk upsert, streaming reads. See :doc:`table`.
   * - ``driver.topic_client``
     - :class:`~ydb.TopicClient`
     - Topic writers, readers, topic management. See :doc:`topic`.
   * - ``driver.scheme_client``
     - :class:`~ydb.SchemeClient`
     - Directory and path operations. See :doc:`scheme`.

:class:`~ydb.QuerySessionPool` is constructed explicitly from the driver, not
accessed as a property:

.. code-block:: python

    with ydb.Driver(endpoint=..., database=...) as driver:
        driver.wait(timeout=5, fail_fast=True)

        with ydb.QuerySessionPool(driver) as pool:   # Query service
            pass

        topics = driver.topic_client    # Topic service
        scheme = driver.scheme_client   # Schema operations
        table  = driver.table_client    # Table service
