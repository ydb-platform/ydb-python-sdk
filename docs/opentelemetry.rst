OpenTelemetry
=============

`OpenTelemetry <https://opentelemetry.io/>`_ is the built-in backend for the SDK's
vendor-neutral observability interface (see :doc:`observability`). Enabling tracing turns
key YDB operations — session creation, query execution, transaction commit/rollback,
driver initialization, and retries — into OpenTelemetry spans, and propagates trace
context to the YDB server through gRPC metadata using the
`W3C Trace Context <https://www.w3.org/TR/trace-context/>`_ standard. Enabling metrics
records client-side OpenTelemetry instruments for the same operations, retries, and
query session pools, as well as receive, delivery, and buffer metrics for explicitly
named topic Readers.

Like every backend, it has a **zero-cost no-op path when disabled**: operations, query
sessions, pools, and topic Readers share no-op instrumentation without metric
allocations, timers, locks, or state tracking. The SDK does not import
``opentelemetry`` until you call ``enable_tracing()`` or ``enable_metrics()``.


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

Repeated calls to ``enable_tracing()`` replace the previously installed provider, so
it is safe to reconfigure at any time. Call ``disable_tracing()`` to remove the hooks
entirely and return the SDK to its no-op default.

Advanced users can build the provider explicitly and install it through the
vendor-neutral entrypoint — this is exactly what the convenience wrapper above does:

.. code-block:: python

    from ydb.observability import enable_tracing
    from ydb.opentelemetry import OtelTracingProvider

    enable_tracing(OtelTracingProvider())          # or OtelTracingProvider(my_tracer)


Enabling Metrics
----------------

Metrics are independent from tracing — enable either or both. Configure your
OpenTelemetry meter provider, then call ``enable_metrics()`` before creating query
sessions or a ``QuerySessionPool`` whose lifecycle should be instrumented:

.. code-block:: python

    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource

    import ydb
    from ydb.opentelemetry import enable_metrics

    # 1. Set up OpenTelemetry
    resource = Resource(attributes={"service.name": "my-service"})
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint="http://localhost:4317"),
        export_interval_millis=1000,
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])

    # 2. Enable YDB metrics
    enable_metrics(meter_provider)

    # 3. Use the SDK as usual — metrics are recorded automatically
    with ydb.Driver(endpoint="grpc://localhost:2136", database="/local") as driver:
        driver.wait(timeout=5)
        with ydb.QuerySessionPool(driver, name="main-pool") as pool:
            pool.execute_with_retries("SELECT 1")

    meter_provider.shutdown()

``enable_metrics()`` accepts an optional ``meter_provider`` argument. If omitted, the SDK
obtains a meter named ``"ydb.sdk"`` from the global meter provider. The call is
idempotent: repeated ``enable_metrics()`` calls do nothing until you call
``disable_metrics()``. Disabling deactivates the old observable callbacks and restores
the no-op event provider. Operation and retry metrics follow the active provider
immediately. Pools created while metrics were active retain their state, so enabling
metrics again — including with another meter provider — starts from their current
snapshot. Pools created while metrics were disabled retain no-op lifecycle
instrumentation.

The full list of instruments and their attributes is catalogued on the
:doc:`observability` page.


.. _opentelemetry-topic-reader-metrics:

Topic Reader Metrics
--------------------

Enable metrics before creating the Reader and pass an explicit, non-empty
``reader_name``. The name identifies one logical Reader and remains the same when its
underlying stream reconnects:

.. code-block:: python

    import asyncio
    import uuid

    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import (
        ConsoleMetricExporter,
        PeriodicExportingMetricReader,
    )

    import ydb
    from ydb.opentelemetry import enable_metrics

    metric_reader = PeriodicExportingMetricReader(
        ConsoleMetricExporter(),
        export_interval_millis=1000,
    )
    meter_provider = MeterProvider(metric_readers=[metric_reader])
    enable_metrics(meter_provider)


    async def read_one_message():
        topic_path = f"/local/otel-reader-metrics-example-{uuid.uuid4().hex}"
        consumer = "orders-consumer"

        async with ydb.aio.Driver(
            endpoint="grpc://localhost:2136",
            database="/local",
        ) as driver:
            await driver.wait(timeout=5)

            await driver.topic_client.create_topic(topic_path, consumers=[consumer])
            try:
                async with driver.topic_client.writer(topic_path, codec=ydb.TopicCodec.GZIP) as writer:
                    await writer.write("OpenTelemetry topic Reader metrics")

                async with driver.topic_client.reader(
                    topic_path,
                    consumer=consumer,
                    reader_name="payments-worker",
                ) as reader:
                    await asyncio.wait_for(reader.wait_message(), timeout=10)
                    await asyncio.sleep(2)
                    message = await asyncio.wait_for(reader.receive_message(), timeout=10)
                    await reader.commit_with_ack(message)
                    await asyncio.sleep(2)
            finally:
                await driver.topic_client.drop_topic(topic_path)


    try:
        asyncio.run(read_one_message())
    finally:
        meter_provider.shutdown()

This registers six cumulative counters, two histograms, and five observable instruments:

* ``ydb.topic.reader.received.messages`` counts received messages before decoding. It
  includes ``endpoint``, ``database``, ``reader.name``, optional ``consumer``, and
  ``topic`` attributes.
