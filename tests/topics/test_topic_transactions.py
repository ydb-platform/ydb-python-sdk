import asyncio
from asyncio import wait_for
import pytest
from unittest import mock
import ydb

DEFAULT_TIMEOUT = 0.5
DEFAULT_RETRY_SETTINGS = ydb.RetrySettings(max_retries=1)


@pytest.mark.asyncio
class TestTopicTransactionalReader:
    async def test_commit(self, driver: ydb.aio.Driver, topic_with_messages, topic_consumer):
        async with ydb.aio.QuerySessionPool(driver) as pool:
            async with driver.topic_client.reader(topic_with_messages, topic_consumer) as reader:

                async def callee(tx: ydb.aio.QueryTxContext):
                    batch = await wait_for(reader.receive_batch_with_tx(tx, max_messages=1), DEFAULT_TIMEOUT)
                    assert len(batch.messages) == 1
                    assert batch.messages[0].data.decode() == "123"

                    batch = await wait_for(reader.receive_batch_with_tx(tx, max_messages=1), DEFAULT_TIMEOUT)
                    assert len(batch.messages) == 1
                    assert batch.messages[0].data.decode() == "456"

                await pool.retry_tx_async(callee, retry_settings=DEFAULT_RETRY_SETTINGS)
                assert len(reader._reconnector._tx_to_batches_map) == 0

            async with driver.topic_client.reader(topic_with_messages, topic_consumer) as reader:
                msg = await wait_for(reader.receive_message(), DEFAULT_TIMEOUT)
                assert msg.data.decode() == "789"

    async def test_rollback(self, driver: ydb.aio.Driver, topic_with_messages, topic_consumer):
        async with driver.topic_client.reader(topic_with_messages, topic_consumer) as reader:
            async with ydb.aio.QuerySessionPool(driver) as pool:

                async def callee(tx: ydb.aio.QueryTxContext):
                    batch = await wait_for(reader.receive_batch_with_tx(tx, max_messages=1), DEFAULT_TIMEOUT)
                    assert len(batch.messages) == 1
                    assert batch.messages[0].data.decode() == "123"

                    await tx.rollback()

                await pool.retry_tx_async(callee, retry_settings=DEFAULT_RETRY_SETTINGS)
                assert len(reader._reconnector._tx_to_batches_map) == 0

                msg = await wait_for(reader.receive_message(), DEFAULT_TIMEOUT)
                assert msg.data.decode() == "123"

    async def test_tx_failed_if_update_offsets_call_failed(
        self, driver: ydb.aio.Driver, topic_with_messages, topic_consumer
    ):
        async with driver.topic_client.reader(topic_with_messages, topic_consumer) as reader:
            async with ydb.aio.QuerySessionPool(driver) as pool:
                with mock.patch.object(
                    reader._reconnector,
                    "_do_commit_batches_with_tx_call",
                    side_effect=ydb.Error("Update offsets in tx failed"),
                ):

                    async def callee(tx: ydb.aio.QueryTxContext):
                        batch = await wait_for(reader.receive_batch_with_tx(tx, max_messages=1), DEFAULT_TIMEOUT)
                        assert len(batch.messages) == 1
                        assert batch.messages[0].data.decode() == "123"

                    with pytest.raises(ydb.Error, match="Transaction was failed"):
                        await pool.retry_tx_async(callee, retry_settings=DEFAULT_RETRY_SETTINGS)

                    assert len(reader._reconnector._tx_to_batches_map) == 0

                    msg = await wait_for(reader.receive_message(), DEFAULT_TIMEOUT)
                    assert msg.data.decode() == "123"

    async def test_error_in_lambda(self, driver: ydb.aio.Driver, topic_with_messages, topic_consumer):
        async with driver.topic_client.reader(topic_with_messages, topic_consumer) as reader:
            async with ydb.aio.QuerySessionPool(driver) as pool:

                async def callee(tx: ydb.aio.QueryTxContext):
                    batch = await wait_for(reader.receive_batch_with_tx(tx, max_messages=1), DEFAULT_TIMEOUT)
                    assert len(batch.messages) == 1
                    assert batch.messages[0].data.decode() == "123"

                    raise RuntimeError("Something went wrong")

                with pytest.raises(RuntimeError):
                    await pool.retry_tx_async(callee, retry_settings=DEFAULT_RETRY_SETTINGS)

                assert len(reader._reconnector._tx_to_batches_map) == 0

                msg = await wait_for(reader.receive_message(), DEFAULT_TIMEOUT)
                assert msg.data.decode() == "123"

    async def test_error_during_commit(self, driver: ydb.aio.Driver, topic_with_messages, topic_consumer):
        async with driver.topic_client.reader(topic_with_messages, topic_consumer) as reader:
            async with ydb.aio.QuerySessionPool(driver) as pool:

                async def callee(tx: ydb.aio.QueryTxContext):
                    with mock.patch.object(
                        tx,
                        "_commit_call",
                        side_effect=ydb.Unavailable("YDB Unavailable"),
                    ):
                        batch = await wait_for(reader.receive_batch_with_tx(tx, max_messages=1), DEFAULT_TIMEOUT)
                        assert len(batch.messages) == 1
                        assert batch.messages[0].data.decode() == "123"

                        await tx.commit()

                with pytest.raises(ydb.Unavailable):
                    await pool.retry_tx_async(callee, retry_settings=DEFAULT_RETRY_SETTINGS)

                assert len(reader._reconnector._tx_to_batches_map) == 0

                msg = await wait_for(reader.receive_message(), DEFAULT_TIMEOUT)
                assert msg.data.decode() == "123"

    async def test_error_during_rollback(self, driver: ydb.aio.Driver, topic_with_messages, topic_consumer):
        async with driver.topic_client.reader(topic_with_messages, topic_consumer) as reader:
            async with ydb.aio.QuerySessionPool(driver) as pool:

                async def callee(tx: ydb.aio.QueryTxContext):
                    with mock.patch.object(
                        tx,
                        "_rollback_call",
                        side_effect=ydb.Unavailable("YDB Unavailable"),
                    ):
                        batch = await wait_for(reader.receive_batch_with_tx(tx, max_messages=1), DEFAULT_TIMEOUT)
                        assert len(batch.messages) == 1
                        assert batch.messages[0].data.decode() == "123"

                        await tx.rollback()

                with pytest.raises(ydb.Unavailable):
                    await pool.retry_tx_async(callee, retry_settings=DEFAULT_RETRY_SETTINGS)

                assert len(reader._reconnector._tx_to_batches_map) == 0

                msg = await wait_for(reader.receive_message(), DEFAULT_TIMEOUT)
                assert msg.data.decode() == "123"


