import pytest

import ydb


@pytest.mark.asyncio
class TestTopicReaderAsyncIO:
    async def test_read_batch(self, driver, topic_with_messages, topic_consumer):
        reader = driver.topic_client.reader(topic_with_messages, topic_consumer)
        batch = await reader.receive_batch()

        assert batch is not None
        assert len(batch.messages) > 0

        await reader.close()

    async def test_link_to_client(self, driver, topic_path, topic_consumer):
        reader = driver.topic_client.reader(topic_path, topic_consumer)
        assert reader._parent is driver.topic_client

    async def test_read_message(self, driver, topic_with_messages, topic_consumer):
        reader = driver.topic_client.reader(topic_with_messages, topic_consumer)
        msg = await reader.receive_message()

        assert msg is not None
        assert msg.seqno

        await reader.close()

    async def test_read_and_commit_with_close_reader(self, driver, topic_with_messages, topic_consumer):
        async with driver.topic_client.reader(topic_with_messages, topic_consumer) as reader:
            message = await reader.receive_message()
            reader.commit(message)

        async with driver.topic_client.reader(topic_with_messages, topic_consumer) as reader:
            message2 = await reader.receive_message()
            assert message != message2

    async def test_read_and_commit_with_ack(self, driver, topic_with_messages, topic_consumer):
        reader = driver.topic_client.reader(topic_with_messages, topic_consumer)
        batch = await reader.receive_batch()
        await reader.commit_with_ack(batch)

        reader = driver.topic_client.reader(topic_with_messages, topic_consumer)
        batch2 = await reader.receive_batch()
        assert batch.messages[0] != batch2.messages[0]

        await reader.close()

    async def test_read_compressed_messages(self, driver, topic_path, topic_consumer):
        async with driver.topic_client.writer(topic_path, codec=ydb.TopicCodec.GZIP) as writer:
            await writer.write("123")

        async with driver.topic_client.reader(topic_path, topic_consumer) as reader:
            batch = await reader.receive_batch()
            assert batch.messages[0].data.decode() == "123"

    async def test_read_custom_encoded(self, driver, topic_path, topic_consumer):
        codec = 10001

        def encode(b: bytes):
            return bytes(reversed(b))

        def decode(b: bytes):
            return bytes(reversed(b))

        async with driver.topic_client.writer(topic_path, codec=codec, encoders={codec: encode}) as writer:
            await writer.write("123")

        async with driver.topic_client.reader(topic_path, topic_consumer, decoders={codec: decode}) as reader:
            batch = await reader.receive_batch()
            assert batch.messages[0].data.decode() == "123"

    async def test_read_from_two_topics(self, driver, topic_path, topic2_path, topic_consumer):
        async with driver.topic_client.writer(topic_path) as writer:
            await writer.write("1")
            await writer.flush()

        async with driver.topic_client.writer(topic2_path) as writer:
            await writer.write("2")
            await writer.flush()

        messages = []
        async with driver.topic_client.reader(
            [
                topic_path,
                ydb.TopicReaderSelector(path=topic2_path),
            ],
            consumer=topic_consumer,
        ) as reader:
            for _ in range(2):
                message = await reader.receive_message()
                messages.append(message)

        messages = [message.data.decode() for message in messages]
        messages.sort()
        assert messages == ["1", "2"]


class TestTopicReaderSync:
    def test_read_batch(self, driver_sync, topic_with_messages, topic_consumer):
        reader = driver_sync.topic_client.reader(topic_with_messages, topic_consumer)
        batch = reader.receive_batch()

        assert batch is not None
        assert len(batch.messages) > 0

        reader.close()

    def test_link_to_client(self, driver_sync, topic_path, topic_consumer):
        reader = driver_sync.topic_client.reader(topic_path, topic_consumer)
        assert reader._parent is driver_sync.topic_client

    def test_read_message(self, driver_sync, topic_with_messages, topic_consumer):
        reader = driver_sync.topic_client.reader(topic_with_messages, topic_consumer)
        msg = reader.receive_message()

        assert msg is not None
        assert msg.seqno

        reader.close()

    def test_read_and_commit_with_close_reader(self, driver_sync, topic_with_messages, topic_consumer):
        with driver_sync.topic_client.reader(topic_with_messages, topic_consumer) as reader:
            message = reader.receive_message()
            reader.commit(message)

        with driver_sync.topic_client.reader(topic_with_messages, topic_consumer) as reader:
            message2 = reader.receive_message()
            assert message != message2

    def test_read_and_commit_with_ack(self, driver_sync, topic_with_messages, topic_consumer):
        reader = driver_sync.topic_client.reader(topic_with_messages, topic_consumer)
        batch = reader.receive_batch()
        reader.commit_with_ack(batch)

        reader = driver_sync.topic_client.reader(topic_with_messages, topic_consumer)
        batch2 = reader.receive_batch()
        assert batch.messages[0] != batch2.messages[0]

    def test_read_compressed_messages(self, driver_sync, topic_path, topic_consumer):
        with driver_sync.topic_client.writer(topic_path, codec=ydb.TopicCodec.GZIP) as writer:
            writer.write("123")

        with driver_sync.topic_client.reader(topic_path, topic_consumer) as reader:
            batch = reader.receive_batch()
            assert batch.messages[0].data.decode() == "123"

    def test_read_custom_encoded(self, driver_sync, topic_path, topic_consumer):
        codec = 10001

        def encode(b: bytes):
            return bytes(reversed(b))

        def decode(b: bytes):
            return bytes(reversed(b))

        with driver_sync.topic_client.writer(topic_path, codec=codec, encoders={codec: encode}) as writer:
            writer.write("123")

        with driver_sync.topic_client.reader(topic_path, topic_consumer, decoders={codec: decode}) as reader:
            batch = reader.receive_batch()
            assert batch.messages[0].data.decode() == "123"
