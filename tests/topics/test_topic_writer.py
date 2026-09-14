from __future__ import annotations

import asyncio
import datetime
from typing import List  # noqa: F401

import pytest

import ydb
import ydb.aio


@pytest.mark.asyncio
class TestTopicWriterAsyncIO:
    async def test_send_message(self, driver: ydb.aio.Driver, topic_path):
        writer = driver.topic_client.writer(topic_path, producer_id="test")
        await writer.write(ydb.TopicWriterMessage(data="123".encode()))
        await writer.close()

    async def test_send_message_with_metadata(self, driver: ydb.aio.Driver, topic_path):
        writer = driver.topic_client.writer(topic_path, producer_id="test")
        await writer.write(ydb.TopicWriterMessage(data="123".encode(), metadata_items={"key": "value"}))
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
        async with driver.topic_client.writer(topic_path) as writer:
            assert writer._parent is driver.topic_client

    async def test_random_producer_id(self, driver: ydb.aio.Driver, topic_path, topic_reader: ydb.TopicReaderAsyncIO):
        async with driver.topic_client.writer(topic_path) as writer:
            await writer.write(ydb.TopicWriterMessage(data="123".encode()))
        async with driver.topic_client.writer(topic_path) as writer:
            await writer.write(ydb.TopicWriterMessage(data="123".encode()))

        msg1 = await topic_reader.receive_message()
        msg2 = await topic_reader.receive_message()

        assert msg1.producer_id != msg2.producer_id

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

        msg1 = await topic_reader.receive_message()
        msg2 = await topic_reader.receive_message()

        assert msg1.offset == 0
        assert msg1.seqno == 1
        assert msg1.data == "123".encode()

        assert msg2.offset == 1
        assert msg2.seqno == 2
        assert msg2.data == "456".encode()

    @pytest.mark.parametrize(
        "codec",
        [
            ydb.TopicCodec.RAW,
            ydb.TopicCodec.GZIP,
            None,
        ],
    )
    async def test_write_encoded(self, driver: ydb.aio.Driver, topic_path: str, codec):
        async with driver.topic_client.writer(topic_path, codec=codec) as writer:
            await writer.write("a" * 1000)
            await writer.write("b" * 1000)
            await writer.write("c" * 1000)

    async def test_create_writer_after_stop(self, driver: ydb.aio.Driver, topic_path: str):
        await driver.stop()
        with pytest.raises(ydb.Error):
            async with driver.topic_client.writer(topic_path) as writer:
                await writer.write_with_ack("123")

    @pytest.mark.skip(reason="something wrong with this test, need to assess")
    async def test_send_message_after_stop(self, driver: ydb.aio.Driver, topic_path: str):
        writer = driver.topic_client.writer(topic_path)
        await driver.stop()
        with pytest.raises(ydb.Error):
            await writer.write_with_ack("123")

    async def test_preserve_exception_on_cm_close(self, driver: ydb.aio.Driver, topic_path: str):
        class TestException(Exception):
            pass

        with pytest.raises(TestException):
            async with driver.topic_client.writer(topic_path) as writer:
                await writer.wait_init()
                await driver.stop()  # will raise exception on topic writer __exit__

                # ensure writer has exception internally
                with pytest.raises((ydb.Error, asyncio.CancelledError)):
                    await writer.write_with_ack("123")

                raise TestException()


@pytest.mark.asyncio
class TestTopicWriterBackpressureAsyncIO:
    async def test_write_and_read_with_backpressure_settings(
        self, driver: ydb.aio.Driver, topic_path: str, topic_consumer: str
    ):
        messages = [b"msg-1", b"msg-2", b"msg-3"]

        async with driver.topic_client.writer(
            topic_path,
            producer_id="bp-test",
            max_buffer_size_bytes=1024 * 1024,
            max_buffer_messages=100,
            buffer_wait_timeout_sec=10.0,
        ) as writer:
            for data in messages:
                await writer.write(ydb.TopicWriterMessage(data=data))

        async with driver.topic_client.reader(topic_path, consumer=topic_consumer) as reader:
            for expected in messages:
                msg = await asyncio.wait_for(reader.receive_message(), timeout=10)
                assert msg.data == expected
                reader.commit(msg)