class TestTopicTransactionalReaderSync:
    def test_commit(self, driver_sync: ydb.Driver, topic_with_messages, topic_consumer):
        with ydb.QuerySessionPool(driver_sync) as pool:
            with driver_sync.topic_client.reader(topic_with_messages, topic_consumer) as reader:

                def callee(tx: ydb.QueryTxContext):
                    batch = reader.receive_batch_with_tx(tx, max_messages=1, timeout=DEFAULT_TIMEOUT)
                    assert len(batch.messages) == 1
                    assert batch.messages[0].data.decode() == "123"

                    batch = reader.receive_batch_with_tx(tx, max_messages=1, timeout=DEFAULT_TIMEOUT)
                    assert len(batch.messages) == 1
                    assert batch.messages[0].data.decode() == "456"

                pool.retry_tx_sync(callee, retry_settings=DEFAULT_RETRY_SETTINGS)
                assert len(reader._async_reader._reconnector._tx_to_batches_map) == 0

            with driver_sync.topic_client.reader(topic_with_messages, topic_consumer) as reader:
                msg = reader.receive_message(timeout=DEFAULT_TIMEOUT)
                assert msg.data.decode() == "789"

    def test_rollback(self, driver_sync: ydb.Driver, topic_with_messages, topic_consumer):
        with driver_sync.topic_client.reader(topic_with_messages, topic_consumer) as reader:
            with ydb.QuerySessionPool(driver_sync) as pool:

                def callee(tx: ydb.QueryTxContext):
                    batch = reader.receive_batch_with_tx(tx, max_messages=1, timeout=DEFAULT_TIMEOUT)
                    assert len(batch.messages) == 1
                    assert batch.messages[0].data.decode() == "123"

                    tx.rollback()

                pool.retry_tx_sync(callee, retry_settings=DEFAULT_RETRY_SETTINGS)
                assert len(reader._async_reader._reconnector._tx_to_batches_map) == 0

                msg = reader.receive_message(timeout=DEFAULT_TIMEOUT)
                assert msg.data.decode() == "123"

    def test_tx_failed_if_update_offsets_call_failed(
        self, driver_sync: ydb.Driver, topic_with_messages, topic_consumer
    ):
        with driver_sync.topic_client.reader(topic_with_messages, topic_consumer) as reader:
            with ydb.QuerySessionPool(driver_sync) as pool:
                with mock.patch.object(
                    reader._async_reader._reconnector,
                    "_do_commit_batches_with_tx_call",
                    side_effect=ydb.Error("Update offsets in tx failed"),
                ):

                    def callee(tx: ydb.QueryTxContext):
                        batch = reader.receive_batch_with_tx(tx, max_messages=1, timeout=DEFAULT_TIMEOUT)
                        assert len(batch.messages) == 1
                        assert batch.messages[0].data.decode() == "123"

                    with pytest.raises(ydb.Error, match="Transaction was failed"):
                        pool.retry_tx_sync(callee, retry_settings=DEFAULT_RETRY_SETTINGS)

                    assert len(reader._async_reader._reconnector._tx_to_batches_map) == 0

                    msg = reader.receive_message(timeout=DEFAULT_TIMEOUT)
                    assert msg.data.decode() == "123"

    def test_error_in_lambda(self, driver_sync: ydb.Driver, topic_with_messages, topic_consumer):
        with driver_sync.topic_client.reader(topic_with_messages, topic_consumer) as reader:
            with ydb.QuerySessionPool(driver_sync) as pool:

                def callee(tx: ydb.QueryTxContext):
                    batch = reader.receive_batch_with_tx(tx, max_messages=1, timeout=DEFAULT_TIMEOUT)
                    assert len(batch.messages) == 1
                    assert batch.messages[0].data.decode() == "123"

                    raise RuntimeError("Something went wrong")

                with pytest.raises(RuntimeError):
                    pool.retry_tx_sync(callee, retry_settings=DEFAULT_RETRY_SETTINGS)

                assert len(reader._async_reader._reconnector._tx_to_batches_map) == 0

                msg = reader.receive_message(timeout=DEFAULT_TIMEOUT)
                assert msg.data.decode() == "123"

    def test_error_during_commit(self, driver_sync: ydb.Driver, topic_with_messages, topic_consumer):
        with driver_sync.topic_client.reader(topic_with_messages, topic_consumer) as reader:
            with ydb.QuerySessionPool(driver_sync) as pool:

                def callee(tx: ydb.QueryTxContext):
                    with mock.patch.object(
                        tx,
                        "_commit_call",
                        side_effect=ydb.Unavailable("YDB Unavailable"),
                    ):
                        batch = reader.receive_batch_with_tx(tx, max_messages=1, timeout=DEFAULT_TIMEOUT)
                        assert len(batch.messages) == 1
                        assert batch.messages[0].data.decode() == "123"

                        tx.commit()

                with pytest.raises(ydb.Unavailable):
                    pool.retry_tx_sync(callee, retry_settings=DEFAULT_RETRY_SETTINGS)

                assert len(reader._async_reader._reconnector._tx_to_batches_map) == 0

                msg = reader.receive_message(timeout=DEFAULT_TIMEOUT)
                assert msg.data.decode() == "123"

    def test_error_during_rollback(self, driver_sync: ydb.Driver, topic_with_messages, topic_consumer):
        with driver_sync.topic_client.reader(topic_with_messages, topic_consumer) as reader:
            with ydb.QuerySessionPool(driver_sync) as pool:

                def callee(tx: ydb.QueryTxContext):
                    with mock.patch.object(
                        tx,
                        "_rollback_call",
                        side_effect=ydb.Unavailable("YDB Unavailable"),
                    ):
                        batch = reader.receive_batch_with_tx(tx, max_messages=1, timeout=DEFAULT_TIMEOUT)
                        assert len(batch.messages) == 1
                        assert batch.messages[0].data.decode() == "123"

                        tx.rollback()

                with pytest.raises(ydb.Unavailable):
                    pool.retry_tx_sync(callee, retry_settings=DEFAULT_RETRY_SETTINGS)

                assert len(reader._async_reader._reconnector._tx_to_batches_map) == 0

                msg = reader.receive_message(timeout=DEFAULT_TIMEOUT)
                assert msg.data.decode() == "123"


