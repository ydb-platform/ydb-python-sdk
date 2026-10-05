"""Executable source of the synchronous topic snippets on ydb.tech."""

import collections
import datetime
import os
import uuid

import ydb

EXPECTED = [
    b"text",
    bytes([1, 2, 3]),
    b"batch-one",
    b"batch-two",
    b"manual-one",
    b"manual-two",
    b"buffer-one",
    b"buffer-two",
    b"ack-batch-one",
    b"ack-batch-two",
    b"ack-one",
    b"metadata",
    b"compressed",
]


def run():
    endpoint = os.getenv("YDB_ENDPOINT", "grpc://localhost:2136")
    database = os.getenv("YDB_DATABASE", "/local")
    topic_path = "ydb_tech_" + uuid.uuid4().hex
    consumers = ["one", "batch", "commit_one", "commit_batch", "soft", "hard", "outside", "transaction"]
    # [BEGIN topic_init]
    config = ydb.DriverConfig(endpoint=endpoint, database=database)
    with ydb.Driver(config) as driver:
        driver.wait(timeout=30)
        # [END topic_init]
        # [BEGIN topic_create]
        driver.topic_client.create_topic(
            topic_path,
            consumers=consumers,
            supported_codecs=[ydb.TopicCodec.RAW, ydb.TopicCodec.GZIP],
            min_active_partitions=3,
            max_active_partitions=3,
        )
        # [END topic_create]
        try:
            # [BEGIN topic_alter]
            driver.topic_client.alter_topic(
                topic_path,
                set_supported_codecs=[ydb.TopicCodec.RAW, ydb.TopicCodec.GZIP],
                set_min_active_partitions=3,
                add_consumers=["another-consumer"],
            )
            # [END topic_alter]
            # [BEGIN topic_describe]
            info = driver.topic_client.describe_topic(topic_path)
            print("Consumers:", [consumer.name for consumer in info.consumers])
            # [END topic_describe]
            assert len(info.consumers) == len(consumers) + 1

            seed(driver, topic_path)
            for consumer in ["one", "batch", "commit_one", "commit_batch", "soft"]:
                consume(driver, topic_path, consumer)
            without_consumer(driver, topic_path)
            expired_batch(driver, topic_path)
            commit_outside(driver, topic_path)
            transactions(driver, topic_path)
            autoscaling(driver, topic_path + "_auto")
        finally:
            # [BEGIN topic_drop]
            driver.topic_client.drop_topic(topic_path)
            # [END topic_drop]
    print("All synchronous topic scenarios completed")


def seed(driver, topic_path):
    # [BEGIN topic_start_writer]
    writer = driver.topic_client.writer(topic_path, partition_id=0)
    # [END topic_start_writer]
    with writer:
        # [BEGIN topic_write]
        writer.write("text")
        writer.write(bytes([1, 2, 3]))
        writer.write(["batch-one", "batch-two"])
        # [END topic_write]
        # [BEGIN topic_write_ack]
        for message in ["buffer-one", "buffer-two"]:
            writer.write(message)
        writer.flush(timeout=30)
        writer.write_with_ack(["ack-batch-one", "ack-batch-two"], timeout=30)
        writer.write_with_ack("ack-one", timeout=30)
        # [END topic_write_ack]
        # [BEGIN topic_write_metadata]
        message = ydb.TopicWriterMessage(data="metadata", metadata_items={"meta-key": "meta-value"})
        writer.write(message)
        # [END topic_write_metadata]

    # [BEGIN topic_write_manual]
    with driver.topic_client.writer(topic_path, partition_id=0, auto_seqno=False, auto_created_at=False) as writer:
        writer.write(
            [
                ydb.TopicWriterMessage(
                    "manual-one", seqno=123, created_at=datetime.datetime.now(datetime.timezone.utc)
                ),
                ydb.TopicWriterMessage(
                    "manual-two", seqno=124, created_at=datetime.datetime.now(datetime.timezone.utc)
                ),
            ]
        )
    # [END topic_write_manual]
    # [BEGIN topic_codec]
    with driver.topic_client.writer(topic_path, partition_id=0, codec=ydb.TopicCodec.GZIP) as writer:
        writer.write_with_ack("compressed", timeout=30)
    # [END topic_codec]


def consume(driver, topic_path, consumer_name):
    # [BEGIN topic_start_reader]
    reader = driver.topic_client.reader(topic=topic_path, consumer=consumer_name)
    # [END topic_start_reader]
    received = []
    with reader:
        if consumer_name == "one":
            # [BEGIN topic_read_one]
            while len(received) < len(EXPECTED):
                message = reader.receive_message(timeout=30)
                received.append(check_message(message))
            # [END topic_read_one]
        elif consumer_name == "batch":
            # [BEGIN topic_read_batch]
            while len(received) < len(EXPECTED):
                batch = reader.receive_batch(timeout=30)
                received.extend(check_message(message) for message in batch.messages)
            # [END topic_read_batch]
        elif consumer_name == "commit_one":
            # [BEGIN topic_read_commit]
            while len(received) < len(EXPECTED):
                message = reader.receive_message(timeout=30)
                received.append(check_message(message))
                reader.commit(message)
            # [END topic_read_commit]
        elif consumer_name == "commit_batch":
            # [BEGIN topic_read_batch_commit]
            while len(received) < len(EXPECTED):
                batch = reader.receive_batch(timeout=30)
                received.extend(check_message(message) for message in batch.messages)
                reader.commit(batch)
            # [END topic_read_batch_commit]
        else:
            # [BEGIN topic_soft_stop]
            while len(received) < len(EXPECTED):
                batch = reader.receive_batch(timeout=30)
                received.extend(check_message(message) for message in batch.messages)
                reader.commit(batch)
            # [END topic_soft_stop]
        assert collections.Counter(received) == collections.Counter(EXPECTED)