class TestTopicWriterBackpressureSync:
    def test_write_and_read_with_backpressure_settings(
        self, driver_sync: ydb.Driver, topic_path: str, topic_consumer: str
    ):
        messages = [b"msg-1", b"msg-2", b"msg-3"]

        with driver_sync.topic_client.writer(
            topic_path,
            producer_id="bp-sync-test",
            max_buffer_size_bytes=1024 * 1024,
            max_buffer_messages=100,
            buffer_wait_timeout_sec=10.0,
        ) as writer:
            for data in messages:
                writer.write(ydb.TopicWriterMessage(data=data))

        with driver_sync.topic_client.reader(topic_path, consumer=topic_consumer) as reader:
            for expected in messages:
                msg = reader.receive_message(timeout=10)
                assert msg.data == expected
                reader.commit(msg)


class TestTopicWriterSync:
    def test_send_message(self, driver_sync: ydb.Driver, topic_path):
        writer = driver_sync.topic_client.writer(topic_path, producer_id="test")
        writer.write(ydb.TopicWriterMessage(data="123".encode()))
        writer.close()

    def test_send_message_with_metadata(self, driver_sync: ydb.Driver, topic_path):
        writer = driver_sync.topic_client.writer(topic_path, producer_id="test")
        writer.write(ydb.TopicWriterMessage(data="123".encode(), metadata_items={"key": "value"}))
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
        with driver_sync.topic_client.writer(topic_path) as writer:
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

        msg1 = topic_reader_sync.receive_message()
        msg2 = topic_reader_sync.receive_message()

        assert msg1.producer_id != msg2.producer_id

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

        msg1 = topic_reader_sync.receive_message()
        msg2 = topic_reader_sync.receive_message()

        assert msg1.offset == 0
        assert msg1.seqno == 1
        assert msg1.data == "123".encode()

        assert msg2.offset == 1
        assert msg2.seqno == 2
        assert msg2.data == "456".encode()

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

    def test_create_writer_after_stop(self, driver_sync: ydb.Driver, topic_path: str):
        driver_sync.stop()
        with pytest.raises(ydb.Error):
            with driver_sync.topic_client.writer(topic_path) as writer:
                writer.write_with_ack("123")

    @pytest.mark.skip(reason="something wrong with this test, need to assess")
    def test_send_message_after_stop(self, driver_sync: ydb.Driver, topic_path: str):
        writer = driver_sync.topic_client.writer(topic_path)
        driver_sync.stop()
        with pytest.raises(ydb.Error):
            writer.write_with_ack("123")

    def test_preserve_exception_on_cm_close(self, driver_sync: ydb.Driver, topic_path: str):
        class TestException(Exception):
            pass

        with pytest.raises(TestException):
            with driver_sync.topic_client.writer(topic_path) as writer:
                writer.wait_init()
                driver_sync.stop()  # will raise exception on topic writer __exit__

                # ensure writer has exception internally
                with pytest.raises(ydb.Error):
                    writer.write_with_ack("123")

                raise TestException()