class TestTopicTransactionalWriter:
    async def test_commit(self, driver: ydb.aio.Driver, topic_path, topic_reader: ydb.TopicReaderAsyncIO):
        async with ydb.aio.QuerySessionPool(driver) as pool:

            async def callee(tx: ydb.aio.QueryTxContext):
                tx_writer = driver.topic_client.tx_writer(tx, topic_path)
                await tx_writer.write(ydb.TopicWriterMessage(data="123".encode()))

            await pool.retry_tx_async(callee, retry_settings=DEFAULT_RETRY_SETTINGS)

        msg = await wait_for(topic_reader.receive_message(), 0.1)
        assert msg.data.decode() == "123"

    async def test_rollback(self, driver: ydb.aio.Driver, topic_path, topic_reader: ydb.TopicReaderAsyncIO):
        async with ydb.aio.QuerySessionPool(driver) as pool:

            async def callee(tx: ydb.aio.QueryTxContext):
                tx_writer = driver.topic_client.tx_writer(tx, topic_path)
                await tx_writer.write(ydb.TopicWriterMessage(data="123".encode()))

                await tx.rollback()

            await pool.retry_tx_async(callee, retry_settings=DEFAULT_RETRY_SETTINGS)

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
                await pool.retry_tx_async(callee, retry_settings=DEFAULT_RETRY_SETTINGS)

        with pytest.raises(asyncio.TimeoutError):
            await wait_for(topic_reader.receive_message(), 0.1)

    async def test_no_msg_written_in_tx_commit_error(
        self, driver: ydb.aio.Driver, topic_path, topic_reader: ydb.TopicReaderAsyncIO
    ):
        async with ydb.aio.QuerySessionPool(driver) as pool:

            async def callee(tx: ydb.aio.QueryTxContext):
                with mock.patch.object(
                    tx,
                    "_commit_call",
                    side_effect=ydb.Unavailable("YDB Unavailable"),
                ):
                    tx_writer = driver.topic_client.tx_writer(tx, topic_path)
                    await tx_writer.write(ydb.TopicWriterMessage(data="123".encode()))
                    await tx.commit()

            with pytest.raises(ydb.Unavailable):
                await pool.retry_tx_async(callee, retry_settings=DEFAULT_RETRY_SETTINGS)

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

            await pool.retry_tx_async(callee, retry_settings=DEFAULT_RETRY_SETTINGS)

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

            pool.retry_tx_sync(callee, retry_settings=DEFAULT_RETRY_SETTINGS)

        msg = topic_reader_sync.receive_message(timeout=DEFAULT_TIMEOUT)
        assert msg.data.decode() == "123"

    def test_rollback(self, driver_sync: ydb.Driver, topic_path, topic_reader_sync: ydb.TopicReader):
        with ydb.QuerySessionPool(driver_sync) as pool:

            def callee(tx: ydb.QueryTxContext):
                tx_writer = driver_sync.topic_client.tx_writer(tx, topic_path)
                tx_writer.write(ydb.TopicWriterMessage(data="123".encode()))

                tx.rollback()

            pool.retry_tx_sync(callee, retry_settings=DEFAULT_RETRY_SETTINGS)

        with pytest.raises(TimeoutError):
            topic_reader_sync.receive_message(timeout=DEFAULT_TIMEOUT)

    def test_no_msg_written_in_error_case(
        self, driver_sync: ydb.Driver, topic_path, topic_reader_sync: ydb.TopicReader
    ):
        with ydb.QuerySessionPool(driver_sync) as pool:

            def callee(tx: ydb.QueryTxContext):
                tx_writer = driver_sync.topic_client.tx_writer(tx, topic_path)
                tx_writer.write(ydb.TopicWriterMessage(data="123".encode()))

                raise BaseException("error")

            with pytest.raises(BaseException):
                pool.retry_tx_sync(callee, retry_settings=DEFAULT_RETRY_SETTINGS)

        with pytest.raises(TimeoutError):
            topic_reader_sync.receive_message(timeout=DEFAULT_TIMEOUT)

    def test_no_msg_written_in_tx_commit_error(
        self, driver_sync: ydb.Driver, topic_path, topic_reader_sync: ydb.TopicReader
    ):
        with ydb.QuerySessionPool(driver_sync) as pool:

            def callee(tx: ydb.QueryTxContext):
                with mock.patch.object(
                    tx,
                    "_commit_call",
                    side_effect=ydb.Unavailable("YDB Unavailable"),
                ):
                    tx_writer = driver_sync.topic_client.tx_writer(tx, topic_path)
                    tx_writer.write(ydb.TopicWriterMessage(data="123".encode()))
                    tx.commit()

            with pytest.raises(ydb.Unavailable):
                pool.retry_tx_sync(callee, retry_settings=DEFAULT_RETRY_SETTINGS)

        with pytest.raises(TimeoutError):
            topic_reader_sync.receive_message(timeout=DEFAULT_TIMEOUT)

    def test_msg_written_exactly_once_with_retries(
        self, driver_sync: ydb.Driver, topic_path, topic_reader_sync: ydb.TopicReader
    ):
        error_raised = False
        with ydb.QuerySessionPool(driver_sync) as pool:

            def callee(tx: ydb.QueryTxContext):
                nonlocal error_raised
                tx_writer = driver_sync.topic_client.tx_writer(tx, topic_path)
                tx_writer.write(ydb.TopicWriterMessage(data="123".encode()))

                if not error_raised:
                    error_raised = True
                    raise ydb.issues.Unavailable("some retriable error")

            pool.retry_tx_sync(callee, retry_settings=DEFAULT_RETRY_SETTINGS)

            msg = topic_reader_sync.receive_message(timeout=DEFAULT_TIMEOUT)
            assert msg.data.decode() == "123"

            with pytest.raises(TimeoutError):
                topic_reader_sync.receive_message(timeout=DEFAULT_TIMEOUT)
