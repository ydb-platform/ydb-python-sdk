"""Executable source of the asynchronous topic snippets on ydb.tech."""

import asyncio
import collections
import faulthandler
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
]


class ScenarioComplete(Exception):
    pass


class FiniteReader:
    def __init__(self, reader, received):
        self.reader = reader
        self.received = received

    def __getattr__(self, name):
        return getattr(self.reader, name)

    async def receive_message(self):
        if len(self.received) >= len(EXPECTED):
            raise ScenarioComplete
        return await asyncio.wait_for(self.reader.receive_message(), 30)

    async def receive_batch(self):
        if len(self.received) >= len(EXPECTED):
            raise ScenarioComplete
        return await asyncio.wait_for(self.reader.receive_batch(), 30)


def check_message(message):
    assert message.data in EXPECTED
    if message.data == b"message-data":
        assert message.metadata_items["meta-key"] == b"meta-value"
    return message.data


async def initialize(topic_path, consumer_name):
    # [BEGIN topic_init]
    import os
    import ydb

    driver_config = ydb.DriverConfig(
        endpoint=os.environ["YDB_ENDPOINT"],
        database=os.environ["YDB_DATABASE"],
    )
    async with ydb.aio.Driver(driver_config) as driver:
        await driver.wait(timeout=5)
        # driver.topic_client — client for working with topics
        writer = driver.topic_client.writer(topic_path)
        reader = driver.topic_client.reader(topic=topic_path, consumer=consumer_name)
        # [END topic_init]
        await writer.write_with_ack("initialization")
        message = await asyncio.wait_for(reader.receive_message(), 30)
        assert message.data == b"initialization"
        await writer.close()
        await reader.close(flush=False)


async def run():
    os.environ.setdefault("YDB_ENDPOINT", "grpc://localhost:2136")
    os.environ.setdefault("YDB_DATABASE", "/local")
    topic_path = "ydb_tech_" + uuid.uuid4().hex
    consumers = ["init", "one", "batch", "commit_one", "commit_batch", "soft", "hard", "outside"]
    config = ydb.DriverConfig(endpoint=os.environ["YDB_ENDPOINT"], database=os.environ["YDB_DATABASE"])
    async with ydb.aio.Driver(config) as driver:
        await driver.wait(timeout=30)
        # [BEGIN topic_create]
        await driver.topic_client.create_topic(
            topic_path,
            supported_codecs=[ydb.TopicCodec.RAW, ydb.TopicCodec.GZIP],  # optional
            min_active_partitions=3,  # optional
        )
        # [END topic_create]
        try:
            await driver.topic_client.alter_topic(topic_path, add_consumers=consumers)
            initialization_topic = topic_path + "_init"
            await driver.topic_client.create_topic(initialization_topic, consumers=["init"])
            try:
                await initialize(initialization_topic, "init")
            finally:
                await driver.topic_client.drop_topic(initialization_topic)
            # [BEGIN topic_alter]
            await driver.topic_client.alter_topic(
                topic_path,
                set_supported_codecs=[ydb.TopicCodec.RAW, ydb.TopicCodec.GZIP],  # optional
                set_min_active_partitions=3,  # optional
            )
            # [END topic_alter]
            # [BEGIN topic_describe]
            info = await driver.topic_client.describe_topic(topic_path)
            print(info)
            # [END topic_describe]
            assert len(info.consumers) == len(consumers)
            await seed(driver, topic_path)
            for consumer in ["one", "batch", "commit_one", "commit_batch", "soft"]:
                await consume(driver, topic_path, consumer)
            await metadata(driver, topic_path + "_metadata")
            await without_consumer(driver, topic_path)
            await expired_batch(driver, topic_path)
            await commit_outside(driver, topic_path)
            await transactions(driver, topic_path + "_tx")
            await autoscaling(driver, topic_path + "_auto")
        finally:
            # [BEGIN topic_drop]
            await driver.topic_client.drop_topic(topic_path)
            # [END topic_drop]


async def start_writer(driver, topic_path):
    # [BEGIN topic_start_writer]
    writer = driver.topic_client.writer(topic_path)
    # [END topic_start_writer]
    return writer


