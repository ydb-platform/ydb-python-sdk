OpenTelemetry Tracing
=====================

The SDK provides built-in distributed tracing via `OpenTelemetry <https://opentelemetry.io/>`_.
When enabled, key YDB operations — such as session creation, query execution, transaction
commit/rollback, and driver initialization — produce OpenTelemetry spans. Trace
context is automatically propagated to the YDB server through gRPC metadata using the
`W3C Trace Context <https://www.w3.org/TR/trace-context/>`_ standard.

Tracing is **zero-cost when disabled**: the SDK uses no-op stubs by default, so there is
no overhead unless you explicitly opt in.


Installation
------------

OpenTelemetry packages are not included by default. Install the SDK with the
``opentelemetry`` extra:

.. code-block:: sh

    pip install ydb[opentelemetry]

This pulls in ``opentelemetry-api``. You will also need ``opentelemetry-sdk`` and an
exporter for your tracing backend, for example:

.. code-block:: sh

    # OTLP/gRPC exporter (works with Jaeger, Tempo, and others)
    pip install opentelemetry-exporter-otlp-proto-grpc


Enabling Tracing
----------------

Call ``enable_tracing()`` once, **after** configuring your OpenTelemetry tracer provider
and **before** creating a ``Driver``:

.. code-block:: python

    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource

    import ydb
    from ydb.opentelemetry import enable_tracing

    # 1. Set up OpenTelemetry
    resource = Resource(attributes={"service.name": "my-service"})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint="http://localhost:4317"))
    )
    trace.set_tracer_provider(provider)

    # 2. Enable YDB tracing
    enable_tracing()

    # 3. Use the SDK as usual — spans are created automatically
    with ydb.Driver(endpoint="grpc://localhost:2136", database="/local") as driver:
        driver.wait(timeout=5)
        with ydb.QuerySessionPool(driver) as pool:
            pool.execute_with_retries("SELECT 1")

    provider.shutdown()

``enable_tracing()`` accepts an optional ``tracer`` argument. If omitted, the SDK
obtains a tracer named ``"ydb.sdk"`` from the global tracer provider.


What Is Instrumented
--------------------

The following operations produce spans:

.. list-table::
   :header-rows: 1
   :widths: 35 20 45

   * - Span Name
     - Kind
     - Description
   * - ``ydb.Driver.Initialize``
     - INTERNAL
     - Driver wait / endpoint discovery.
   * - ``ydb.CreateSession``
     - CLIENT
     - Creating a new query session.
   * - ``ydb.ExecuteQuery``
     - CLIENT
     - Executing a query (including ``execute_with_retries``).
   * - ``ydb.Commit``
     - CLIENT
     - Committing an explicit transaction.
   * - ``ydb.Rollback``
     - CLIENT
     - Rolling back a transaction.
   * - ``ydb.RunWithRetry``
     - INTERNAL
     - Umbrella span wrapping the whole retryable block (``retry_operation_*`` / ``retry_tx_*`` / ``execute_with_retries``).
   * - ``ydb.Try``
     - INTERNAL
     - A single retry attempt. Carries ``ydb.retry.backoff_ms`` — how long the retrier slept before starting this attempt (``0`` for the first one).

All spans are nested under the currently active span, so wrapping your application
logic in a parent span produces a complete trace tree:

.. code-block:: python

    tracer = trace.get_tracer(__name__)

    with tracer.start_as_current_span("handle-request"):
        pool.execute_with_retries("SELECT 1")
        # ↳ ydb.CreateSession  (if a new session is needed)
        #   ↳ ydb.ExecuteQuery


Span Attributes
---------------

Every YDB RPC (CLIENT-kind) span carries these semantic attributes:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Attribute
     - Description
   * - ``db.system.name``
     - Always ``"ydb"``.
   * - ``db.namespace``
     - Database path (e.g. ``"/local"``).
   * - ``server.address``
     - Host from the connection string.
   * - ``server.port``
     - Port from the connection string.
   * - ``network.peer.address``
     - Actual node host used for this call (set once the session is attached to a node).
   * - ``network.peer.port``
     - Actual node port used for this call.

Additional attributes are set when available:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Attribute
     - Description
   * - ``ydb.session.id``
     - Session identifier.
   * - ``ydb.node.id``
     - YDB node that handled the request.
   * - ``ydb.tx.id``
     - Transaction identifier.

On errors, the span also records:

- ``error.type`` — ``"ydb_error"``, ``"transport_error"``, or the Python exception class name.
- ``db.response.status_code`` — the YDB status code name (e.g. ``"SCHEME_ERROR"``).


Trace Context Propagation
-------------------------

When tracing is enabled, the SDK automatically injects trace context headers into
every gRPC call to YDB using the globally configured OpenTelemetry propagator
(``opentelemetry.propagate.inject``). By default, OpenTelemetry uses the
`W3C Trace Context <https://www.w3.org/TR/trace-context/>`_ propagator, which adds
``traceparent`` and ``tracestate`` headers.

YDB server expects W3C Trace Context headers, so the default propagator configuration
works out of the box. This allows the server to correlate client spans with
server-side processing, enabling end-to-end trace visibility across the entire
request path.


Async Usage
-----------

Tracing works identically with the async driver. Call ``enable_tracing()`` once at
startup:

.. code-block:: python

    import asyncio
    import ydb
    from ydb.opentelemetry import enable_tracing

    enable_tracing()

    async def main():
        async with ydb.aio.Driver(
            endpoint="grpc://localhost:2136",
            database="/local",
        ) as driver:
            await driver.wait(timeout=5)
            async with ydb.aio.QuerySessionPool(driver) as pool:
                await pool.execute_with_retries("SELECT 1")

    asyncio.run(main())



Using a Custom Tracer
---------------------

To use a specific tracer instead of the global one:

.. code-block:: python

    from opentelemetry import trace

    my_tracer = trace.get_tracer("my.custom.tracer")
    enable_tracing(tracer=my_tracer)


Running the Examples
--------------------

The ``examples/opentelemetry/`` directory contains ready-to-run examples with a Docker
Compose setup that starts YDB, an OTLP collector, Tempo, Prometheus, and Grafana:

.. code-block:: sh

    cd examples/opentelemetry
    docker compose -f compose-e2e.yaml up -d

    # Run the example
    python example.py

Open `http://localhost:3000 <http://localhost:3000>`_ (Grafana) to explore the
collected traces via the Tempo data source.
