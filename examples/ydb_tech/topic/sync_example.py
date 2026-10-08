"""Executable source of the synchronous topic snippets on ydb.tech."""

import collections
import datetime
import os
import uuid

import ydb
import ydb.aio

EXPECTED = [
    b"mess",
    bytes([1, 2, 3]),
    b"mess-1",
    b"mess-2",
    b"buffer-one",
    b"buffer-two",
    b"mess-1",
    b"mess-2",
    b"message",
    b"message-data",
    b"asd",
    bytes([1, 2, 3]),
    b"compressed",
    b"asd",
    bytes([1, 2, 3]),
]


class ScenarioComplete(Exception):
    pass


class FiniteReader:
    def __init__(self, reader, received):
        self.reader = reader
        self.received = received

    def __getattr__(self, name):
        return getattr(self.reader, name)

    def receive_message(self):
        if len(self.received) >= len(EXPECTED):
            raise ScenarioComplete
        return self.reader.receive_message(timeout=30)

    def receive_batch(self):
        if len(self.received) >= len(EXPECTED):
            raise ScenarioComplete
        return self.reader.receive_batch(timeout=30)


def check_message(message):
    assert message.data in EXPECTED
    if message.data == b"message-data":
        assert message.metadata_items["meta-key"] == b"meta-value"
    return message.data


def initialize(topic_path, consumer_name):
    # [BEGIN topic_init]
    import os
    import ydb

    driver_config = ydb.DriverConfig(
        endpoint=os.environ["YDB_ENDPOINT"],
        database=os.environ["YDB_DATABASE"],
    )
    driver = ydb.Driver(driver_config)
    driver.wait(timeout=5)
    # driver.topic_client — client for working with topics
    writer = driver.topic_client.writer(topic_path)
    reader = driver.topic_client.reader(topic=topic_path, consumer=consumer_name)
    # [END topic_init]
    writer.close()
    reader.close()
    driver.stop()


def run():
    os.environ.setdefault("YDB_ENDPOINT", "grpc://localhost:2136")
    os.environ.setdefault("YDB_DATABASE", "/local")
    topic_path = "ydb_tech_" + uuid.uuid4().hex
    consumers = ["init", "one", "batch", "commit_one", "commit_batch", "soft", "hard", "outside"]
    config = ydb.DriverConfig(endpoint=os.environ["YDB_ENDPOINT"], database=os.environ["YDB_DATABASE"])
    with ydb.Driver(config) as driver:
        driver.wait(timeout=30)
        # [BEGIN topic_create]
        driver.topic_client.create_topic(
            topic_path,
            supported_codecs=[ydb.TopicCodec.RAW, ydb.TopicCodec.GZIP],  # optional
            min_active_partitions=3,  # optional
        )
        # [END topic_create]
        try:
            driver.topic_client.alter_topic(topic_path, add_consumers=consumers)
            initialize(topic_path, "init")
            # [BEGIN topic_alter]
            driver.topic_client.alter_topic(
                topic_path,
                set_supported_codecs=[ydb.TopicCodec.RAW, ydb.TopicCodec.GZIP],  # optional
                set_min_active_partitions=3,  # optional
            )
            # [END topic_alter]
            # [BEGIN topic_describe]
            info = driver.topic_client.describe_topic(topic_path)
            print(info)
            # [END topic_describe]
            assert len(info.consumers) == len(consumers)
            seed(driver, topic_path)
            for consumer in ["one", "batch", "commit_one", "commit_batch", "soft"]:
                consume(driver, topic_path, consumer)
            metadata(driver, topic_path + "_metadata")
            without_consumer(driver, topic_path)
            expired_batch(driver, topic_path)
            commit_outside(driver, topic_path)
            transactions(driver, topic_path + "_tx")
            autoscaling(driver, topic_path + "_auto")
        finally:
            # [BEGIN topic_drop]
            driver.topic_client.drop_topic(topic_path)
            # [END topic_drop]


def start_writer(driver, topic_path):
    # [BEGIN topic_start_writer]
    writer = driver.topic_client.writer(topic_path)
    # [END topic_start_writer]
    return writer