@pytest.mark.asyncio
class TestTopicMultiWriterAsyncIO:
    async def test_flush_and_close_report_encoder_errors(self, driver, database, topic_consumer):
        path = database + "/mw-encoder-error"
        await self._recreate(driver, path, topic_consumer)

        def failing_encoder(data):
            raise ValueError("encoder failed")

        writer = driver.topic_client.multiwriter(
            path,
            codec=ydb.TopicCodec.GZIP,
            encoders={ydb.TopicCodec.GZIP: failing_encoder},
        )
        try:
            await writer.write(ydb.TopicWriterMessage(data=b"payload", key="key"))
            with pytest.raises(ValueError, match="encoder failed"):
                await asyncio.wait_for(writer.flush(), timeout=10)
            with pytest.raises(ValueError, match="encoder failed"):
                await asyncio.wait_for(writer.close(), timeout=10)
            assert writer._closed
            assert not writer._writers
        finally:
            await writer.close(flush=False)

    async def _recreate(self, driver, path, consumer, **kwargs):
        try:
            await driver.topic_client.drop_topic(path)
        except ydb.SchemeError:
            pass
        await driver.topic_client.create_topic(path=path, consumers=[consumer], **kwargs)

    def _auto_partitioning(self):
        return ydb.TopicAutoPartitioningSettings(
            strategy=ydb.TopicAutoPartitioningStrategy.SCALE_UP,
            up_utilization_percent=1,
            down_utilization_percent=1,
            stabilization_window=datetime.timedelta(seconds=1),
        )

    async def test_key_range_exposed_for_autopartitioned_topic(self, driver, database, topic_consumer):
        path = database + "/mw-keyrange"
        await self._recreate(
            driver,
            path,
            topic_consumer,
            min_active_partitions=2,
            max_active_partitions=50,
            auto_partitioning_settings=self._auto_partitioning(),
        )
        desc = await driver.topic_client.describe_topic(path)
        assert any(p.key_range is not None for p in desc.partitions)

    async def test_write_by_key_preserves_per_key_order(self, driver, database, topic_consumer):
        path = database + "/mw-plain"
        await self._recreate(driver, path, topic_consumer, min_active_partitions=3)

        keys = ["user-1", "user-2", "user-3", "user-4", "user-5"]
        per_key = 8
        async with driver.topic_client.multiwriter(path, producer_id_prefix="mw") as writer:
            await writer.wait_init()
            assert isinstance(writer._chooser, ydb.TopicWriterPartitionByKeyKafka)
            for i in range(per_key):
                for key in keys:
                    await writer.write(ydb.TopicWriterMessage(data=("%s:%d" % (key, i)).encode(), key=key))
            await writer.flush()

        total = per_key * len(keys)
        received = {key: [] for key in keys}
        async with driver.topic_client.reader(path, consumer=topic_consumer) as reader:
            for _ in range(total):
                message = await asyncio.wait_for(reader.receive_message(), timeout=30)
                key, index = message.data.decode().split(":")
                received[key].append(int(index))
                reader.commit(message)

        for key in keys:
            assert received[key] == list(range(per_key)), (key, received[key])

    async def test_write_by_key_on_autopartitioned_topic(self, driver, database, topic_consumer):
        path = database + "/mw-auto"
        await self._recreate(
            driver,
            path,
            topic_consumer,
            min_active_partitions=2,
            max_active_partitions=50,
            auto_partitioning_settings=self._auto_partitioning(),
        )

        keys = ["alpha", "beta", "gamma", "delta"]
        per_key = 5
        async with driver.topic_client.multiwriter(path, producer_id_prefix="mw") as writer:
            await writer.wait_init()
            # auto-partitioned topics report key ranges -> adaptive default picks the bound chooser
            assert isinstance(writer._chooser, ydb.TopicWriterPartitionByKeyBound)
            for i in range(per_key):
                for key in keys:
                    # write_with_ack verifies the server accepts bound-routed writes
                    await writer.write_with_ack(ydb.TopicWriterMessage(data=("%s:%d" % (key, i)).encode(), key=key))

        total = per_key * len(keys)
        seen = 0
        async with driver.topic_client.reader(path, consumer=topic_consumer) as reader:
            for _ in range(total):
                message = await asyncio.wait_for(reader.receive_message(), timeout=30)
                seen += 1
                reader.commit(message)
        assert seen == total

    async def test_write_by_key_survives_partition_split(self, driver, database, topic_consumer):
        path = database + "/mw-split"
        await self._recreate(
            driver,
            path,
            topic_consumer,
            min_active_partitions=1,
            max_active_partitions=4,
            auto_partitioning_settings=ydb.TopicAutoPartitioningSettings(
                strategy=ydb.TopicAutoPartitioningStrategy.SCALE_UP,
                up_utilization_percent=90,
                down_utilization_percent=1,
                stabilization_window=datetime.timedelta(seconds=300),
            ),
        )

        async def wait_for_partitions(expected):
            deadline = asyncio.get_running_loop().time() + 30
            while True:
                description = await driver.topic_client.describe_topic(path)
                active = [partition for partition in description.partitions if partition.active]
                if len(active) == expected:
                    return description
                assert asyncio.get_running_loop().time() < deadline, (
                    "topic did not reach %d active partitions" % expected
                )
                await asyncio.sleep(0.1)

        description = await wait_for_partitions(1)
        assert len(description.partitions) == 1

        keys = ["k%d" % i for i in range(32)]
        written = 0
        async with driver.topic_client.multiwriter(path, producer_id_prefix="mw-split") as writer:
            await writer.wait_init()
            assert isinstance(writer._chooser, ydb.TopicWriterPartitionByKeyBound)

            async def write_batch(count):
                nonlocal written
                for _ in range(count):
                    key = keys[written % len(keys)]
                    await writer.write(ydb.TopicWriterMessage(data=("%d:%s" % (written, key)).encode(), key=key))
                    written += 1
                await writer.flush()

            await write_batch(50)

            await driver.topic_client.alter_topic(path, set_min_active_partitions=2)
            description = await wait_for_partitions(2)
            assert len(description.partitions) == 3
            root = next(partition for partition in description.partitions if not partition.parent_partition_ids)
            active_ids = {partition.partition_id for partition in description.partitions if partition.active}
            assert not root.active
            assert set(root.child_partition_ids) == active_ids
            await write_batch(100)

            await driver.topic_client.alter_topic(path, set_min_active_partitions=4)
            description = await wait_for_partitions(4)
            assert len(description.partitions) == 7
            await write_batch(100)

        total = written
        seen = set()
        last_by_key = {}
        async with driver.topic_client.reader(path, consumer=topic_consumer) as reader:
            while True:
                try:
                    message = await asyncio.wait_for(
                        reader.receive_message(),
                        timeout=30 if len(seen) < total else 2,
                    )
                except asyncio.TimeoutError:
                    assert len(seen) == total, "reader did not receive all messages"
                    break
                index_raw, key_raw = message.data.split(b":", 1)
                index = int(index_raw)
                key = key_raw.decode()
                assert index not in seen, "resend produced duplicate message %d" % index
                assert index > last_by_key.get(key, -1), "messages for key %s were reordered" % key
                last_by_key[key] = index
                seen.add(index)
                reader.commit(message)

        assert seen == set(range(total)), "some messages were lost"


