import pytest


@pytest.mark.asyncio
class TestTopicReaderAsyncIO:
    async def test_read_message(
        self, driver, topic_path, topic_with_messages, topic_consumer
    ):
        reader = driver.topic_client.reader(topic_consumer, topic_path)

        assert await reader.receive_batch() is not None
        await reader.close()

    async def test_read_and_commit_message(
        self, driver, topic_path, topic_with_messages, topic_consumer
    ):

        reader = driver.topic_client.reader(topic_consumer, topic_path)
        batch = await reader.receive_batch()
        await reader.commit_with_ack(batch)

        reader = driver.topic_client.reader(topic_consumer, topic_path)
        batch2 = await reader.receive_batch()
        assert batch.messages[0] != batch2.messages[0]


class TestTopicReaderSync:
    def test_read_message(
        self, driver_sync, topic_path, topic_with_messages, topic_consumer
    ):
        reader = driver_sync.topic_client.reader(topic_consumer, topic_path)

        assert reader.receive_batch() is not None
        reader.close()

    def test_read_and_commit_message(
        self, driver_sync, topic_path, topic_with_messages, topic_consumer
    ):
        reader = driver_sync.topic_client.reader(topic_consumer, topic_path)
        batch = reader.receive_batch()
        reader.commit_with_ack(batch)

        reader = driver_sync.topic_client.reader(topic_consumer, topic_path)
        batch2 = reader.receive_batch()
        assert batch.messages[0] != batch2.messages[0]