def seed(driver, topic_path):
    messages = ["buffer-one", "buffer-two"]
    # [BEGIN topic_write]
    # Simple message sending, without explicitly specifying metadata.
    # Convenient to start with, convenient to use while only the message content matters.
    writer = driver.topic_client.writer(topic_path)
    writer.write("mess")  # Strings are encoded as utf-8; convenient for
    # text messages.
    writer.write(bytes([1, 2, 3]))  # Bytes are sent unchanged; convenient for
    # binary data.
    writer.write(["mess-1", "mess-2"])  # Send multiple messages with one call:
    # this reduces overhead on internal SDK processes,
    # makes sense with a large message stream.
    # [END topic_write]
    try:
        # [BEGIN topic_write_ack]
        # Put several messages into the internal buffer, then wait
        # until all of them are delivered to the server.
        for mess in messages:
            writer.write(mess)

        writer.flush()

        # You can send several messages and wait for acknowledgment for the entire group.
        writer.write_with_ack(["mess-1", "mess-2"])

        # Waiting when sending each message — this method will return a result only after receiving
        # acknowledgment from the server.
        # This is the slowest message sending option, use it only if this mode
        # is really needed.
        writer.write_with_ack("message")
        # [END topic_write_ack]
        # [BEGIN topic_write_metadata]
        message = ydb.TopicWriterMessage(data="message-data", metadata_items={"meta-key": "meta-value"})
        writer.write(message)
        # [END topic_write_metadata]
    finally:
        writer.close()
    # [BEGIN topic_write_manual]
    # Full form, used when, in addition to the message content, you need to manually set its properties.
    writer = driver.topic_client.writer(topic=topic_path, auto_seqno=False, auto_created_at=False)

    writer.write(ydb.TopicWriterMessage("asd", seqno=123, created_at=datetime.datetime.now()))
    writer.write(ydb.TopicWriterMessage(bytes([1, 2, 3]), seqno=124, created_at=datetime.datetime.now()))

    # In the full form, you can also send multiple messages in a single function call.
    # This makes sense with a large stream of outgoing messages — to reduce
    # overhead on internal SDK calls.
    writer.write(
        [
            ydb.TopicWriterMessage("asd", seqno=125, created_at=datetime.datetime.now()),
            ydb.TopicWriterMessage(bytes([1, 2, 3]), seqno=126, created_at=datetime.datetime.now()),
        ]
    )
    # [END topic_write_manual]
    writer.close()
    # [BEGIN topic_codec]
    writer = driver.topic_client.writer(
        topic_path,
        codec=ydb.TopicCodec.GZIP,
    )
    # [END topic_codec]
    with writer:
        writer.write_with_ack("compressed")


def consume(driver, topic_path, consumer_name):
    # [BEGIN topic_start_reader]
    reader = driver.topic_client.reader(topic=topic_path, consumer=consumer_name)
    # [END topic_start_reader]
    received = []

    def process(value):
        messages = value.messages if hasattr(value, "messages") else [value]
        received.extend(check_message(message) for message in messages)

    with reader:
        reader = FiniteReader(reader, received)
        try:
            if consumer_name == "one":
                # [BEGIN topic_read_one]
                while True:
                    message = reader.receive_message()
                    process(message)
                # [END topic_read_one]
            elif consumer_name == "batch":
                # [BEGIN topic_read_batch]
                while True:
                    batch = reader.receive_batch()
                    process(batch)
                # [END topic_read_batch]
            elif consumer_name == "commit_one":
                # [BEGIN topic_read_commit]
                while True:
                    message = reader.receive_message()
                    process(message)
                    reader.commit(message)
                # [END topic_read_commit]
            elif consumer_name == "commit_batch":
                # [BEGIN topic_read_batch_commit]
                while True:
                    batch = reader.receive_batch()
                    process(batch)
                    reader.commit(batch)
                # [END topic_read_batch_commit]
            elif consumer_name == "soft":
                # [BEGIN topic_soft_stop]
                while True:
                    batch = reader.receive_batch()
                    process(batch)
                    reader.commit(batch)
                # [END topic_soft_stop]
        except ScenarioComplete:
            pass
    assert collections.Counter(received) == collections.Counter(EXPECTED)


def metadata(driver, topic_path):
    driver.topic_client.create_topic(topic_path, consumers=["metadata"])
    try:
        with driver.topic_client.writer(topic_path) as writer:
            writer.write_with_ack(ydb.TopicWriterMessage("message-data", metadata_items={"meta-key": "meta-value"}))
        with driver.topic_client.reader(topic_path, "metadata") as reader:
            # [BEGIN topic_read_metadata]
            message = reader.receive_message()
            for meta_key, meta_value in message.metadata_items.items():
                print(f"{meta_key}: {meta_value}")
            # [END topic_read_metadata]
            assert message.metadata_items["meta-key"] == b"meta-value"
    finally:
        driver.topic_client.drop_topic(topic_path)


# [BEGIN topic_no_consumer_handler]
class CustomEventHandler(ydb.TopicReaderEvents.EventHandler):
    def on_partition_get_start_offset(self, event: ydb.TopicReaderEvents.OnPartitionGetStartOffsetRequest):
        return ydb.TopicReaderEvents.OnPartitionGetStartOffsetResponse(
            start_offset=0,
        )


# [END topic_no_consumer_handler]


def without_consumer(driver, topic_path):
    # [BEGIN topic_no_consumer]
    reader = driver.topic_client.reader(
        topic=ydb.TopicReaderSelector(
            path=topic_path,
            partitions=[0, 1, 2],
        ),
        consumer=None,
        event_handler=CustomEventHandler(),
    )
    # [END topic_no_consumer]
    with reader:
        message = reader.receive_message(timeout=30)
        check_message(message)