* ``ydb.topic.reader.received.bytes`` adds ``ReadResponse.bytes_size`` once for every
  response received by the logical Reader. It has the same Reader attributes but no
  ``topic``, because one response may contain batches from several topics.
* ``ydb.topic.reader.delivered.messages`` counts messages returned to the application
  by ``receive_message``, ``receive_batch``, or ``receive_batch_with_tx``. It carries
  the Reader attributes and ``topic``.
* ``ydb.topic.reader.compression.duration`` records time spent inside the decoder for
  each non-RAW message, excluding decoder-executor queueing. It uses seconds and carries
  ``topic``, ``codec``, ``outcome``, and ``error.type`` on failures.
* ``ydb.topic.reader.message.processing.duration`` records time from receipt until each
  non-RAW message's batch is ready for delivery. It includes decoder queueing and uses
  the same attributes as the compression histogram.
* ``ydb.topic.reader.commit.queued`` counts messages in commit ranges accepted by the
  SDK, using ``range.end - range.start``. It carries the Reader attributes and ``topic``.
* ``ydb.topic.reader.commit.acknowledged`` counts monotonic committed-offset advances
  reported by regular acknowledgements. Successful transaction commits count their
  submitted ranges; duplicate or stale regular acknowledgements and failed transactions
  add nothing. It carries the Reader attributes and ``topic``.
* ``ydb.topic.reader.commit_offset.lag.max`` reports the maximum gap between the highest
  requested commit end offset and the acknowledged offset across active partitions of
  each ``topic``. It tracks regular stream commits; transactional ranges remain visible
  in the commit counters but do not contribute to this gauge. Stale acknowledgements
  cannot increase it.
* ``ydb.topic.reader.session.errors`` counts failed sessions or connection attempts.
  The ``retry_decision`` attribute is ``retry`` when the Reader will reconnect and
  ``stop`` when it terminates. ``status_code`` identifies the YDB status or exception
  class, while ``error.type`` classifies transport, YDB, and other failures. Normal
  Reader shutdown is not counted. This Reader-level metric has no ``topic`` attribute.
* ``ydb.topic.reader.credit_balance_bytes`` reports the protocol byte credit granted to
  the server and not yet consumed by read responses. It is ``0`` between stream
  sessions, uses unit ``By``, and has the Reader attributes but no ``topic``.
* ``ydb.topic.reader.local_buffer.messages`` reports the current number of messages
  retained by the logical Reader, including messages waiting for decoding and decoded
  messages waiting for the application. It has the Reader attributes but no ``topic``.
* ``ydb.topic.reader.local_buffer.message_age.max`` reports, in seconds, the age of the
  oldest retained message. It uses a monotonic clock, becomes ``0`` when the buffer is
  empty, and has the Reader attributes but no ``topic``.
* ``ydb.topic.reader.partition_session.count`` reports active partition sessions per
  ``topic``. Configured topics report ``0`` before the first session starts. The metric
  has the Reader attributes and ``topic``, but deliberately has no ``partition``
  attribute.

If ``reader_name`` is omitted or empty, the Reader still works and receives its normal
process-local diagnostic name, but these thirteen metrics are not published. The runnable
``examples/opentelemetry/otel_example.py`` creates a topic, writes one message, reads it
with an explicitly named Reader, and exports its Reader metrics through OTLP.


Instrumented Spans and Attributes
---------------------------------

The set of spans and the standard attributes attached to them are the same for every
backend and are catalogued on the :doc:`observability` page. All spans are nested under
the currently active OpenTelemetry span, so wrapping your application logic in a parent
span produces a complete trace tree:

.. code-block:: python

    tracer = trace.get_tracer(__name__)

    with tracer.start_as_current_span("handle-request"):
        pool.execute_with_retries("SELECT 1")
        # ↳ ydb.CreateSession  (if a new session is needed)
        #   ↳ ydb.ExecuteQuery


Error Recording
---------------

On failures the OpenTelemetry backend enriches the span before ending it:

- ``error.type`` — ``"ydb_error"``, ``"transport_error"``, or the Python exception class name.
- ``db.response.status_code`` — the YDB status code name (e.g. ``"SCHEME_ERROR"``).
- the span status is set to ``ERROR`` and the exception is recorded via
  ``record_exception``.


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

The runnable script is ``examples/opentelemetry/otel_example.py`` (bank table + concurrent
Serializable transactions, ``app_startup`` / ``example_tli`` application spans, and an
explicitly named topic Reader that emits receive, delivery, and buffer metrics). **Start Docker
(YDB or the full stack) first**, then install and run on the host — see
``examples/opentelemetry/README.md`` for the full order of commands and environment
variables.

**Full stack in one command** (YDB + OTLP + Tempo + Grafana; the ``otel-example`` service is built from ``examples/opentelemetry/Dockerfile`` and runs the script once):

.. code-block:: sh

    docker compose -f examples/opentelemetry/compose-e2e.yaml up --build

The first run builds the ``otel-example`` image from the local SDK source; subsequent runs reuse the cached image. Pass ``--build`` again if you change the SDK or the demo script.

**Typical local run** (YDB in Docker, script on the host — Compose **before** ``pip`` / ``python``):

.. code-block:: sh

    docker compose up -d
    pip install -e '.[opentelemetry]' -r examples/opentelemetry/requirements.txt
    python examples/opentelemetry/otel_example.py

Open `http://localhost:3000 <http://localhost:3000>`_ (Grafana) to explore traces via Tempo.
