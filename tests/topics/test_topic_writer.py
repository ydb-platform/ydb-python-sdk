from __future__ import annotations
from typing import List

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
            ret = await writer.write_with_ack(ydb.TopicWriterMessage(data="123".encode(), seqno=5))
            assert ret.offset == 0

        async with driver.topic_client.writer(
            topic_path,
            producer_id="test",
        ) as writer2:
            init_info = await writer2.wait_init()
            assert init_info.last_seqno == 5

    async def test_link_to_client(self, driver, topic_path, topic_consumer):
        writer = driver.topic_client.writer(topic_path)
        assert writer._parent is driver.topic_client

    async def test_random_producer_id(self, driver: ydb.aio.Driver, topic_path, topic_reader: ydb.TopicReaderAsyncIO):
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
                await writer.write(ydb.TopicWriterMessage(data=f"msg-{i}", seqno=last_seqno))

        async with driver.topic_client.writer(
            topic_path,
            producer_id="test",
        ) as writer:
            init_info = await writer.wait_init()
            assert init_info.last_seqno == last_seqno

    async def test_write_multi_message_with_ack(
        self, driver: ydb.aio.Driver, topic_path, topic_reader: ydb.TopicReaderAsyncIO
    ):
        async with driver.topic_client.writer(topic_path) as writer:
            res1, res2 = await writer.write_with_ack(
                [
                    ydb.TopicWriterMessage(data="123".encode()),
                    ydb.TopicWriterMessage(data="456".encode()),
                ]
            )
            assert res1.offset == 0
            assert res2.offset == 1

        batch = await topic_reader.receive_batch()

        assert batch.messages[0].offset == 0
        assert batch.messages[0].seqno == 1
        assert batch.messages[0].data == "123".encode()

        # remove second recieve batch when implement batching
        # https://github.com/ydb-platform/ydb-python-sdk/issues/142
        batch = await topic_reader.receive_batch()
        assert batch.messages[0].offset == 1
        assert batch.messages[0].seqno == 2
        assert batch.messages[0].data == "456".encode()

    @pytest.mark.parametrize(
        "codec",
        [
            ydb.TopicCodec.RAW,
            ydb.TopicCodec.GZIP,
            None,
        ],
    )
    async def test_write_encoded(self, driver: ydb.Driver, topic_path: str, codec):
        async with driver.topic_client.writer(topic_path, codec=codec) as writer:
            await writer.write("a" * 1000)
            await writer.write("b" * 1000)
            await writer.write("c" * 1000)


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

    def test_link_to_client(self, driver_sync, topic_path, topic_consumer):
        writer = driver_sync.topic_client.writer(topic_path)
        assert writer._parent is driver_sync.topic_client

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

    def test_write_multi_message_with_ack(
        self, driver_sync: ydb.Driver, topic_path, topic_reader_sync: ydb.TopicReader
    ):
        with driver_sync.topic_client.writer(topic_path) as writer:
            writer.write_with_ack(
                [
                    ydb.TopicWriterMessage(data="123".encode()),
                    ydb.TopicWriterMessage(data="456".encode()),
                ]
            )

        batch = topic_reader_sync.receive_batch()

        assert batch.messages[0].offset == 0
        assert batch.messages[0].seqno == 1
        assert batch.messages[0].data == "123".encode()

        # remove second recieve batch when implement batching
        # https://github.com/ydb-platform/ydb-python-sdk/issues/142
        batch = topic_reader_sync.receive_batch()
        assert batch.messages[0].offset == 1
        assert batch.messages[0].seqno == 2
        assert batch.messages[0].data == "456".encode()

    @pytest.mark.parametrize(
        "codec",
        [
            ydb.TopicCodec.RAW,
            ydb.TopicCodec.GZIP,
            None,
        ],
    )
    def test_write_encoded(self, driver_sync: ydb.Driver, topic_path: str, codec):
        with driver_sync.topic_client.writer(topic_path, codec=codec) as writer:
            writer.write("a" * 1000)
            writer.write("b" * 1000)
            writer.write("c" * 1000)

    def test_start_many_sync_writers_in_parallel(self, driver_sync: ydb.Driver, topic_path):
        target_count = 100
        writers = []  # type: List[ydb.TopicWriter]
        for i in range(target_count):
            writer = driver_sync.topic_client.writer(topic_path)
            writers.append(writer)

        for i, writer in enumerate(writers):
            writer.write(str(i))

        for writer in writers:
            writer.close()
