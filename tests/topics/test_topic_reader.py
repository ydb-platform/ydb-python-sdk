import asyncio

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
        await reader.wait_message()
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

    async def test_error_unknown_codec(self, driver, topic_path, topic_consumer):
        codec = 10001

        def encode(b: bytes):
            return bytes(reversed(b))

        async with driver.topic_client.writer(topic_path, codec=codec, encoders={codec: encode}) as writer:
            await writer.write("123")

        async with driver.topic_client.reader(topic_path, topic_consumer) as reader:
            with pytest.raises(ydb.TopicReaderUnexpectedCodecError):
                await asyncio.wait_for(reader.receive_batch(), timeout=5)

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


@pytest.mark.asyncio
class TestBugFixesAsync:
    async def test_issue_297_bad_handle_stop_partition(
        self, driver, topic_consumer, topic_with_two_partitions_path: str
    ):
        async def wait(fut):
            return await asyncio.wait_for(fut, timeout=10)

        topic = topic_with_two_partitions_path  # type: str

        async with driver.topic_client.writer(topic, partition_id=0) as writer:
            await writer.write_with_ack("00")

        async with driver.topic_client.writer(topic, partition_id=1) as writer:
            await writer.write_with_ack("01")

        # Start first reader and receive messages from both partitions
        reader0 = driver.topic_client.reader(topic, consumer=topic_consumer)
        await wait(reader0.receive_message())
        await wait(reader0.receive_message())

        # Start second reader for same topic, same consumer, partition 1
        reader1 = driver.topic_client.reader(topic, consumer=topic_consumer)

        # receive uncommited message
        await reader1.receive_message()

        # write one message for every partition
        async with driver.topic_client.writer(topic, partition_id=0) as writer:
            await writer.write_with_ack("10")
        async with driver.topic_client.writer(topic, partition_id=1) as writer:
            await writer.write_with_ack("11")

        msg0 = await wait(reader0.receive_message())
        msg1 = await wait(reader1.receive_message())

        datas = [msg0.data.decode(), msg1.data.decode()]
        datas.sort()

        assert datas == ["10", "11"]
