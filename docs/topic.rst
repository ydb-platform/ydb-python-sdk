Topic Service
=============

YDB Topic Service is a persistent message queue that supports multiple producers and consumers,
horizontal scaling via partitioning, and at-least-once delivery semantics.

The Python SDK provides both synchronous and asynchronous clients with identical APIs.


Concepts
--------

**Topic** — a named stream of messages divided into one or more partitions.

**Partition** — an ordered, append-only log. Messages within a partition are delivered in order.

**Producer** — a client that writes messages to a topic. Each producer has a ``producer_id``
that is used to deduplicate messages via sequence numbers (``seqno``).

**Consumer** — a named group of readers that share offset state. Each consumer independently
tracks its position in every partition, so multiple consumer groups can read the same topic
without interfering with each other.


Getting a Topic Client
----------------------

The topic client is available on every driver instance via the ``topic_client`` property.

**Synchronous:**

.. code-block:: python

    import ydb

    with ydb.Driver(
        endpoint="grpc://localhost:2136",
        database="/local",
        credentials=ydb.credentials_from_env_variables(),
    ) as driver:
        driver.wait(timeout=5, fail_fast=True)
        topic_client = driver.topic_client

**Asynchronous:**

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
            topic_client = driver.topic_client


Topic Management
----------------

Create a Topic
^^^^^^^^^^^^^^

.. code-block:: python

    # Synchronous
    driver.topic_client.create_topic(
        "/local/my-topic",
        min_active_partitions=1,
        max_active_partitions=10,
        retention_period=datetime.timedelta(hours=24),
        consumers=["my-consumer"],
    )

    # Asynchronous
    await driver.topic_client.create_topic(
        "/local/my-topic",
        min_active_partitions=1,
        max_active_partitions=10,
        retention_period=datetime.timedelta(hours=24),
        consumers=["my-consumer"],
    )

Key parameters for ``create_topic``:

* ``path`` — full topic path including database prefix.
* ``min_active_partitions`` — minimum number of active partitions (default: 1).
* ``max_active_partitions`` — maximum number of partitions when auto-scaling is enabled.
* ``retention_period`` — how long messages are kept (``datetime.timedelta``).
* ``retention_storage_mb`` — maximum storage size per partition in megabytes.
* ``supported_codecs`` — list of :class:`~ydb.TopicCodec` values the topic accepts (default: RAW and GZIP).
* ``consumers`` — list of consumer names (strings) or :class:`~ydb.TopicConsumer` objects to create upfront.
* ``partition_write_speed_bytes_per_second`` — per-partition write throughput limit.


Alter a Topic
^^^^^^^^^^^^^

.. code-block:: python

    # Add a consumer
    driver.topic_client.alter_topic(
        "/local/my-topic",
        add_consumers=["new-consumer"],
    )

    # Change retention
    driver.topic_client.alter_topic(
        "/local/my-topic",
        set_retention_period=datetime.timedelta(hours=48),
    )


Drop a Topic
^^^^^^^^^^^^

.. code-block:: python

    driver.topic_client.drop_topic("/local/my-topic")


Describe a Topic
^^^^^^^^^^^^^^^^

.. code-block:: python

    description = driver.topic_client.describe_topic("/local/my-topic")
    print(description.partitions)
    print(description.consumers)

    # Include partition-level statistics
    description = driver.topic_client.describe_topic(
        "/local/my-topic",
        include_stats=True,
    )


Writing Messages
----------------

Create a Writer
^^^^^^^^^^^^^^^

Use ``topic_client.writer()`` as a context manager (recommended) or create it manually.

**Synchronous:**

.. code-block:: python

    with driver.topic_client.writer("/local/my-topic") as writer:
        writer.write("hello")

**Asynchronous:**

.. code-block:: python

    async with driver.topic_client.writer("/local/my-topic") as writer:
        await writer.write("hello")

**Without context manager** (you must call ``close()`` yourself):

.. code-block:: python

    writer = driver.topic_client.writer("/local/my-topic")
    try:
        writer.write("hello")
    finally:
        writer.close()


Writer Parameters
^^^^^^^^^^^^^^^^^

.. code-block:: python

    writer = driver.topic_client.writer(
        "/local/my-topic",
        producer_id="my-producer",       # Unique producer ID; auto-generated UUID if omitted.
        partition_id=0,                  # Pin to a specific partition; None = auto-select.
        codec=ydb.TopicCodec.GZIP,       # Compress messages. Default: RAW (no compression).
        auto_seqno=True,                 # Auto-increment sequence numbers (default: True).
        auto_created_at=True,            # Auto-set message timestamps (default: True).
    )

