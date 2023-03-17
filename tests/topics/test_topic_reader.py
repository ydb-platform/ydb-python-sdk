import pytest

import ydb


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

        await reader.close()

    async def test_read_compressed_messages(self, driver, topic_path, topic_consumer):
        async with driver.topic_client.writer(
            topic_path, codec=ydb.TopicCodec.GZIP
        ) as writer:
            await writer.write("123")

        async with driver.topic_client.reader(topic_consumer, topic_path) as reader:
            batch = await reader.receive_batch()
            assert batch.messages[0].data.decode() == "123"

    async def test_read_custom_encoded(self, driver, topic_path, topic_consumer):
        codec = 10001

        def encode(b: bytes):
            return bytes(reversed(b))

        def decode(b: bytes):
            return bytes(reversed(b))

        async with driver.topic_client.writer(
            topic_path, codec=codec, encoders={codec: encode}
        ) as writer:
            await writer.write("123")

        async with driver.topic_client.reader(
            topic_consumer, topic_path, decoders={codec: decode}
        ) as reader:
            batch = await reader.receive_batch()
            assert batch.messages[0].data.decode() == "123"


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

    def test_read_compressed_messages(self, driver_sync, topic_path, topic_consumer):
        with driver_sync.topic_client.writer(
            topic_path, codec=ydb.TopicCodec.GZIP
        ) as writer:
            writer.write("123")

        with driver_sync.topic_client.reader(topic_consumer, topic_path) as reader:
            batch = reader.receive_batch()
            assert batch.messages[0].data.decode() == "123"

    def test_read_custom_encoded(self, driver_sync, topic_path, topic_consumer):
        codec = 10001

        def encode(b: bytes):
            return bytes(reversed(b))

        def decode(b: bytes):
            return bytes(reversed(b))

        with driver_sync.topic_client.writer(
            topic_path, codec=codec, encoders={codec: encode}
        ) as writer:
            writer.write("123")

        with driver_sync.topic_client.reader(
            topic_consumer, topic_path, decoders={codec: decode}
        ) as reader:
            batch = reader.receive_batch()
            assert batch.messages[0].data.decode() == "123"
