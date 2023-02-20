import pytest

import ydb.aio


@pytest.mark.asyncio
class TestTopicWriterAsyncIO:
    async def test_send_message(self, driver: ydb.aio.Driver, topic_path):
        writer = driver.topic_client.topic_writer(
            topic_path, producer_and_message_group_id="test"
        )
        writer.write(ydb.TopicWriterMessage(data="123".encode()))

        # todo check receive mess

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


class TestTopicWriterSync:
    def test_send_message(self, driver_sync: ydb.Driver, topic_path):
        writer = driver_sync.topic_client.topic_writer(
            topic_path, producer_and_message_group_id="test"
        )
        writer.write(ydb.TopicWriterMessage(data="123".encode()))

        # todo check receive mess

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
