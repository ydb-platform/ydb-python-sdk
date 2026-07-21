"""Examples for the topic multi-partition writer (write-by-key).

The multi-writer routes each message to a partition by its ``key``, keeping every
message with the same key on the same partition (per-key ordering). By default it
picks a partition chooser automatically: the key-range chooser for
auto-partitioned topics, the Kafka-hash chooser otherwise.
"""

import asyncio

import ydb


def write_by_key_sync(db: ydb.Driver, topic_path: str):
    with db.topic_client.multiwriter(topic_path, producer_id_prefix="my-app") as writer:
        writer.write(ydb.TopicWriterMessage(data="event-a", key="user-42"))
        writer.write(ydb.TopicWriterMessage(data="event-b", key="user-7"))
        # messages with the same key always land on the same partition, in order
        writer.write(ydb.TopicWriterMessage(data="event-c", key="user-42"))
        writer.flush()


async def write_by_key_async(db: ydb.aio.Driver, topic_path: str):
    async with db.topic_client.multiwriter(topic_path, producer_id_prefix="my-app") as writer:
        await writer.write(ydb.TopicWriterMessage(data="event-a", key="user-42"))
        # wait for the server ack of a specific message
        await writer.write_with_ack(ydb.TopicWriterMessage(data="event-b", key="user-7"))


def write_by_key_with_explicit_chooser(db: ydb.Driver, topic_path: str):
    # Force the Kafka-compatible hash chooser (murmur2(key) % partitions_count).
    with db.topic_client.multiwriter(
        topic_path,
        partition_chooser=ydb.TopicWriterPartitionByKeyKafka(),
    ) as writer:
        writer.write(ydb.TopicWriterMessage(data="event", key="user-42"))


def run_sync():
    with ydb.Driver(
        connection_string="grpc://localhost:2135?database=/local",
        credentials=ydb.credentials.AnonymousCredentials(),
    ) as db:
        db.wait(timeout=5, fail_fast=True)
        write_by_key_sync(db, "/local/topic")


async def run_async():
    async with ydb.aio.Driver(
        connection_string="grpc://localhost:2135?database=/local",
        credentials=ydb.credentials.AnonymousCredentials(),
    ) as db:
        await db.wait(timeout=5, fail_fast=True)
        await write_by_key_async(db, "/local/topic")


if __name__ == "__main__":
    run_sync()
    asyncio.run(run_async())