class TestTopicMultiWriterSync:
    def test_flush_and_close_report_encoder_errors(self, driver_sync, database, topic_consumer):
        path = database + "/mw-sync-encoder-error"
        try:
            driver_sync.topic_client.drop_topic(path)
        except ydb.SchemeError:
            pass
        driver_sync.topic_client.create_topic(path=path, consumers=[topic_consumer])

        def failing_encoder(data):
            raise ValueError("encoder failed")

        writer = driver_sync.topic_client.multiwriter(
            path,
            codec=ydb.TopicCodec.GZIP,
            encoders={ydb.TopicCodec.GZIP: failing_encoder},
        )
        try:
            writer.write(ydb.TopicWriterMessage(data=b"payload", key="key"), timeout=10)
            with pytest.raises(ValueError, match="encoder failed"):
                writer.flush(timeout=10)
            with pytest.raises(ValueError, match="encoder failed"):
                writer.close(timeout=10)
            assert writer._closed
        finally:
            writer.close(flush=False, timeout=10)

    def test_write_by_key_preserves_per_key_order(self, driver_sync, database, topic_consumer):
        path = database + "/mw-sync"
        try:
            driver_sync.topic_client.drop_topic(path)
        except ydb.SchemeError:
            pass
        driver_sync.topic_client.create_topic(path=path, consumers=[topic_consumer], min_active_partitions=3)

        keys = ["a", "b", "c"]
        per_key = 6
        with driver_sync.topic_client.multiwriter(path, producer_id_prefix="mw-sync") as writer:
            for i in range(per_key):
                for key in keys:
                    writer.write(ydb.TopicWriterMessage(data=("%s:%d" % (key, i)).encode(), key=key))
            writer.flush()

        total = per_key * len(keys)
        received = {key: [] for key in keys}
        with driver_sync.topic_client.reader(path, consumer=topic_consumer) as reader:
            for _ in range(total):
                message = reader.receive_message(timeout=30)
                key, index = message.data.decode().split(":")
                received[key].append(int(index))
                reader.commit(message)

        for key in keys:
            assert received[key] == list(range(per_key)), (key, received[key])
