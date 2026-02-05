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
        async with driver.topic_client.reader(topic_path, topic_consumer) as reader:
            assert reader._parent is driver.topic_client

    async def test_read_message(self, driver, topic_with_messages, topic_consumer):
        reader = driver.topic_client.reader(topic_with_messages, topic_consumer)
        await reader.wait_message()
        msg = await reader.receive_message()

        assert msg is not None
        assert msg.seqno

        await reader.close()

    async def test_read_metadata(self, driver, topic_with_messages_with_metadata, topic_consumer):
        reader = driver.topic_client.reader(topic_with_messages_with_metadata, topic_consumer)

        expected_metadata_items = {"key": b"value"}

        for _ in range(2):
            await reader.wait_message()
            msg = await reader.receive_message()

            assert msg is not None
            assert msg.metadata_items
            assert msg.metadata_items == expected_metadata_items

        await reader.close()

    async def test_read_and_commit_with_close_reader(self, driver, topic_with_messages, topic_consumer):
        async with driver.topic_client.reader(topic_with_messages, topic_consumer) as reader:
            message = await reader.receive_message()
            reader.commit(message)

        async with driver.topic_client.reader(topic_with_messages, topic_consumer) as reader:
            message2 = await reader.receive_message()
            assert message != message2

    async def test_read_and_commit_with_ack(self, driver, topic_with_messages, topic_consumer):
        async with driver.topic_client.reader(topic_with_messages, topic_consumer) as reader:
            message = await reader.receive_message()
            await reader.commit_with_ack(message)

        async with driver.topic_client.reader(topic_with_messages, topic_consumer) as reader:
            batch = await reader.receive_batch()

        assert message != batch.messages[0]

    async def test_commit_offset_works(self, driver, topic_with_messages, topic_consumer):
        for out in ["123", "456", "789", "0"]:
            async with driver.topic_client.reader(topic_with_messages, topic_consumer) as reader:
                message = await reader.receive_message()
                assert message.data.decode() == out

                await driver.topic_client.commit_offset(
                    topic_with_messages, topic_consumer, message.partition_id, message.offset + 1
                )

    async def test_commit_offset_with_session_id_works(self, driver, topic_with_messages, topic_consumer):
        async with driver.topic_client.reader(topic_with_messages, topic_consumer) as reader:
            msg1 = await reader.receive_message()
            assert msg1.seqno == 1
            msg2 = await reader.receive_message()
            assert msg2.seqno == 2

            await driver.topic_client.commit_offset(
                topic_with_messages,
                topic_consumer,
                msg1.partition_id,
                msg1.offset + 1,
                reader.read_session_id,
            )

            msg3 = await reader.receive_message()
            assert msg3.seqno == 3

        async with driver.topic_client.reader(topic_with_messages, topic_consumer) as reader:
            msg2 = await reader.receive_message()
            assert msg2.seqno == 2

    async def test_commit_offset_retry_on_ydb_errors(self, driver, topic_with_messages, topic_consumer, monkeypatch):
        async with driver.topic_client.reader(topic_with_messages, topic_consumer) as reader:
            message = await reader.receive_message()

            call_count = 0
            original_driver_call = driver.topic_client._driver

            async def mock_driver_call(*args, **kwargs):
                nonlocal call_count
                call_count += 1

                if call_count == 1:
                    raise ydb.Unavailable("Service temporarily unavailable")
                elif call_count == 2:
                    raise ydb.Cancelled("Operation was cancelled")
                else:
                    return await original_driver_call(*args, **kwargs)

            monkeypatch.setattr(driver.topic_client, "_driver", mock_driver_call)

            await driver.topic_client.commit_offset(
                topic_with_messages, topic_consumer, message.partition_id, message.offset + 1
            )

            assert call_count == 3

    async def test_reader_reconnect_after_commit_offset(self, driver, topic_with_messages, topic_consumer):
        async with driver.topic_client.reader(topic_with_messages, topic_consumer) as reader:
            for out in ["123", "456", "789", "0"]:
                message = await reader.receive_message()
                assert message.data.decode() == out

                await driver.topic_client.commit_offset(
                    topic_with_messages, topic_consumer, message.partition_id, message.offset + 1
                )

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
        with driver_sync.topic_client.reader(topic_path, topic_consumer) as reader:
            assert reader._parent is driver_sync.topic_client

    def test_read_message(self, driver_sync, topic_with_messages, topic_consumer):
        reader = driver_sync.topic_client.reader(topic_with_messages, topic_consumer)
        msg = reader.receive_message()

        assert msg is not None
        assert msg.seqno

        reader.close()

    def test_read_metadata(self, driver_sync, topic_with_messages_with_metadata, topic_consumer):
        reader = driver_sync.topic_client.reader(topic_with_messages_with_metadata, topic_consumer)

        expected_metadata_items = {"key": b"value"}

        for _ in range(2):
            msg = reader.receive_message()

            assert msg is not None
            assert msg.metadata_items
            assert msg.metadata_items == expected_metadata_items

        reader.close()

    def test_read_and_commit_with_close_reader(self, driver_sync, topic_with_messages, topic_consumer):
        with driver_sync.topic_client.reader(topic_with_messages, topic_consumer) as reader:
            message = reader.receive_message()
            reader.commit(message)

        with driver_sync.topic_client.reader(topic_with_messages, topic_consumer) as reader:
            message2 = reader.receive_message()
            assert message != message2

    def test_read_and_commit_with_ack(self, driver_sync, topic_with_messages, topic_consumer):
        with driver_sync.topic_client.reader(topic_with_messages, topic_consumer) as reader:
            message = reader.receive_message()
            reader.commit_with_ack(message)

        with driver_sync.topic_client.reader(topic_with_messages, topic_consumer) as reader:
            batch = reader.receive_batch()

        assert message != batch.messages[0]

    def test_commit_offset_works(self, driver_sync, topic_with_messages, topic_consumer):
        for out in ["123", "456", "789", "0"]:
            with driver_sync.topic_client.reader(topic_with_messages, topic_consumer) as reader:
                message = reader.receive_message()
                assert message.data.decode() == out

                driver_sync.topic_client.commit_offset(
                    topic_with_messages, topic_consumer, message.partition_id, message.offset + 1
                )

    def test_commit_offset_with_session_id_works(self, driver_sync, topic_with_messages, topic_consumer):
        with driver_sync.topic_client.reader(topic_with_messages, topic_consumer) as reader:
            msg1 = reader.receive_message()
            assert msg1.seqno == 1
            msg2 = reader.receive_message()
            assert msg2.seqno == 2

            driver_sync.topic_client.commit_offset(
                topic_with_messages,
                topic_consumer,
                msg1.partition_id,
                msg1.offset + 1,
                reader.read_session_id,
            )

            msg3 = reader.receive_message()
            assert msg3.seqno == 3

        with driver_sync.topic_client.reader(topic_with_messages, topic_consumer) as reader:
            msg2 = reader.receive_message()
            assert msg2.seqno == 2

    def test_commit_offset_retry_on_ydb_errors(self, driver_sync, topic_with_messages, topic_consumer, monkeypatch):
        with driver_sync.topic_client.reader(topic_with_messages, topic_consumer) as reader:
            message = reader.receive_message()

            # Counter to track retry attempts
            call_count = 0
            original_driver_call = driver_sync.topic_client._driver

            def mock_driver_call(*args, **kwargs):
                nonlocal call_count
                call_count += 1

                if call_count == 1:
                    raise ydb.Unavailable("Service temporarily unavailable")
                elif call_count == 2:
                    raise ydb.Cancelled("Operation was cancelled")
                else:
                    return original_driver_call(*args, **kwargs)

            monkeypatch.setattr(driver_sync.topic_client, "_driver", mock_driver_call)

            driver_sync.topic_client.commit_offset(
                topic_with_messages, topic_consumer, message.partition_id, message.offset + 1
            )

            assert call_count == 3

    def test_reader_reconnect_after_commit_offset(self, driver_sync, topic_with_messages, topic_consumer):
        with driver_sync.topic_client.reader(topic_with_messages, topic_consumer) as reader:
            for out in ["123", "456", "789", "0"]:
                message = reader.receive_message()
                assert message.data.decode() == out

                driver_sync.topic_client.commit_offset(
                    topic_with_messages, topic_consumer, message.partition_id, message.offset + 1
                )

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

        await reader0.close()
        await reader1.close()