* ``producer_id`` is used for deduplication: if the same ``(producer_id, seqno)`` pair is
  received again, YDB silently skips it.
* When ``auto_seqno=True`` the SDK assigns monotonically increasing sequence numbers.
  Set ``auto_seqno=False`` and provide ``seqno`` manually when you need deterministic IDs.


Sending Messages
^^^^^^^^^^^^^^^^

**Simple write** — non-blocking; buffers the message internally and returns immediately:

.. code-block:: python

    writer.write("text message")
    writer.write(b"\x01\x02\x03")          # bytes
    writer.write(["msg-1", "msg-2"])        # send multiple messages in one call

**Full message form** with optional fields:

.. code-block:: python

    writer.write(ydb.TopicWriterMessage(
        data="hello",
        seqno=42,                           # omit when auto_seqno=True
        created_at=datetime.datetime.now(), # omit when auto_created_at=True
        metadata_items={"key": "value"},
    ))

**Write and wait for server acknowledgment:**

.. code-block:: python

    # Blocks until the server confirms the write.
    result = writer.write_with_ack("important message")

    # Get a Future and wait for it later (synchronous client).
    future = writer.async_write_with_ack("important message")
    future.result()  # blocks here

    # Async client — await directly.
    result = await writer.write_with_ack("important message")

**Flush** — wait for all previously buffered messages to be acknowledged:

.. code-block:: python

    for i in range(100):
        writer.write(f"message-{i}")
    writer.flush()  # blocks until all 100 messages are acked

    # Async version:
    await writer.flush()


Async Write Pattern
^^^^^^^^^^^^^^^^^^^

For high-throughput pipelines, buffer writes and gather futures:

.. code-block:: python

    import concurrent.futures

    futures = []
    for i in range(100):
        future = writer.async_write_with_ack(f"message-{i}")
        futures.append(future)

    concurrent.futures.wait(futures)
    for f in futures:
        if f.exception():
            raise f.exception()


Writer Backpressure
^^^^^^^^^^^^^^^^^^^

By default the writer's internal buffer is unbounded — ``write()`` always returns immediately
regardless of how many unacknowledged messages are in flight. Enable backpressure by setting
one or both limits:

.. code-block:: python

    writer = driver.topic_client.writer(
        "/local/my-topic",
        max_buffer_size_bytes=50 * 1024 * 1024,  # pause when 50 MB in flight
        max_buffer_messages=1000,                # pause when 1000 messages in flight
    )

A message is counted as occupying the buffer from the moment it is passed to ``write()``
until the server acknowledges it. Backpressure is active when **at least one** limit is set;
setting both means either limit can trigger a wait (OR semantics).

The limits are **soft**: ``write()`` blocks only if the buffer is *already* at or above the
limit when the call starts. Once unblocked, the entire batch is admitted regardless of its
size. This means callers that batch multiple messages in a single ``write()`` call will never
deadlock even when the batch is larger than the limit.

**Blocking behavior (default)**

When the buffer is at or above the limit, ``write()`` blocks until enough messages are
acknowledged by the server. There is no timeout by default — the call waits indefinitely:

.. code-block:: python

    # Producer pauses here if the buffer is full, then proceeds once space is freed.
    writer.write("message")

**Timeout**

Set ``buffer_wait_timeout_sec`` to raise :class:`~ydb.TopicWriterBufferFullError` if space
does not free up in time. Use a positive value to wait up to that many seconds, or ``0`` to
fail immediately without waiting (non-blocking):

.. code-block:: python

    writer = driver.topic_client.writer(
        "/local/my-topic",
        max_buffer_messages=500,
        buffer_wait_timeout_sec=5.0,  # raise after 5 seconds; use 0 to fail immediately
    )

    try:
        writer.write("message")
    except ydb.TopicWriterBufferFullError:
        # handle overload — log, drop, or apply back-off
        ...

**Async client**

The async writer behaves identically — ``await writer.write()`` suspends the coroutine
instead of blocking the thread:

.. code-block:: python

    writer = driver.topic_client.writer(
        "/local/my-topic",
        max_buffer_size_bytes=4 * 1024 * 1024,
        buffer_wait_timeout_sec=10.0,
    )

    try:
        await writer.write("message")
    except ydb.TopicWriterBufferFullError:
        ...