def expired_batch(driver, topic_path):
    reader = driver.topic_client.reader(topic_path, "hard")
    process = check_message
    try:
        # [BEGIN topic_hard_stop]
        def process_batch(batch):
            for message in batch.messages:
                if not batch.alive:
                    return False
                process(message)
            return True

        batch = reader.receive_batch()
        if process_batch(batch):
            reader.commit(batch)
        # [END topic_hard_stop]
    finally:
        reader.close(flush=False)
    assert not process_batch(batch)


def commit_outside(driver, topic_path):
    consumer_name = "outside"
    with driver.topic_client.reader(topic_path, consumer_name) as reader:
        message = reader.receive_message(timeout=30)
        check_message(message)
        partition_id = message.partition_id
        offset = message.offset + 1
        # [BEGIN topic_commit_outside]
        driver.topic_client.commit_offset(
            topic_path,
            consumer_name,
            partition_id,
            offset,
            reader.read_session_id,  # опционально: не прерывает активную сессию чтения
        )
        # [END topic_commit_outside]


def transactions(driver, topic):
    consumer = "transaction"
    message_count = 3
    driver.topic_client.create_topic(topic, consumers=[consumer, "verify"])
    try:
        # [BEGIN topic_write_tx]
        with ydb.QuerySessionPool(driver) as session_pool:

            def callee(tx: ydb.QueryTxContext):
                tx_writer: ydb.TopicTxWriter = driver.topic_client.tx_writer(tx, topic)

                for i in range(message_count):
                    result_stream = tx.execute(query=f"select {i} as res;")
                    for result_set in result_stream:
                        message = str(result_set.rows[0]["res"])
                        tx_writer.write(ydb.TopicWriterMessage(message))
                        print(f"Message {message} was written with tx.")

            session_pool.retry_tx_sync(callee)
        # [END topic_write_tx]
        with driver.topic_client.reader(topic, "verify") as verifier:
            payloads = []
            while len(payloads) < message_count:
                batch = verifier.receive_batch(timeout=30)
                payloads.extend(message.data for message in batch.messages)
            assert payloads == [b"0", b"1", b"2"]
        # [BEGIN topic_read_tx]
        with driver.topic_client.reader(topic, consumer) as reader:
            with ydb.QuerySessionPool(driver) as session_pool:
                for _ in range(message_count):

                    def callee(tx: ydb.QueryTxContext):
                        batch = reader.receive_batch_with_tx(tx, max_messages=1)
                        print(f"Message {batch.messages[0].data.decode()} was read with tx.")

                    session_pool.retry_tx_sync(callee)
        # [END topic_read_tx]
    finally:
        driver.topic_client.drop_topic(topic)


def autoscaling(driver, topic):
    consumer = "auto"
    # [BEGIN topic_autoscale_create]
    driver.topic_client.create_topic(
        topic,
        consumers=[consumer],
        min_active_partitions=10,
        max_active_partitions=100,
        auto_partitioning_settings=ydb.TopicAutoPartitioningSettings(
            strategy=ydb.TopicAutoPartitioningStrategy.SCALE_UP,
            up_utilization_percent=80,
            down_utilization_percent=20,
            stabilization_window=datetime.timedelta(seconds=300),
        ),
    )
    # [END topic_autoscale_create]
    topic_path = topic
    try:
        # [BEGIN topic_autoscale_alter]
        driver.topic_client.alter_topic(
            topic_path,
            alter_auto_partitioning_settings=ydb.TopicAlterAutoPartitioningSettings(
                set_strategy=ydb.TopicAutoPartitioningStrategy.SCALE_UP,
                set_up_utilization_percent=80,
                set_down_utilization_percent=20,
                set_stabilization_window=datetime.timedelta(seconds=300),
            ),
        )
        # [END topic_autoscale_alter]
        with driver.topic_client.writer(topic) as writer:
            writer.write_with_ack("auto")
        # [BEGIN topic_autoscale_reader_full]
        reader = driver.topic_client.reader(
            topic,
            consumer,
            auto_partitioning_support=True,  # Full support is enabled
        )
        # [END topic_autoscale_reader_full]
        with reader:
            message = reader.receive_message(timeout=30)
            assert message.data == b"auto"
        # [BEGIN topic_autoscale_reader_compat]
        reader = driver.topic_client.reader(
            topic,
            consumer,
            auto_partitioning_support=False,  # Compatibility mode is enabled
        )
        # [END topic_autoscale_reader_compat]
        with reader:
            message = reader.receive_message(timeout=30)
            assert message.data == b"auto"
    finally:
        driver.topic_client.drop_topic(topic)


if __name__ == "__main__":
    run()
