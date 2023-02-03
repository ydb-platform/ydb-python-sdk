import pytest

from ydb._topic_reader.topic_reader_asyncio import PublicAsyncIOReader
from ydb import TopicReaderSettings


@pytest.mark.asyncio
class TestTopicWriterAsyncIO:
    async def test_read_message(self, driver, topic_path, topic_with_messages, topic_consumer):
        reader = PublicAsyncIOReader(driver, TopicReaderSettings(
            consumer=topic_consumer,
            topic=topic_path,
        ))
        await reader.wait_messages()

        assert reader.receive_batch() is not None
