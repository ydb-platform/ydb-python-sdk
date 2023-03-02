import pytest


@pytest.mark.asyncio
class TestTopicReaderAsyncIO:
    async def test_read_message(
        self, driver, topic_path, topic_with_messages, topic_consumer
    ):
        reader = driver.topic_client.reader(topic_consumer, topic_path)

        assert await reader.receive_batch() is not None
        await reader.close()


class TestTopicReaderSync:
    def test_read_message(
        self, driver_sync, topic_path, topic_with_messages, topic_consumer
    ):
        reader = driver_sync.topic_client.reader(topic_consumer, topic_path)

        assert reader.receive_batch() is not None
        reader.close()