To apply your own timeout without raising an error, wrap the call with
``asyncio.wait_for``:

.. code-block:: python

    try:
        await asyncio.wait_for(writer.write("message"), timeout=2.0)
    except asyncio.TimeoutError:
        ...  # timed out waiting for buffer space


Reading Messages
----------------

Create a Reader
^^^^^^^^^^^^^^^

A reader requires a ``consumer`` name that must already exist on the topic.

**Synchronous:**

.. code-block:: python

    with driver.topic_client.reader("/local/my-topic", consumer="my-consumer") as reader:
        message = reader.receive_message()
        print(message.data.decode())
        reader.commit(message)

**Asynchronous:**

.. code-block:: python

    async with driver.topic_client.reader("/local/my-topic", consumer="my-consumer") as reader:
        message = await reader.receive_message()
        print(message.data.decode())
        reader.commit(message)

Reader Parameters
^^^^^^^^^^^^^^^^^

.. code-block:: python

    reader = driver.topic_client.reader(
        topic="/local/my-topic",           # str, TopicReaderSelector, or a list of these
        consumer="my-consumer",
        buffer_size_bytes=50 * 1024 * 1024,  # client-side buffer (default: 50 MB)
        buffer_release_threshold=0.5,        # see below (default: 0.5)
    )

``buffer_size_bytes`` controls how many bytes the server is allowed to send before the client
signals that it is ready for more. The server will not exceed this limit.

``buffer_release_threshold`` (float in ``[0.0, 1.0]``) controls when the client sends a new
``ReadRequest`` to the server after consuming messages from the local buffer:

* ``0.0`` — send a ``ReadRequest`` immediately after every batch is consumed.
  Produces more round-trips when many small batches arrive.
* ``> 0.0`` — accumulate freed bytes until they reach
  ``threshold × buffer_size_bytes``, then send a single ``ReadRequest`` covering the
  accumulated amount. This reduces network round-trips. The default is ``0.5``.

Example — reduce round-trips for a high-throughput reader with many small messages:

.. code-block:: python

    reader = driver.topic_client.reader(
        "/local/my-topic",
        consumer="my-consumer",
        buffer_size_bytes=50 * 1024 * 1024,
        buffer_release_threshold=0.2,  # send ReadRequest after freeing 10 MiB
    )

To read from multiple topics at once, pass a list:

.. code-block:: python

    reader = driver.topic_client.reader(
        topic=["/local/topic-a", "/local/topic-b"],
        consumer="my-consumer",
    )

To fine-tune per-topic settings (e.g. start offset or timestamp), use :class:`~ydb.TopicReaderSelector`:

.. code-block:: python

    reader = driver.topic_client.reader(
        topic=ydb.TopicReaderSelector(
            path="/local/my-topic",
            read_from=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
        ),
        consumer="my-consumer",
    )


Receiving Messages
^^^^^^^^^^^^^^^^^^

**One message at a time:**

.. code-block:: python

    # Synchronous — blocks until a message arrives.
    message = reader.receive_message()
    print(message.data.decode())
    reader.commit(message)

    # With timeout — raises TimeoutError if no message arrives within 1 second.
    try:
        message = reader.receive_message(timeout=1)
    except TimeoutError:
        print("no new messages")

    # Asynchronous:
    message = await reader.receive_message()

**Batch processing:**

.. code-block:: python

    # Synchronous
    batch = reader.receive_batch()
    for message in batch.messages:
        process(message)
    reader.commit(batch)   # commit the whole batch at once

    # With size limits
    batch = reader.receive_batch(max_messages=100)

    # Asynchronous
    batch = await reader.receive_batch()
    for message in batch.messages:
        process(message)
    reader.commit(batch)


Message Fields
^^^^^^^^^^^^^^

Each received message exposes:

.. code-block:: python

    message.data           # bytes — the message payload
    message.seqno          # int — producer sequence number
    message.offset         # int — partition offset
    message.partition_id   # int — partition this message came from
    message.producer_id    # str — producer_id set by the writer
    message.created_at     # datetime — timestamp set by the writer
    message.written_at     # datetime — timestamp when YDB persisted the message
    message.metadata_items # Dict[str, bytes] — arbitrary key-value metadata


Committing Offsets
^^^^^^^^^^^^^^^^^^

Committing tells YDB that the consumer has successfully processed a message. YDB resumes
from the last committed offset when the reader reconnects.

