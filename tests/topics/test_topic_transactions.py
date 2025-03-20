import asyncio
from asyncio import wait_for
import pytest
import ydb


# @pytest.mark.skip("Not implemented yet.")
@pytest.mark.asyncio
class TestTopicTransactionalReader:
    async def test_commit(self, driver: ydb.aio.Driver, topic_with_messages, topic_consumer):
        async with ydb.aio.QuerySessionPool(driver) as pool:
            async with driver.topic_client.reader(topic_with_messages, topic_consumer) as reader:

                async def callee(tx: ydb.aio.QueryTxContext):
                    batch = await wait_for(reader.receive_batch_with_tx(tx, max_messages=1), 1)
                    assert len(batch.messages) == 1
                    assert batch.messages[0].data.decode() == "123"

                await pool.retry_tx_async(callee)

            async with driver.topic_client.reader(topic_with_messages, topic_consumer) as reader:
                msg = await wait_for(reader.receive_message(), 1)
                assert msg.data.decode() == "456"

    async def test_rollback(self, driver: ydb.aio.Driver, topic_with_messages, topic_consumer):
        async with driver.topic_client.reader(topic_with_messages, topic_consumer) as reader:
            async with ydb.aio.QuerySessionPool(driver) as pool:

                async def callee(tx: ydb.aio.QueryTxContext):
                    batch = await wait_for(reader.receive_batch_with_tx(tx, max_messages=1), 1)
                    assert len(batch.messages) == 1
                    assert batch.messages[0].data.decode() == "123"

                    await tx.rollback()

                await pool.retry_tx_async(callee)

                msg = await wait_for(reader.receive_message(), 1)
                assert msg.data.decode() == "123"


class TestTopicTransactionalWriter:
    async def test_commit(self, driver: ydb.aio.Driver, topic_path, topic_reader: ydb.TopicReaderAsyncIO):
        async with ydb.aio.QuerySessionPool(driver) as pool:

            async def callee(tx: ydb.aio.QueryTxContext):
                tx_writer = driver.topic_client.tx_writer(tx, topic_path)
                await tx_writer.write(ydb.TopicWriterMessage(data="123".encode()))

            await pool.retry_tx_async(callee)

        msg = await wait_for(topic_reader.receive_message(), 0.1)
        assert msg.data.decode() == "123"

    async def test_rollback(self, driver: ydb.aio.Driver, topic_path, topic_reader: ydb.TopicReaderAsyncIO):
        async with ydb.aio.QuerySessionPool(driver) as pool:

            async def callee(tx: ydb.aio.QueryTxContext):
                tx_writer = driver.topic_client.tx_writer(tx, topic_path)
                await tx_writer.write(ydb.TopicWriterMessage(data="123".encode()))

                await tx.rollback()

            await pool.retry_tx_async(callee)

        with pytest.raises(asyncio.TimeoutError):
            await wait_for(topic_reader.receive_message(), 0.1)

    async def test_no_msg_written_in_error_case(
        self, driver: ydb.aio.Driver, topic_path, topic_reader: ydb.TopicReaderAsyncIO
    ):
        async with ydb.aio.QuerySessionPool(driver) as pool:

            async def callee(tx: ydb.aio.QueryTxContext):
                tx_writer = driver.topic_client.tx_writer(tx, topic_path)
                await tx_writer.write(ydb.TopicWriterMessage(data="123".encode()))

                raise BaseException("error")

            with pytest.raises(BaseException):
                await pool.retry_tx_async(callee)

        with pytest.raises(asyncio.TimeoutError):
            await wait_for(topic_reader.receive_message(), 0.1)

    async def test_msg_written_exactly_once_with_retries(
        self, driver: ydb.aio.Driver, topic_path, topic_reader: ydb.TopicReaderAsyncIO
    ):
        error_raised = False
        async with ydb.aio.QuerySessionPool(driver) as pool:

            async def callee(tx: ydb.aio.QueryTxContext):
                nonlocal error_raised
                tx_writer = driver.topic_client.tx_writer(tx, topic_path)
                await tx_writer.write(ydb.TopicWriterMessage(data="123".encode()))

                if not error_raised:
                    error_raised = True
                    raise ydb.issues.Unavailable("some retriable error")

            await pool.retry_tx_async(callee)

            msg = await wait_for(topic_reader.receive_message(), 0.1)
            assert msg.data.decode() == "123"

            with pytest.raises(asyncio.TimeoutError):
                await wait_for(topic_reader.receive_message(), 0.1)


class TestTopicTransactionalWriterSync:
    def test_commit(self, driver_sync: ydb.Driver, topic_path, topic_reader_sync: ydb.TopicReader):
        with ydb.QuerySessionPool(driver_sync) as pool:

            def callee(tx: ydb.QueryTxContext):
                tx_writer = driver_sync.topic_client.tx_writer(tx, topic_path)
                tx_writer.write(ydb.TopicWriterMessage(data="123".encode()))

            pool.retry_tx_sync(callee)

        msg = topic_reader_sync.receive_message(timeout=0.1)
        assert msg.data.decode() == "123"

    def test_rollback(self, driver_sync: ydb.aio.Driver, topic_path, topic_reader_sync: ydb.TopicReader):
        with ydb.QuerySessionPool(driver_sync) as pool:

            def callee(tx: ydb.QueryTxContext):
                tx_writer = driver_sync.topic_client.tx_writer(tx, topic_path)
                tx_writer.write(ydb.TopicWriterMessage(data="123".encode()))

                tx.rollback()

            pool.retry_tx_sync(callee)

        with pytest.raises(TimeoutError):
            topic_reader_sync.receive_message(timeout=0.1)

    def test_no_msg_written_in_error_case(
        self, driver_sync: ydb.Driver, topic_path, topic_reader_sync: ydb.TopicReaderAsyncIO
    ):
        with ydb.QuerySessionPool(driver_sync) as pool:

            def callee(tx: ydb.QueryTxContext):
                tx_writer = driver_sync.topic_client.tx_writer(tx, topic_path)
                tx_writer.write(ydb.TopicWriterMessage(data="123".encode()))

                raise BaseException("error")

            with pytest.raises(BaseException):
                pool.retry_tx_sync(callee)

        with pytest.raises(TimeoutError):
            topic_reader_sync.receive_message(timeout=0.1)
