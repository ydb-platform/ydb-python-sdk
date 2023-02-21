import asyncio

import pytest

import ydb.aio


@pytest.mark.asyncio
class TestTopicWriterAsyncIO:
    async def test_send_message(
        self, driver: ydb.aio.Driver, topic_path, topic_consumer
    ):
        seqno = 10
        writer = driver.topic_client.topic_writer(
            topic_path,
            producer_and_message_group_id="test-producer-id",
            auto_seqno=False,
        )
        await writer.write(ydb.TopicWriterMessage(seqno=seqno, data="123".encode()))

        reader = driver.topic_client.topic_reader(topic_consumer, topic_path)
        batch = await asyncio.wait_for(reader.receive_batch(), timeout=60)
        assert batch.messages[0].seqno == seqno

        await writer.close()

    async def test_wait_last_seqno(self, driver: ydb.aio.Driver, topic_path):
        async with driver.topic_client.topic_writer(
            topic_path,
            producer_and_message_group_id="test",
            auto_seqno=False,
        ) as writer:
            await writer.write_with_ack(
                ydb.TopicWriterMessage(data="123".encode(), seqno=5)
            )

        async with driver.topic_client.topic_writer(
            topic_path,
            producer_and_message_group_id="test",
            get_last_seqno=True,
        ) as writer2:
            init_info = await writer2.wait_init()
            assert init_info.last_seqno == 5

    async def test_auto_flush_on_close(self, driver: ydb.aio.Driver, topic_path):
        async with driver.topic_client.topic_writer(
            topic_path,
            producer_and_message_group_id="test",
            auto_seqno=False,
        ) as writer:
            last_seqno = 0
            for i in range(10):
                last_seqno = i + 1
                await writer.write(
                    ydb.TopicWriterMessage(data=f"msg-{i}", seqno=last_seqno)
                )

        async with driver.topic_client.topic_writer(
            topic_path,
            producer_and_message_group_id="test",
            get_last_seqno=True,
        ) as writer:
            init_info = await writer.wait_init()
            assert init_info.last_seqno == last_seqno


class TestTopicWriterSync:
    def test_send_message(self, driver_sync: ydb.Driver, topic_path, topic_consumer):
        seqno = 10
        writer = driver_sync.topic_client.topic_writer(
            topic_path,
            producer_and_message_group_id="test-producer-id",
            auto_seqno=False,
        )
        writer.write(
            ydb.TopicWriterMessage(seqno=seqno, data="123".encode()),
        )

        # todo check message by read

    def test_wait_last_seqno(self, driver_sync: ydb.Driver, topic_path):
        with driver_sync.topic_client.topic_writer(
            topic_path,
            producer_and_message_group_id="test",
            auto_seqno=False,
        ) as writer:
            writer.write_with_ack(ydb.TopicWriterMessage(data="123".encode(), seqno=5))

        with driver_sync.topic_client.topic_writer(
            topic_path,
            producer_and_message_group_id="test",
            get_last_seqno=True,
        ) as writer2:
            init_info = writer2.wait_init()
            assert init_info.last_seqno == 5