.. code-block:: python

    # Non-blocking commit — buffered and sent in the background.
    reader.commit(message)
    reader.commit(batch)

    # Blocking commit — waits for the server to acknowledge the commit.
    reader.commit_with_ack(message)

    # Async version:
    await reader.commit_with_ack(message)

.. note::

   ``commit()`` is non-blocking and sufficient for most use cases. The offset is flushed
   automatically when the reader is closed (``flush=True`` by default).


Handling Partition Rebalancing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When the topic rebalances (partitions are reassigned between reader instances), unfinished
messages from revoked partitions become stale. The SDK signals this via the ``alive``
property:

.. code-block:: python

    # Per message
    message = reader.receive_message()
    # ... do some work ...
    if message.alive:
        reader.commit(message)

    # Per batch — check before expensive processing
    batch = reader.receive_batch()
    for message in batch.messages:
        if not batch.alive:
            break   # partition revoked, skip remaining messages
        process(message)
    if batch.alive:
        reader.commit(batch)


Transactions
------------

The SDK integrates with YDB transactions so that topic writes and reads can be made
atomically together with database queries.

Transactional Write
^^^^^^^^^^^^^^^^^^^

Use ``topic_client.tx_writer(tx, topic)`` inside a transaction callback:

**Synchronous:**

.. code-block:: python

    def write_with_tx(driver: ydb.Driver, topic: str):
        with ydb.QuerySessionPool(driver) as pool:

            def callee(tx: ydb.QueryTxContext):
                tx_writer = driver.topic_client.tx_writer(tx, topic)
                for i in range(10):
                    tx_writer.write(ydb.TopicWriterMessage(f"message-{i}"))

            pool.retry_tx_sync(callee)

**Asynchronous:**

.. code-block:: python

    async def write_with_tx(driver: ydb.aio.Driver, topic: str):
        async with ydb.aio.QuerySessionPool(driver) as pool:

            async def callee(tx: ydb.aio.QueryTxContext):
                tx_writer = driver.topic_client.tx_writer(tx, topic)
                for i in range(10):
                    await tx_writer.write(ydb.TopicWriterMessage(f"message-{i}"))

            await pool.retry_tx_async(callee)

Messages written via a ``tx_writer`` are visible to readers only after the transaction commits.
If the transaction rolls back, the messages are discarded.


Transactional Read
^^^^^^^^^^^^^^^^^^

Use ``reader.receive_batch_with_tx(tx)`` to read messages inside a transaction. The commit
offset is advanced atomically with the transaction:

**Synchronous:**

.. code-block:: python

    def read_with_tx(driver: ydb.Driver, topic: str, consumer: str):
        with driver.topic_client.reader(topic, consumer) as reader:
            with ydb.QuerySessionPool(driver) as pool:

                def callee(tx: ydb.QueryTxContext):
                    batch = reader.receive_batch_with_tx(tx, max_messages=10)
                    for message in batch.messages:
                        process(message)

                pool.retry_tx_sync(callee)

**Asynchronous:**

.. code-block:: python

    async def read_with_tx(driver: ydb.aio.Driver, topic: str, consumer: str):
        async with driver.topic_client.reader(topic, consumer) as reader:
            async with ydb.aio.QuerySessionPool(driver) as pool:

                async def callee(tx: ydb.aio.QueryTxContext):
                    batch = await reader.receive_batch_with_tx(tx, max_messages=10)
                    for message in batch.messages:
                        process(message)

                await pool.retry_tx_async(callee)

.. note::

   Do not call ``reader.commit()`` when using ``receive_batch_with_tx`` — the commit is
   handled automatically by the transaction.


Auto-Partitioning
-----------------

YDB can automatically scale the number of partitions up (and optionally down) based on write
throughput. Enable it when creating a topic:

.. code-block:: python

    import datetime
    import ydb

    driver.topic_client.create_topic(
        "/local/my-topic",
        consumers=["my-consumer"],
        max_active_partitions=100,
        auto_partitioning_settings=ydb.TopicAutoPartitioningSettings(
            strategy=ydb.TopicAutoPartitioningStrategy.SCALE_UP,
            up_utilization_percent=70,      # split a partition when it reaches 70% capacity
            down_utilization_percent=30,    # merge partitions when below 30% (SCALE_UP_AND_DOWN only)
            stabilization_window=datetime.timedelta(seconds=60),
        ),
    )

Available :class:`~ydb.TopicAutoPartitioningStrategy` values:

