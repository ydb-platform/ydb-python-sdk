import os.path

import pytest

import ydb
from ydb import issues


@pytest.mark.asyncio
class TestTopicClientControlPlaneAsyncIO:
    async def test_create_topic(self, driver, database):
        client = driver.topic_client

        topic_path = database + "/my-test-topic"

        await client.create_topic(topic_path)

        with pytest.raises(issues.SchemeError):
            # double create is ok - try create topic with bad path
            await client.create_topic(database)

    async def test_drop_topic(self, driver, topic_path):
        client = driver.topic_client

        await client.drop_topic(topic_path)

        with pytest.raises(issues.SchemeError):
            await client.drop_topic(topic_path)

    async def test_describe_topic(self, driver, topic_path: str, topic_consumer):
        res = await driver.topic_client.describe_topic(topic_path)

        assert res.self.name == os.path.basename(topic_path)

        has_consumer = False
        for consumer in res.consumers:
            assert consumer.consumer_stats is not None
            for stat in ["min_partitions_last_read_time", "max_read_time_lag", "max_write_time_lag", "bytes_read"]:
                assert getattr(consumer.consumer_stats, stat, None) is not None
            if consumer.name == topic_consumer:
                has_consumer = True
                break

        assert has_consumer

    async def test_describe_consumer(self, driver, topic_path: str, topic_consumer):
        res = await driver.topic_client.describe_consumer(topic_path, topic_consumer)

        assert res.self.name.endswith(topic_consumer)
        assert res.consumer.name == topic_consumer
        assert res.partitions is not None

    async def test_describe_not_existed_consumer(self, driver, topic_path: str):
        with pytest.raises(issues.SchemeError):
            await driver.topic_client.describe_consumer(topic_path, "not-existed-consumer")

    async def test_describe_consumer_with_stats(self, driver, topic_path: str, topic_consumer):
        res = await driver.topic_client.describe_consumer(topic_path, topic_consumer, include_stats=True)

        assert res.self.name.endswith(topic_consumer)
        assert res.consumer.name == topic_consumer
        assert res.partitions is not None
        for partition in res.partitions:
            assert partition.partition_stats is not None
            assert partition.partition_consumer_stats is not None

    async def test_describe_consumer_with_location(self, driver, topic_path: str, topic_consumer):
        res = await driver.topic_client.describe_consumer(topic_path, topic_consumer, include_location=True)

        assert res.consumer.name == topic_consumer
        assert res.partitions is not None
        assert len(res.partitions) > 0
        for partition in res.partitions:
            assert partition.partition_location is not None
            assert hasattr(partition.partition_location, "node_id")
            assert hasattr(partition.partition_location, "generation")

    async def test_describe_consumer_offsets(self, driver, topic_with_messages, topic_consumer):
        # topic_with_messages has 4 messages written (offsets 0, 1, 2, 3)
        # Read and commit 2 messages
        async with driver.topic_client.reader(topic_with_messages, topic_consumer) as reader:
            msg1 = await reader.receive_message()
            await reader.commit_with_ack(msg1)
            msg2 = await reader.receive_message()
            await reader.commit_with_ack(msg2)

        # Check consumer stats
        res = await driver.topic_client.describe_consumer(topic_with_messages, topic_consumer, include_stats=True)

        assert len(res.partitions) > 0
        partition = res.partitions[0]

        # Verify partition stats
        assert partition.partition_stats is not None
        assert partition.partition_stats.partition_end == 4  # 4 messages written

        # Verify consumer stats
        assert partition.partition_consumer_stats is not None
        assert partition.partition_consumer_stats.committed_offset == 2  # 2 messages committed

    async def test_alter_not_existed_topic(self, driver, topic_path):
        client = driver.topic_client

        with pytest.raises(issues.SchemeError):
            await client.alter_topic(topic_path + "-not-exist")

    async def test_alter_existed_topic(self, driver, topic_path):
        client = driver.topic_client

        topic_before = await client.describe_topic(topic_path)

        target_min_active_partitions = topic_before.min_active_partitions + 1
        await client.alter_topic(topic_path, set_min_active_partitions=target_min_active_partitions)

        topic_after = await client.describe_topic(topic_path)
        assert topic_after.min_active_partitions == target_min_active_partitions

    async def test_alter_auto_partitioning_settings(self, driver, topic_path):
        client = driver.topic_client

        topic_before = await client.describe_topic(topic_path)

        expected = topic_before.auto_partitioning_settings

        expected.strategy = ydb.TopicAutoPartitioningStrategy.SCALE_UP

        await client.alter_topic(
            topic_path,
            alter_auto_partitioning_settings=ydb.TopicAlterAutoPartitioningSettings(
                set_strategy=ydb.TopicAutoPartitioningStrategy.SCALE_UP,
            ),
        )

        topic_after = await client.describe_topic(topic_path)

        assert topic_after.auto_partitioning_settings == expected

        expected.up_utilization_percent = 88

        await client.alter_topic(
            topic_path,
            alter_auto_partitioning_settings=ydb.TopicAlterAutoPartitioningSettings(
                set_up_utilization_percent=88,
            ),
        )

        topic_after = await client.describe_topic(topic_path)

        assert topic_after.auto_partitioning_settings == expected