async def seed(driver, topic_path):
    messages = ["buffer-one", "buffer-two"]
    # [BEGIN topic_write]
    writer = driver.topic_client.writer(topic_path)
    await writer.write("mess")
    await writer.write(bytes([1, 2, 3]))
    await writer.write(["mess-1", "mess-2"])
    # [END topic_write]
    try:
        # [BEGIN topic_write_ack]
        for mess in messages:
            await writer.write(mess)

        await writer.flush()

        await writer.write_with_ack(["mess-1", "mess-2"])
        await writer.write_with_ack("message")
        # [END topic_write_ack]
        # [BEGIN topic_write_metadata]
        message = ydb.TopicWriterMessage(data="message-data", metadata_items={"meta-key": "meta-value"})
        await writer.write(message)
        # [END topic_write_metadata]
    finally:
        await writer.close()
    writer = driver.topic_client.writer(topic_path, auto_seqno=False, auto_created_at=False)
    async with writer:
        await writer.write(
            [
                ydb.TopicWriterMessage("asd", seqno=123, created_at=datetime.datetime.now()),
                ydb.TopicWriterMessage(bytes([1, 2, 3]), seqno=124, created_at=datetime.datetime.now()),
            ]
        )
    # codec setup
    writer = driver.topic_client.writer(
        topic_path,
        codec=ydb.TopicCodec.GZIP,
    )
    async with writer:
        await writer.write_with_ack("compressed")


async def consume(driver, topic_path, consumer_name):
    # [BEGIN topic_start_reader]
    reader = driver.topic_client.reader(topic=topic_path, consumer=consumer_name)
    # [END topic_start_reader]
    received = []

    def process(value):
        messages = value.messages if hasattr(value, "messages") else [value]
        received.extend(check_message(message) for message in messages)

    async with reader:
        reader = FiniteReader(reader, received)
        try:
            if consumer_name == "one":
                # [BEGIN topic_read_one]
                while True:
                    message = await reader.receive_message()
                    process(message)
                # [END topic_read_one]
            elif consumer_name == "batch":
                # [BEGIN topic_read_batch]
                while True:
                    batch = await reader.receive_batch()
                    process(batch)
                # [END topic_read_batch]
            elif consumer_name == "commit_one":
                # [BEGIN topic_read_commit]
                while True:
                    message = await reader.receive_message()
                    process(message)
                    reader.commit(message)
                # [END topic_read_commit]
            elif consumer_name == "commit_batch":
                # [BEGIN topic_read_batch_commit]
                while True:
                    batch = await reader.receive_batch()
                    process(batch)
                    reader.commit(batch)
                # [END topic_read_batch_commit]
            elif consumer_name == "soft":
                # [BEGIN topic_soft_stop]
                while True:
                    batch = await reader.receive_batch()
                    process(batch)
                    reader.commit(batch)
                # [END topic_soft_stop]
        except ScenarioComplete:
            pass
    assert collections.Counter(received) == collections.Counter(EXPECTED)


async def metadata(driver, topic_path):
    await driver.topic_client.create_topic(topic_path, consumers=["metadata"])
    try:
        async with driver.topic_client.writer(topic_path) as writer:
            await writer.write_with_ack(
                ydb.TopicWriterMessage("message-data", metadata_items={"meta-key": "meta-value"})
            )
        async with driver.topic_client.reader(topic_path, "metadata") as reader:
            message = await reader.receive_message()
            for meta_key, meta_value in message.metadata_items.items():
                print(f"{meta_key}: {meta_value}")
            assert message.metadata_items["meta-key"] == b"meta-value"
    finally:
        await driver.topic_client.drop_topic(topic_path)


# Consumerless reader handler
class CustomEventHandler(ydb.TopicReaderEvents.EventHandler):
    def on_partition_get_start_offset(self, event: ydb.TopicReaderEvents.OnPartitionGetStartOffsetRequest):
        return ydb.TopicReaderEvents.OnPartitionGetStartOffsetResponse(
            start_offset=0,
        )


async def without_consumer(driver, topic_path):
    reader = driver.topic_client.reader(
        topic=ydb.TopicReaderSelector(
            path=topic_path,
            partitions=[0, 1, 2],
        ),
        consumer=None,
        event_handler=CustomEventHandler(),
    )
    async with reader:
        message = await asyncio.wait_for(reader.receive_message(), 30)
        check_message(message)