@pytest.fixture()
def topic_selector(topic_with_messages):
    return ydb.TopicReaderSelector(path=topic_with_messages, partitions=[0])


@pytest.mark.asyncio
@pytest.mark.skip("something went wrong")
class TestTopicNoConsumerReaderAsyncIO:
    async def test_reader_with_no_partition_ids_raises(self, driver, topic_with_messages):
        with pytest.raises(ydb.Error):
            driver.topic_client.reader(
                topic_with_messages,
                consumer=None,
                event_handler=ydb.TopicReaderEvents.EventHandler(),
            )

    async def test_reader_with_no_event_handler_raises(self, driver, topic_with_messages):
        with pytest.raises(ydb.Error):
            driver.topic_client.reader(
                topic_with_messages,
                consumer=None,
            )

    async def test_reader_with_no_partition_ids_selector_raises(self, driver, topic_selector):
        topic_selector.partitions = None

        with pytest.raises(ydb.Error):
            driver.topic_client.reader(
                topic_selector,
                consumer=None,
                event_handler=ydb.TopicReaderEvents.EventHandler(),
            )

    async def test_reader_with_default_lambda(self, driver, topic_selector):
        reader = driver.topic_client.reader(
            topic_selector,
            consumer=None,
            event_handler=ydb.TopicReaderEvents.EventHandler(),
        )
        msg = await reader.receive_message()

        assert msg.seqno == 1

        await reader.close()

    async def test_reader_with_sync_lambda(self, driver, topic_selector):
        class CustomEventHandler(ydb.TopicReaderEvents.EventHandler):
            def on_partition_get_start_offset(self, event):
                assert topic_selector.path.endswith(event.topic)
                assert event.partition_id == 0
                return ydb.TopicReaderEvents.OnPartitionGetStartOffsetResponse(1)

        reader = driver.topic_client.reader(
            topic_selector,
            consumer=None,
            event_handler=CustomEventHandler(),
        )

        msg = await reader.receive_message()

        assert msg.seqno == 2

        await reader.close()

    async def test_reader_with_async_lambda(self, driver, topic_selector):
        class CustomEventHandler(ydb.TopicReaderEvents.EventHandler):
            async def on_partition_get_start_offset(self, event):
                assert topic_selector.path.endswith(event.topic)
                assert event.partition_id == 0
                return ydb.TopicReaderEvents.OnPartitionGetStartOffsetResponse(1)

        reader = driver.topic_client.reader(
            topic_selector,
            consumer=None,
            event_handler=CustomEventHandler(),
        )

        msg = await reader.receive_message()

        assert msg.seqno == 2

        await reader.close()

    async def test_commit_not_allowed(self, driver, topic_selector):
        reader = driver.topic_client.reader(
            topic_selector,
            consumer=None,
            event_handler=ydb.TopicReaderEvents.EventHandler(),
        )
        batch = await reader.receive_batch()

        with pytest.raises(ydb.Error):
            reader.commit(batch)

        with pytest.raises(ydb.Error):
            await reader.commit_with_ack(batch)

        await reader.close()

    async def test_offsets_updated_after_reconnect(self, driver, topic_selector):
        current_offset = 0

        class CustomEventHandler(ydb.TopicReaderEvents.EventHandler):
            def on_partition_get_start_offset(self, event):
                return ydb.TopicReaderEvents.OnPartitionGetStartOffsetResponse(current_offset)

        reader = driver.topic_client.reader(
            topic_selector,
            consumer=None,
            event_handler=CustomEventHandler(),
        )
        msg = await reader.receive_message()

        assert msg.seqno == current_offset + 1

        current_offset += 2
        reader._reconnector._stream_reader._set_first_error(ydb.Unavailable("some retriable error"))

        await asyncio.sleep(0)

        msg = await reader.receive_message()

        assert msg.seqno == current_offset + 1

        await reader.close()


