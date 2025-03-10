import asyncio
from asyncio import wait_for
import pytest
import ydb


@pytest.mark.skip("Not implemented yet.")
@pytest.mark.asyncio
class TestTopicTransactionalReader:
    async def test_commit(self, driver: ydb.aio.Driver, topic_with_messages, topic_consumer):
        async with driver.topic_client.reader(topic_with_messages, topic_consumer) as reader:
            async with ydb.aio.QuerySessionPool(driver) as pool:

                async def callee(tx: ydb.aio.QueryTxContext):
                    batch = await wait_for(reader.receive_batch_with_tx(tx, max_messages=1), 1)
                    assert len(batch) == 1
                    assert batch[0].data.decode() == "123"

                await pool.retry_tx_async(callee)

                msg = await wait_for(reader.receive_message(), 1)
                assert msg.data.decode() == "456"

    async def test_rollback(self, driver: ydb.aio.Driver, topic_with_messages, topic_consumer):
        async with driver.topic_client.reader(topic_with_messages, topic_consumer) as reader:
            async with ydb.aio.QuerySessionPool(driver) as pool:

                async def callee(tx: ydb.aio.QueryTxContext):
                    batch = await wait_for(reader.receive_batch_with_tx(tx, max_messages=1), 1)
                    assert len(batch) == 1
                    assert batch[0].data.decode() == "123"

                    await tx.rollback()

                await pool.retry_tx_async(callee)

                msg = await wait_for(reader.receive_message(), 1)
                assert msg.data.decode() == "123"


@pytest.mark.skip("Not implemented yet.")
class TestTopicTransactionalWriter:
    async def test_commit(self, driver: ydb.aio.Driver, topic_path, topic_reader: ydb.TopicReaderAsyncIO):
        async with ydb.aio.QuerySessionPool(driver) as pool:

            async def callee(tx: ydb.aio.QueryTxContext):
                tx_writer = driver.topic_client.tx_writer(tx, topic_path)
                tx_writer.write(ydb.TopicWriterMessage(data="123".encode()))

            await pool.retry_tx_async(callee)

        msg = await wait_for(topic_reader.receive_message(), 0.1)
        assert msg.data.decode() == "123"

    async def test_rollback(self, driver: ydb.aio.Driver, topic_path, topic_reader: ydb.TopicReaderAsyncIO):
        async with ydb.aio.QuerySessionPool(driver) as pool:

            async def callee(tx: ydb.aio.QueryTxContext):
                tx_writer = driver.topic_client.tx_writer(tx, topic_path)
                tx_writer.write(ydb.TopicWriterMessage(data="123".encode()))

                await tx.rollback()

            await pool.retry_tx_async(callee)

        with pytest.raises(asyncio.TimeoutError):
            await wait_for(topic_reader.receive_message(), 0.1)