class TestTopicClientControlPlane:
    def test_create_topic(self, driver_sync, database):
        client = driver_sync.topic_client

        topic_path = database + "/my-test-topic"

        client.create_topic(topic_path)

        with pytest.raises(issues.SchemeError):
            # double create is ok - try create topic with bad path
            client.create_topic(database)

    def test_drop_topic(self, driver_sync, topic_path):
        client = driver_sync.topic_client

        client.drop_topic(topic_path)

        with pytest.raises(issues.SchemeError):
            client.drop_topic(topic_path)

    def test_describe_topic(self, driver_sync, topic_path: str, topic_consumer):
        res = driver_sync.topic_client.describe_topic(topic_path)

        assert res.self.name == os.path.basename(topic_path)

        has_consumer = False
        for consumer in res.consumers:
            if consumer.name == topic_consumer:
                has_consumer = True
                break

        assert has_consumer

    def test_describe_consumer(self, driver_sync, topic_path: str, topic_consumer):
        res = driver_sync.topic_client.describe_consumer(topic_path, topic_consumer)

        assert res.self.name.endswith(topic_consumer)
        assert res.consumer.name == topic_consumer
        assert res.partitions is not None

    def test_describe_not_existed_consumer(self, driver_sync, topic_path: str):
        with pytest.raises(issues.SchemeError):
            driver_sync.topic_client.describe_consumer(topic_path, "not-existed-consumer")

    def test_describe_consumer_with_stats(self, driver_sync, topic_path: str, topic_consumer):
        res = driver_sync.topic_client.describe_consumer(topic_path, topic_consumer, include_stats=True)

        assert res.self.name.endswith(topic_consumer)
        assert res.consumer.name == topic_consumer
        assert res.partitions is not None
        for partition in res.partitions:
            assert partition.partition_stats is not None
            assert partition.partition_consumer_stats is not None

    def test_describe_consumer_with_location(self, driver_sync, topic_path: str, topic_consumer):
        res = driver_sync.topic_client.describe_consumer(topic_path, topic_consumer, include_location=True)

        assert res.consumer.name == topic_consumer
        assert res.partitions is not None
        assert len(res.partitions) > 0
        for partition in res.partitions:
            assert partition.partition_location is not None
            assert hasattr(partition.partition_location, "node_id")
            assert hasattr(partition.partition_location, "generation")

    def test_describe_consumer_offsets(self, driver_sync, topic_with_messages, topic_consumer):
        # topic_with_messages has 4 messages written (offsets 0, 1, 2, 3)
        # Read and commit 2 messages
        with driver_sync.topic_client.reader(topic_with_messages, topic_consumer) as reader:
            msg1 = reader.receive_message()
            reader.commit(msg1)
            msg2 = reader.receive_message()
            reader.commit(msg2)

        # Check consumer stats
        res = driver_sync.topic_client.describe_consumer(topic_with_messages, topic_consumer, include_stats=True)

        assert len(res.partitions) > 0
        partition = res.partitions[0]

        # Verify partition stats
        assert partition.partition_stats is not None
        assert partition.partition_stats.partition_end == 4  # 4 messages written

        # Verify consumer stats
        assert partition.partition_consumer_stats is not None
        assert partition.partition_consumer_stats.committed_offset == 2  # 2 messages committed

    def test_alter_not_existed_topic(self, driver_sync, topic_path):
        client = driver_sync.topic_client

        with pytest.raises(issues.SchemeError):
            client.alter_topic(topic_path + "-not-exist")

    def test_alter_existed_topic(self, driver_sync, topic_path):
        client = driver_sync.topic_client

        topic_before = client.describe_topic(topic_path)

        target_min_active_partitions = topic_before.min_active_partitions + 1
        client.alter_topic(topic_path, set_min_active_partitions=target_min_active_partitions)

        topic_after = client.describe_topic(topic_path)
        assert topic_after.min_active_partitions == target_min_active_partitions