def check_message(message):
    assert message is not None
    assert message.data in EXPECTED
    if message.data == b"metadata":
        # [BEGIN topic_read_metadata]
        for key, value in message.metadata_items.items():
            print(key, value)
        # [END topic_read_metadata]
        assert message.metadata_items["meta-key"] == b"meta-value"
    return message.data


# [BEGIN topic_no_consumer_handler]
class StartAtBeginning(ydb.TopicReaderEvents.EventHandler):
    def on_partition_get_start_offset(self, event):
        return ydb.TopicReaderEvents.OnPartitionGetStartOffsetResponse(start_offset=0)


# [END topic_no_consumer_handler]


def without_consumer(driver, topic_path):
    # [BEGIN topic_no_consumer]
    with driver.topic_client.reader(
        topic=ydb.TopicReaderSelector(path=topic_path, partitions=[0]),
        consumer=None,
        event_handler=StartAtBeginning(),
    ) as reader:
        message = reader.receive_message(timeout=30)
        check_message(message)
    # [END topic_no_consumer]


def expired_batch(driver, topic_path):
    reader = driver.topic_client.reader(topic=topic_path, consumer="hard")
    try:
        batch = reader.receive_batch(max_messages=1, timeout=30)
        assert process_batch(batch)
    finally:
        reader.close(flush=False, timeout=30)
    assert not process_batch(batch)


# [BEGIN topic_hard_stop]
def process_batch(batch):
    for message in batch.messages:
        if not batch.alive:
            return False
        check_message(message)
    return True


# [END topic_hard_stop]


def commit_outside(driver, topic_path):
    with driver.topic_client.reader(topic_path, "outside") as reader:
        message = reader.receive_message(timeout=30)
        check_message(message)
        # [BEGIN topic_commit_outside]
        driver.topic_client.commit_offset(
            topic_path,
            "outside",
            0,
            message.offset + 1,
            reader.read_session_id,
        )
        # [END topic_commit_outside]


def transactions(driver, topic_path):
    transaction_topic = topic_path + "_tx"
    driver.topic_client.create_topic(transaction_topic, consumers=["transaction"])
    try:
        # [BEGIN topic_write_tx]
        with ydb.QuerySessionPool(driver) as pool:

            def write_in_transaction(tx):
                writer = driver.topic_client.tx_writer(tx, transaction_topic)
                for result_set in tx.execute("SELECT 'transaction-message' AS payload"):
                    payload = result_set.rows[0]["payload"]
                    writer.write(ydb.TopicWriterMessage(payload))

            pool.retry_tx_sync(write_in_transaction)
        # [END topic_write_tx]

        # [BEGIN topic_read_tx]
        with driver.topic_client.reader(transaction_topic, "transaction") as reader:
            with ydb.QuerySessionPool(driver) as pool:

                def read_in_transaction(tx):
                    batch = reader.receive_batch_with_tx(tx, max_messages=1, timeout=30)
                    assert batch.messages[0].data == b"transaction-message"

                pool.retry_tx_sync(read_in_transaction)
        # [END topic_read_tx]
    finally:
        driver.topic_client.drop_topic(transaction_topic)


def autoscaling(driver, topic_path):
    # [BEGIN topic_autoscale_create]
    driver.topic_client.create_topic(
        topic_path,
        consumers=["auto"],
        min_active_partitions=1,
        max_active_partitions=4,
        auto_partitioning_settings=ydb.TopicAutoPartitioningSettings(
            strategy=ydb.TopicAutoPartitioningStrategy.SCALE_UP,
            up_utilization_percent=80,
            down_utilization_percent=20,
            stabilization_window=datetime.timedelta(seconds=300),
        ),
    )
    # [END topic_autoscale_create]
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
        with driver.topic_client.writer(topic_path) as writer:
            writer.write_with_ack("auto", timeout=30)
        # [BEGIN topic_autoscale_reader]
        for full_support in [True, False]:
            with driver.topic_client.reader(
                topic_path,
                "auto",
                auto_partitioning_support=full_support,
            ) as reader:
                message = reader.receive_message(timeout=30)
                assert message.data == b"auto"
        # [END topic_autoscale_reader]
    finally:
        driver.topic_client.drop_topic(topic_path)


if __name__ == "__main__":
    run()