* ``SCALE_UP`` — only split partitions (add capacity).
* ``SCALE_UP_AND_DOWN`` — split and merge partitions automatically.
* ``DISABLED`` — static partition count.

The reader handles partition splits and merges transparently when ``auto_partitioning_support=True``
(which is the default):

.. code-block:: python

    reader = driver.topic_client.reader(
        "/local/my-topic",
        consumer="my-consumer",
        auto_partitioning_support=True,  # default
    )


Custom Codecs
-------------

The SDK supports RAW (no compression) and GZIP out of the box. You can register custom
encode/decode functions for any codec ID:

**Custom encoder (writer side):**

.. code-block:: python

    import zlib

    def my_compress(data: bytes) -> bytes:
        return zlib.compress(data)

    CUSTOM_CODEC = 10001  # must be in range 10000–19999

    writer = driver.topic_client.writer(
        "/local/my-topic",
        codec=CUSTOM_CODEC,
        encoders={CUSTOM_CODEC: my_compress},
    )

**Custom decoder (reader side):**

.. code-block:: python

    def my_decompress(data: bytes) -> bytes:
        return zlib.decompress(data)

    reader = driver.topic_client.reader(
        "/local/my-topic",
        consumer="my-consumer",
        decoders={CUSTOM_CODEC: my_decompress},
    )

For CPU-intensive codecs you can offload encoding/decoding to a thread pool:

.. code-block:: python

    import concurrent.futures

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

    writer = driver.topic_client.writer(
        "/local/my-topic",
        codec=CUSTOM_CODEC,
        encoders={CUSTOM_CODEC: my_compress},
        encoder_executor=executor,
    )


Topic Client Settings
---------------------

Pass :class:`~ydb.TopicClientSettings` to the driver config to tune SDK-wide defaults:

.. code-block:: python

    config = ydb.DriverConfig(
        endpoint="grpc://localhost:2136",
        database="/local",
    )
    config.topic_client_settings = ydb.TopicClientSettings(
        encode_decode_threads_count=4,  # threads used for codec operations (default: 1)
    )

    driver = ydb.Driver(config)


Complete Examples
-----------------

Synchronous: Write and Read
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    import ydb

    endpoint = "grpc://localhost:2136"
    database = "/local"
    topic_path = "/local/my-topic"
    consumer = "my-consumer"

    with ydb.Driver(endpoint=endpoint, database=database) as driver:
        driver.wait(timeout=5, fail_fast=True)

        # Create topic (skip if already exists)
        try:
            driver.topic_client.drop_topic(topic_path)
        except ydb.SchemeError:
            pass
        driver.topic_client.create_topic(topic_path, consumers=[consumer])

        # Write messages
        with driver.topic_client.writer(topic_path) as writer:
            for i in range(10):
                writer.write(f"message-{i}")

        # Read messages
        with driver.topic_client.reader(topic_path, consumer=consumer) as reader:
            for _ in range(10):
                try:
                    message = reader.receive_message(timeout=5)
                    print(message.data.decode())
                    reader.commit(message)
                except TimeoutError:
                    break


Asynchronous: Write and Read Concurrently
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    import asyncio
    import ydb

    endpoint = "grpc://localhost:2136"
    database = "/local"
    topic_path = "/local/my-topic"
    consumer = "my-consumer"

    async def write_messages(driver: ydb.aio.Driver):
        async with driver.topic_client.writer(topic_path) as writer:
            for i in range(10):
                await writer.write(ydb.TopicWriterMessage(
                    data=f"message-{i}",
                    metadata_items={"index": str(i)},
                ))

    async def read_messages(driver: ydb.aio.Driver):
        async with driver.topic_client.reader(topic_path, consumer=consumer) as reader:
            while True:
                try:
                    message = await asyncio.wait_for(reader.receive_message(), timeout=5)
                    print(message.data.decode(), message.metadata_items)
                    reader.commit(message)
                except asyncio.TimeoutError:
                    return

    async def main():
        async with ydb.aio.Driver(endpoint=endpoint, database=database) as driver:
            await driver.wait(timeout=5, fail_fast=True)

            # Create topic
            try:
                await driver.topic_client.drop_topic(topic_path)
            except ydb.SchemeError:
                pass
            await driver.topic_client.create_topic(topic_path, consumers=[consumer])

            await asyncio.gather(write_messages(driver), read_messages(driver))

    asyncio.run(main())