async def expired_batch(driver, topic_path):
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

        batch = await reader.receive_batch()
        if process_batch(batch):
            reader.commit(batch)
        # [END topic_hard_stop]
    finally:
        await reader.close(flush=False)
    assert not process_batch(batch)


async def commit_outside(driver, topic_path):
    consumer_name = "outside"
    async with driver.topic_client.reader(topic_path, consumer_name) as reader:
        message = await asyncio.wait_for(reader.receive_message(), 30)
        check_message(message)
        partition_id = message.partition_id
        offset = message.offset + 1
        # [BEGIN topic_commit_outside]
        await driver.topic_client.commit_offset(
            topic_path,
            consumer_name,
            partition_id,
            offset,
            reader.read_session_id,  # опционально: не прерывает активную сессию чтения
        )
        # [END topic_commit_outside]


async def transactions(driver, topic):
    consumer = "transaction"
    message_count = 3
    await driver.topic_client.create_topic(topic, consumers=[consumer, "verify"])
    try:
        # [BEGIN topic_write_tx]
        async with ydb.aio.QuerySessionPool(driver) as session_pool:

            async def callee(tx: ydb.aio.QueryTxContext):
                tx_writer: ydb.TopicTxWriterAsyncIO = driver.topic_client.tx_writer(tx, topic)

                for i in range(message_count):
                    async with await tx.execute(query=f"select {i} as res;") as result_stream:
                        async for result_set in result_stream:
                            message = str(result_set.rows[0]["res"])
                            await tx_writer.write(ydb.TopicWriterMessage(message))
                            print(f"Message {result_set.rows[0]['res']} was written with tx.")

            await session_pool.retry_tx_async(callee)
        # [END topic_write_tx]
        async with driver.topic_client.reader(topic, "verify") as verifier:
            payloads = []
            while len(payloads) < message_count:
                batch = await asyncio.wait_for(verifier.receive_batch(), 30)
                payloads.extend(message.data for message in batch.messages)
            assert payloads == [b"0", b"1", b"2"]
        # [BEGIN topic_read_tx]
        async with driver.topic_client.reader(topic, consumer) as reader:
            async with ydb.aio.QuerySessionPool(driver) as session_pool:
                for _ in range(message_count):

                    async def callee(tx: ydb.aio.QueryTxContext):
                        batch = await reader.receive_batch_with_tx(tx, max_messages=1)
                        print(f"Message {batch.messages[0].data.decode()} was read with tx.")

                    await session_pool.retry_tx_async(callee)
        # [END topic_read_tx]
    finally:
        await driver.topic_client.drop_topic(topic)


async def autoscaling(driver, topic):
    consumer = "auto"
    print("Creating autoscaling topic", flush=True)
    # [BEGIN topic_autoscale_create]
    await driver.topic_client.create_topic(
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
    print("Autoscaling topic created", flush=True)
    topic_path = topic
    try:
        await driver.topic_client.alter_topic(
            topic_path,
            alter_auto_partitioning_settings=ydb.TopicAlterAutoPartitioningSettings(
                set_strategy=ydb.TopicAutoPartitioningStrategy.SCALE_UP,
                set_up_utilization_percent=80,
                set_down_utilization_percent=20,
                set_stabilization_window=datetime.timedelta(seconds=300),
            ),
        )
        async with driver.topic_client.writer(topic) as writer:
            await writer.write_with_ack("auto")
        reader = driver.topic_client.reader(
            topic,
            consumer,
            auto_partitioning_support=True,  # Full support is enabled
        )
        async with reader:
            message = await asyncio.wait_for(reader.receive_message(), 30)
            assert message.data == b"auto"
        reader = driver.topic_client.reader(
            topic,
            consumer,
            auto_partitioning_support=False,  # Compatibility mode is enabled
        )
        async with reader:
            message = await asyncio.wait_for(reader.receive_message(), 30)
            assert message.data == b"auto"
    finally:
        await driver.topic_client.drop_topic(topic)


if __name__ == "__main__":
    faulthandler.dump_traceback_later(45, repeat=True)
    asyncio.run(run())
