import pytest

import ydb.aio


@pytest.mark.asyncio
class TestTopicWriterAsyncIO:
    async def test_send_message(self, driver: ydb.aio.Driver, topic_path):
        writer = driver.topic_client.writer(topic_path, producer_id="test")
        await writer.write(ydb.TopicWriterMessage(data="123".encode()))
        await writer.close()

    async def test_wait_last_seqno(self, driver: ydb.aio.Driver, topic_path):
        async with driver.topic_client.writer(
            topic_path,
            producer_id="test",
            auto_seqno=False,
        ) as writer:
            await writer.write_with_ack(
                ydb.TopicWriterMessage(data="123".encode(), seqno=5)
            )

        async with driver.topic_client.writer(
            topic_path,
            producer_id="test",
        ) as writer2:
            init_info = await writer2.wait_init()
            assert init_info.last_seqno == 5

    async def test_random_producer_id(
        self, driver: ydb.aio.Driver, topic_path, topic_reader: ydb.TopicReaderAsyncIO
    ):
        async with driver.topic_client.writer(topic_path) as writer:
            await writer.write(ydb.TopicWriterMessage(data="123".encode()))
        async with driver.topic_client.writer(topic_path) as writer:
            await writer.write(ydb.TopicWriterMessage(data="123".encode()))

        batch1 = await topic_reader.receive_batch()
        batch2 = await topic_reader.receive_batch()

        assert batch1.messages[0].producer_id != batch2.messages[0].producer_id

    async def test_auto_flush_on_close(self, driver: ydb.aio.Driver, topic_path):
        async with driver.topic_client.writer(
            topic_path,
            producer_id="test",
            auto_seqno=False,
        ) as writer:
            last_seqno = 0
            for i in range(10):
                last_seqno = i + 1
                await writer.write(
                    ydb.TopicWriterMessage(data=f"msg-{i}", seqno=last_seqno)
                )

        async with driver.topic_client.writer(
            topic_path,
            producer_id="test",
        ) as writer:
            init_info = await writer.wait_init()
            assert init_info.last_seqno == last_seqno


class TestTopicWriterSync:
    def test_send_message(self, driver_sync: ydb.Driver, topic_path):
        writer = driver_sync.topic_client.writer(topic_path, producer_id="test")
        writer.write(ydb.TopicWriterMessage(data="123".encode()))
        writer.close()

    def test_wait_last_seqno(self, driver_sync: ydb.Driver, topic_path):
        with driver_sync.topic_client.writer(
            topic_path,
            producer_id="test",
            auto_seqno=False,
        ) as writer:
            writer.write_with_ack(ydb.TopicWriterMessage(data="123".encode(), seqno=5))

        with driver_sync.topic_client.writer(
            topic_path,
            producer_id="test",
        ) as writer2:
            init_info = writer2.wait_init()
            assert init_info.last_seqno == 5

    def test_auto_flush_on_close(self, driver_sync: ydb.Driver, topic_path):
        with driver_sync.topic_client.writer(
            topic_path,
            producer_id="test",
            auto_seqno=False,
        ) as writer:
            last_seqno = 0
            for i in range(10):
                last_seqno = i + 1
                writer.write(ydb.TopicWriterMessage(data=f"msg-{i}", seqno=last_seqno))

        with driver_sync.topic_client.writer(
            topic_path,
            producer_id="test",
        ) as writer:
            init_info = writer.wait_init()
            assert init_info.last_seqno == last_seqno

    def test_random_producer_id(
        self,
        driver_sync: ydb.aio.Driver,
        topic_path,
        topic_reader_sync: ydb.TopicReader,
    ):
        with driver_sync.topic_client.writer(topic_path) as writer:
            writer.write(ydb.TopicWriterMessage(data="123".encode()))
        with driver_sync.topic_client.writer(topic_path) as writer:
            writer.write(ydb.TopicWriterMessage(data="123".encode()))

        batch1 = topic_reader_sync.receive_batch()
        batch2 = topic_reader_sync.receive_batch()

        assert batch1.messages[0].producer_id != batch2.messages[0].producer_id
