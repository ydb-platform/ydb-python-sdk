import pytest


@pytest.mark.asyncio
class TestTopicWriterAsyncIO:
    async def test_read_message(
        self, driver, topic_path, topic_with_messages, topic_consumer
    ):
        reader = driver.topic_client.topic_reader(topic_consumer, topic_path)

        assert await reader.receive_batch() is not None