@pytest.mark.skip("something went wrong")
class TestTopicReaderWithoutConsumer:
    def test_reader_with_no_partition_ids_raises(self, driver_sync, topic_with_messages):
        with pytest.raises(ydb.Error):
            driver_sync.topic_client.reader(
                topic_with_messages,
                consumer=None,
                event_handler=ydb.TopicReaderEvents.EventHandler(),
            )

    def test_reader_with_no_event_handler_raises(self, driver_sync, topic_with_messages):
        with pytest.raises(ydb.Error):
            driver_sync.topic_client.reader(
                topic_with_messages,
                consumer=None,
            )

    def test_reader_with_no_partition_ids_selector_raises(self, driver_sync, topic_selector):
        topic_selector.partitions = None

        with pytest.raises(ydb.Error):
            driver_sync.topic_client.reader(
                topic_selector,
                consumer=None,
                event_handler=ydb.TopicReaderEvents.EventHandler(),
            )

    def test_reader_with_default_lambda(self, driver_sync, topic_selector):
        reader = driver_sync.topic_client.reader(
            topic_selector,
            consumer=None,
            event_handler=ydb.TopicReaderEvents.EventHandler(),
        )
        msg = reader.receive_message()

        assert msg.seqno == 1

        reader.close()

    def test_reader_with_sync_lambda(self, driver_sync, topic_selector):
        class CustomEventHandler(ydb.TopicReaderEvents.EventHandler):
            def on_partition_get_start_offset(self, event):
                assert topic_selector.path.endswith(event.topic)
                assert event.partition_id == 0
                return ydb.TopicReaderEvents.OnPartitionGetStartOffsetResponse(1)

        reader = driver_sync.topic_client.reader(
            topic_selector,
            consumer=None,
            event_handler=CustomEventHandler(),
        )

        msg = reader.receive_message()

        assert msg.seqno == 2

        reader.close()

    def test_reader_with_async_lambda(self, driver_sync, topic_selector):
        class CustomEventHandler(ydb.TopicReaderEvents.EventHandler):
            async def on_partition_get_start_offset(self, event):
                assert topic_selector.path.endswith(event.topic)
                assert event.partition_id == 0
                return ydb.TopicReaderEvents.OnPartitionGetStartOffsetResponse(1)

        reader = driver_sync.topic_client.reader(
            topic_selector,
            consumer=None,
            event_handler=CustomEventHandler(),
        )

        msg = reader.receive_message()

        assert msg.seqno == 2

        reader.close()

    def test_commit_not_allowed(self, driver_sync, topic_selector):
        reader = driver_sync.topic_client.reader(
            topic_selector,
            consumer=None,
            event_handler=ydb.TopicReaderEvents.EventHandler(),
        )
        batch = reader.receive_batch()

        with pytest.raises(ydb.Error):
            reader.commit(batch)

        with pytest.raises(ydb.Error):
            reader.commit_with_ack(batch)

        reader.close()

    def test_offsets_updated_after_reconnect(self, driver_sync, topic_selector):
        current_offset = 0

        class CustomEventHandler(ydb.TopicReaderEvents.EventHandler):
            def on_partition_get_start_offset(self, event):
                return ydb.TopicReaderEvents.OnPartitionGetStartOffsetResponse(current_offset)

        reader = driver_sync.topic_client.reader(
            topic_selector,
            consumer=None,
            event_handler=CustomEventHandler(),
        )
        msg = reader.receive_message()

        assert msg.seqno == current_offset + 1

        current_offset += 2
        reader._async_reader._reconnector._stream_reader._set_first_error(ydb.Unavailable("some retriable error"))

        msg = reader.receive_message()

        assert msg.seqno == current_offset + 1

        reader.close()
