from __future__ import annotations

import asyncio
import copy
import dataclasses
import datetime
import gc
import gzip
import sys
import typing
import weakref
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty
from typing import List, Callable, Optional
from unittest import mock

import freezegun
import grpc
import pytest

from .. import aio
from .. import StatusCode, issues
from .._grpc.grpcwrapper.ydb_topic import (
    Codec,
    StreamWriteMessage,
    TransactionIdentity,
    UpdateTokenRequest,
    UpdateTokenResponse,
)
from .._grpc.grpcwrapper.common_utils import AsyncQueueToSyncIteratorAsyncIO, ServerStatus
from .topic_writer import (
    InternalMessage,
    PublicMessage,
    WriterSettings,
    PublicWriterSettings,
    PublicWriterInitInfo,
    PublicWriteResult,
    TopicWriterError,
    TopicWriterBufferFullError,
    TopicWriterClosedError,
    TopicWriterPartitionSplitError,
    TopicWriterStopped,
)
from .._grpc.grpcwrapper.ydb_topic_public_types import PublicCodec
from .._topic_common.test_helpers import StreamMock, wait_for_fast

from .topic_writer_asyncio import (
    WriterAsyncIOStream,
    WriterAsyncIOReconnector,
    WriterAsyncIO,
)
from .topic_writer_multi_asyncio import TopicWriterMultiAsyncIO, MultiWriterSettings
from .topic_writer_partition_chooser import (
    PublicPartitionByKeyKafka,
    PublicPartitionByKeyBound,
    PublicPartitionChooser,
    murmur2_32,
)
from .._grpc.grpcwrapper.ydb_topic_public_types import PublicDescribeTopicResult

from ..credentials import AnonymousCredentials

from .._constants import DEFAULT_INITIAL_RESPONSE_TIMEOUT


FAKE_TRANSACTION_IDENTITY = TransactionIdentity(
    tx_id="transaction_id",
    session_id="session_id",
)


@pytest.fixture
def default_driver() -> aio.Driver:
    driver = mock.Mock(spec=aio.Driver)
    driver._credentials = AnonymousCredentials()
    return driver


@pytest.mark.asyncio
class TestWriterAsyncIOStream:
    @dataclasses.dataclass
    class WriterWithMockedStream:
        writer: WriterAsyncIOStream
        stream: StreamMock

    @pytest.fixture
    def stream(self):
        stream = StreamMock()
        yield stream
        stream.close()

    @staticmethod
    async def get_started_writer(stream, *args, **kwargs) -> WriterAsyncIOStream:
        stream.from_server.put_nowait(
            StreamWriteMessage.InitResponse(
                last_seq_no=4,
                session_id="123",
                partition_id=3,
                supported_codecs=[Codec.CODEC_RAW, Codec.CODEC_GZIP],
                status=ServerStatus(StatusCode.SUCCESS, []),
            )
        )

        writer = WriterAsyncIOStream(*args, **kwargs)
        await writer._start(
            stream,
            init_message=StreamWriteMessage.InitRequest(
                path="/local/test",
                producer_id="producer-id",
                write_session_meta={"a": "b"},
                partitioning=StreamWriteMessage.PartitioningMessageGroupID(message_group_id="message-group-id"),
                get_last_seq_no=False,
            ),
        )
        await stream.from_client.get()
        return writer

    @pytest.fixture
    async def writer_and_stream(self, stream) -> WriterWithMockedStream:
        writer = await self.get_started_writer(stream)

        yield TestWriterAsyncIOStream.WriterWithMockedStream(
            stream=stream,
            writer=writer,
        )

        await writer.close()

    async def test_init_writer(self, stream):
        init_seqno = 4
        init_message = StreamWriteMessage.InitRequest(
            path="/local/test",
            producer_id="producer-id",
            write_session_meta={"a": "b"},
            partitioning=StreamWriteMessage.PartitioningMessageGroupID(message_group_id="message-group-id"),
            get_last_seq_no=False,
        )
        stream.from_server.put_nowait(
            StreamWriteMessage.InitResponse(
                last_seq_no=init_seqno,
                session_id="123",
                partition_id=0,
                supported_codecs=[],
                status=ServerStatus(StatusCode.SUCCESS, []),
            )
        )

        writer = WriterAsyncIOStream()
        await writer._start(stream, init_message)

        sent_message = await stream.from_client.get()
        expected_message = StreamWriteMessage.FromClient(init_message)

        assert expected_message == sent_message
        assert writer.last_seqno == init_seqno

        await writer.close()

    async def test_write_a_message(self, writer_and_stream: WriterWithMockedStream):
        data = "123".encode()
        now = datetime.datetime.now(datetime.timezone.utc)
        writer_and_stream.writer.write(
            [
                InternalMessage(
                    PublicMessage(
                        seqno=1,
                        created_at=now,
                        data=data,
                    )
                )
            ]
        )

        expected_message = StreamWriteMessage.FromClient(
            StreamWriteMessage.WriteRequest(
                codec=Codec.CODEC_RAW,
                tx_identity=None,
                messages=[
                    StreamWriteMessage.WriteRequest.MessageData(
                        seq_no=1,
                        created_at=now,
                        data=data,
                        metadata_items={},
                        uncompressed_size=len(data),
                        partitioning=None,
                    )
                ],
            )
        )

        sent_message = await writer_and_stream.stream.from_client.get()
        assert expected_message == sent_message

    async def test_write_a_message_with_tx(self, writer_and_stream: WriterWithMockedStream):
        writer_and_stream.writer._tx_identity = FAKE_TRANSACTION_IDENTITY

        data = "123".encode()
        now = datetime.datetime.now(datetime.timezone.utc)
        writer_and_stream.writer.write(
            [
                InternalMessage(
                    PublicMessage(
                        seqno=1,
                        created_at=now,
                        data=data,
                    )
                )
            ]
        )

        expected_message = StreamWriteMessage.FromClient(
            StreamWriteMessage.WriteRequest(
                codec=Codec.CODEC_RAW,
                tx_identity=FAKE_TRANSACTION_IDENTITY,
                messages=[
                    StreamWriteMessage.WriteRequest.MessageData(
                        seq_no=1,
                        created_at=now,
                        data=data,
                        metadata_items={},
                        uncompressed_size=len(data),
                        partitioning=None,
                    )
                ],
            )
        )

        sent_message = await writer_and_stream.stream.from_client.get()
        assert expected_message == sent_message

    async def test_update_token(self, stream: StreamMock):
        writer = await self.get_started_writer(stream, update_token_interval=0.1, get_token_function=lambda: "foo-bar")
        assert stream.from_client.empty()

        expected = StreamWriteMessage.FromClient(UpdateTokenRequest(token="foo-bar"))
        got = await wait_for_fast(stream.from_client.get())
        assert expected == got, "send update token request"

        await asyncio.sleep(0.2)
        assert stream.from_client.empty(), "no answer - no new update request"

        await stream.from_server.put(UpdateTokenResponse())
        receive_task = asyncio.create_task(writer.receive())

        got = await wait_for_fast(stream.from_client.get())
        assert expected == got

        receive_task.cancel()
        await asyncio.wait([receive_task])

        await writer.close()

    async def test_init_timeout_parameter(self, stream):
        """Test that WriterAsyncIOStream._start calls stream.receive with timeout=10"""
        writer_id = 1
        settings = WriterSettings(PublicWriterSettings("test-topic", "test-producer"))

        # Mock stream.receive to check if timeout is passed
        with mock.patch.object(stream, "receive") as mock_receive:
            mock_receive.return_value = StreamWriteMessage.InitResponse(
                last_seq_no=0,
                session_id="test_session",
                partition_id=1,
                supported_codecs=[Codec.CODEC_RAW],
                status=ServerStatus(StatusCode.SUCCESS, []),
            )

            writer = WriterAsyncIOStream(writer_id, settings)
            await writer._start(stream, settings.create_init_request())

            # Verify that receive was called with timeout
            mock_receive.assert_called_with(timeout=DEFAULT_INITIAL_RESPONSE_TIMEOUT)

        await writer.close()

    async def test_init_timeout_behavior(self, stream):
        """Test that WriterAsyncIOStream._start raises TopicWriterError when receive times out"""
        writer_id = 1
        settings = WriterSettings(PublicWriterSettings("test-topic", "test-producer"))

        # Mock stream.receive to directly raise TimeoutError when called with timeout
        async def timeout_receive(timeout=None):
            if timeout == DEFAULT_INITIAL_RESPONSE_TIMEOUT:
                raise asyncio.TimeoutError("Simulated timeout")
            return StreamWriteMessage.InitResponse(
                last_seq_no=0,
                session_id="test_session",
                partition_id=1,
                supported_codecs=[Codec.CODEC_RAW],
                status=ServerStatus(StatusCode.SUCCESS, []),
            )

        with mock.patch.object(stream, "receive", side_effect=timeout_receive):
            writer = WriterAsyncIOStream(writer_id, settings)

            # Should raise TopicWriterError with timeout message
            with pytest.raises(TopicWriterError, match="Timeout waiting for init response"):
                await writer._start(stream, settings.create_init_request())

        # Don't close writer since _start failed and _stream was never set


@pytest.mark.asyncio
class TestWriterAsyncIOReconnector:
    init_last_seqno = 0
    time_for_mocks = 1678046714.639387

    class StreamWriterMock:
        last_seqno: int
        supported_codecs: List[PublicCodec]

        from_client: asyncio.Queue
        from_server: asyncio.Queue

        _closed: bool

        def __init__(
            self,
            update_token_interval: Optional[int, float] = None,
            get_token_function: Optional[Callable[[], str]] = None,
        ):
            self._id = 0
            self.last_seqno = 0
            self.from_server = asyncio.Queue()
            self.from_client = asyncio.Queue()
            self._closed = False
            self.supported_codecs = []

        def write(self, messages: typing.List[InternalMessage]):
            if self._closed:
                raise Exception("write to closed StreamWriterMock")

            self.from_client.put_nowait(messages)

        async def receive(self) -> StreamWriteMessage.WriteResponse:
            if self._closed:
                raise Exception("read from closed StreamWriterMock")

            item = await self.from_server.get()
            if isinstance(item, Exception):
                raise item
            return item

        async def close(self):
            if self._closed:
                return
            self._closed = True

    @pytest.fixture(autouse=True)
    async def stream_writer_double_queue(self, monkeypatch):
        class DoubleQueueWriters:
            _first: Queue
            _second: Queue

            def __init__(self):
                self._first = Queue()
                self._second = Queue()

            def get_first(self):
                try:
                    return self._first.get_nowait()
                except Empty:
                    self._create()
                    return self.get_first()

            def get_second(self):
                try:
                    return self._second.get_nowait()
                except Empty:
                    self._create()
                    return self.get_second()

            def _create(self):
                writer = TestWriterAsyncIOReconnector.StreamWriterMock()
                writer.last_seqno = TestWriterAsyncIOReconnector.init_last_seqno
                self._first.put_nowait(writer)
                self._second.put_nowait(writer)

        res = DoubleQueueWriters()

        async def async_create(driver, init_message, token_getter, tx_identity):
            return res.get_first()

        monkeypatch.setattr(WriterAsyncIOStream, "create", async_create)
        return res

    @pytest.fixture
    def get_stream_writer(
        self, stream_writer_double_queue
    ) -> typing.Callable[[], "TestWriterAsyncIOReconnector.StreamWriterMock"]:
        return stream_writer_double_queue.get_second

    @pytest.fixture
    def default_settings(self) -> WriterSettings:
        return WriterSettings(
            PublicWriterSettings(
                topic="/local/topic",
                producer_id="test-producer",
                auto_seqno=False,
                auto_created_at=False,
                codec=PublicCodec.RAW,
                update_token_interval=3600,
            )
        )

    @pytest.fixture
    def default_write_statistic(
        self,
    ) -> StreamWriteMessage.WriteResponse.WriteStatistics:
        return StreamWriteMessage.WriteResponse.WriteStatistics(
            persisting_time=datetime.timedelta(milliseconds=1),
            min_queue_wait_time=datetime.timedelta(milliseconds=2),
            max_queue_wait_time=datetime.timedelta(milliseconds=3),
            partition_quota_wait_time=datetime.timedelta(milliseconds=4),
            topic_quota_wait_time=datetime.timedelta(milliseconds=5),
        )

    def make_default_ack_message(self, seq_no=1) -> StreamWriteMessage.WriteResponse:
        return StreamWriteMessage.WriteResponse(
            partition_id=1,
            acks=[
                StreamWriteMessage.WriteResponse.WriteAck(
                    seq_no=seq_no,
                    message_write_status=StreamWriteMessage.WriteResponse.WriteAck.StatusWritten(offset=1),
                )
            ],
            write_statistics=self.default_write_statistic,
        )

    @pytest.fixture
    async def reconnector(self, default_driver, default_settings) -> WriterAsyncIOReconnector:
        return WriterAsyncIOReconnector(default_driver, default_settings)

    async def test_reconnect_and_resent_non_acked_messages_on_retriable_error(
        self,
        reconnector: WriterAsyncIOReconnector,
        get_stream_writer,
        default_write_statistic,
    ):
        now = datetime.datetime.now(datetime.timezone.utc)
        data = "123".encode()

        message1 = PublicMessage(
            data=data,
            seqno=1,
            created_at=now,
        )
        message2 = PublicMessage(
            data=data,
            seqno=2,
            created_at=now,
        )
        await reconnector.write_with_ack_future([message1, message2])

        # sent to first stream
        stream_writer = get_stream_writer()

        messages = await stream_writer.from_client.get()
        assert [InternalMessage(message1), InternalMessage(message2)] == messages

        # ack first message
        stream_writer.from_server.put_nowait(self.make_default_ack_message(seq_no=1))

        stream_writer.from_server.put_nowait(issues.Overloaded("test"))

        second_writer = get_stream_writer()
        second_sent_msg = await second_writer.from_client.get()

        expected_messages = [InternalMessage(message2)]
        assert second_sent_msg == expected_messages

        second_writer.from_server.put_nowait(self.make_default_ack_message(seq_no=2))
        await reconnector.close(flush=True)

    async def test_reconnect_on_cancelled_error_from_receive(self, default_driver, default_settings, monkeypatch):
        stream_creates = 0
        stream_2_created = asyncio.Event()

        class StreamWriterCancelOnFirstReceive(TestWriterAsyncIOReconnector.StreamWriterMock):
            def __init__(self):
                super().__init__()
                self._first_receive = True

            async def receive(self):
                if self._first_receive:
                    self._first_receive = False
                    raise asyncio.CancelledError()
                await asyncio.Future()  # stream 2 stays alive

        async def create_mock(*args, **kwargs):
            nonlocal stream_creates
            stream_creates += 1
            writer = StreamWriterCancelOnFirstReceive()
            writer.last_seqno = TestWriterAsyncIOReconnector.init_last_seqno
            if stream_creates >= 2:
                stream_2_created.set()
            return writer

        with mock.patch.object(WriterAsyncIOStream, "create", create_mock):
            reconnector = WriterAsyncIOReconnector(default_driver, default_settings)
            try:
                # Bug: stream 2 is never created — _stop(CancelledError) kills the writer permanently.
                # After the fix: writer reconnects and stream 2 is created.
                await asyncio.wait_for(stream_2_created.wait(), timeout=2.0)
            except asyncio.TimeoutError:
                pytest.fail(
                    "Writer did not reconnect after CancelledError from receive() — "
                    "bug: _stop(CancelledError) permanently kills writer"
                )
            finally:
                await reconnector.close(False)

    async def test_stop_on_unexpected_exception(self, reconnector: WriterAsyncIOReconnector, get_stream_writer):
        class TestException(Exception):
            pass

        stream_writer = get_stream_writer()
        stream_writer.from_server.put_nowait(TestException())

        message = PublicMessage(
            data="123",
            seqno=3,
        )

        with pytest.raises(TestException):

            async def wait_stop():
                while True:
                    await reconnector.write_with_ack_future([message])
                    await asyncio.sleep(0.1)

            await asyncio.wait_for(wait_stop(), 1)

        with pytest.raises(TestException):
            await reconnector.close(flush=False)

    async def test_retriable_error_hook_stops_the_writer(self, default_driver, default_settings, get_stream_writer):
        """The hook must be able to end the connection loop on an otherwise retriable error.

        OVERLOADED normally means "back off and retry", but for the multi-partition writer it is
        also how a split announces itself: the partition went inactive and retrying against it
        would spin forever. The hook lets the owner claim such an error and stop the writer with a
        reason it can recognise, instead of the generic retry path swallowing it.
        """
        seen = []

        def hook(err):
            seen.append(err)
            return True

        settings = copy.deepcopy(default_settings)
        settings._on_check_retriable_error = hook
        reconnector = WriterAsyncIOReconnector(default_driver, settings)

        get_stream_writer().from_server.put_nowait(issues.Overloaded("Write to inactive partition 0"))

        with pytest.raises(TopicWriterPartitionSplitError):

            async def wait_stop():
                while True:
                    await reconnector.write_with_ack_future([PublicMessage(data="123", seqno=3)])
                    await asyncio.sleep(0.01)

            await asyncio.wait_for(wait_stop(), 2)

        assert seen and isinstance(seen[0], issues.Overloaded)

        with pytest.raises(TopicWriterPartitionSplitError):
            await reconnector.close(flush=False)

    async def test_retriable_error_hook_declining_keeps_default_retry(
        self, default_driver, default_settings, get_stream_writer
    ):
        """A hook that declines must leave the normal retry policy untouched."""
        settings = copy.deepcopy(default_settings)
        settings._on_check_retriable_error = lambda err: False
        reconnector = WriterAsyncIOReconnector(default_driver, settings)

        get_stream_writer().from_server.put_nowait(issues.Overloaded("ordinary overload"))
        await reconnector.write_with_ack_future([PublicMessage(data="123", seqno=3)])
        await asyncio.sleep(0.1)

        # Retriable error + declining hook -> the writer reconnected instead of stopping.
        assert not reconnector._stop_reason.done()
        await reconnector.close(flush=False)

    async def test_wait_init(self, default_driver, default_settings, get_stream_writer):
        init_seqno = 100
        expected_init_info = PublicWriterInitInfo(last_seqno=init_seqno, supported_codecs=[])
        with mock.patch.object(TestWriterAsyncIOReconnector, "init_last_seqno", init_seqno):
            reconnector = WriterAsyncIOReconnector(default_driver, default_settings)
            info = await reconnector.wait_init()
            assert info == expected_init_info

        reconnector._stream_connected.clear()

        # force reconnect
        with mock.patch.object(TestWriterAsyncIOReconnector, "init_last_seqno", init_seqno + 1):
            stream_writer = get_stream_writer()
            stream_writer.from_server.put_nowait(issues.Overloaded("test"))  # some retriable error
            await reconnector._stream_connected.wait()

            info = await reconnector.wait_init()
            assert info == expected_init_info

        await reconnector.close(flush=False)

    async def test_write_message(self, reconnector: WriterAsyncIOReconnector, get_stream_writer):
        stream_writer = get_stream_writer()
        message = PublicMessage(
            data="123",
            seqno=3,
        )
        await reconnector.write_with_ack_future([message])

        sent_messages = await asyncio.wait_for(stream_writer.from_client.get(), 1)
        assert sent_messages == [InternalMessage(message)]

        await reconnector.close(flush=False)

    async def test_buffer_full_timeout_raises(self, default_driver, get_stream_writer):
        # Soft limit: blocking starts when buffer >= limit.
        # First message is 10 bytes data + 64 overhead = 74 bytes; set limit=74 so the
        # second write finds buffer already at the limit and must wait.
        settings = WriterSettings(
            PublicWriterSettings(
                topic="/local/topic",
                producer_id="test-producer",
                auto_seqno=False,
                auto_created_at=False,
                codec=PublicCodec.RAW,
                max_buffer_size_bytes=74,
                buffer_wait_timeout_sec=0.1,
            )
        )
        reconnector = WriterAsyncIOReconnector(default_driver, settings)
        stream_writer = get_stream_writer()

        await reconnector.write_with_ack_future([PublicMessage(data=b"x" * 10, seqno=1)])
        await stream_writer.from_client.get()

        # buffer == limit (74) → second write blocks and times out
        with pytest.raises(TopicWriterBufferFullError, match="buffer full"):
            await reconnector.write_with_ack_future([PublicMessage(data=b"y" * 10, seqno=2)])

        await reconnector.close(flush=False)

    async def test_buffer_freed_by_ack_allows_next_write(self, default_driver, get_stream_writer):
        # limit=74 matches one message (10 data + 64 overhead); second write blocks
        # until the first is acked and buffer drops to 0 < 74.
        settings = WriterSettings(
            PublicWriterSettings(
                topic="/local/topic",
                producer_id="test-producer",
                auto_seqno=False,
                auto_created_at=False,
                codec=PublicCodec.RAW,
                max_buffer_size_bytes=74,
                buffer_wait_timeout_sec=5.0,
            )
        )
        reconnector = WriterAsyncIOReconnector(default_driver, settings)
        stream_writer = get_stream_writer()

        await reconnector.write_with_ack_future([PublicMessage(data=b"x" * 10, seqno=1)])
        await stream_writer.from_client.get()

        # Ack the first message to free buffer space
        stream_writer.from_server.put_nowait(self.make_default_ack_message(seq_no=1))

        # Second write must succeed once buffer is freed
        await reconnector.write_with_ack_future([PublicMessage(data=b"y" * 10, seqno=2)])

        stream_writer.from_server.put_nowait(self.make_default_ack_message(seq_no=2))
        await reconnector.close(flush=True)

    async def test_concurrent_writers_only_one_proceeds_after_ack(self, default_driver, get_stream_writer):
        # Soft-limit semantics: blocking starts when buffer >= limit.
        # limit=74 (one message: 10 data + 64 overhead).
        # msg1 fills buffer to 74 >= 74 → tasks 2 and 3 both block.
        # Ack msg1 → buffer=0 < 74 → event fires, both tasks wake up.
        # First task to run adds 94 bytes (30+64) → buffer=94 >= 74.
        # Second task checks again and finds buffer still at limit → stays blocked.
        settings = WriterSettings(
            PublicWriterSettings(
                topic="/local/topic",
                producer_id="test-producer",
                auto_seqno=False,
                auto_created_at=False,
                codec=PublicCodec.RAW,
                max_buffer_size_bytes=74,
                buffer_wait_timeout_sec=5.0,
            )
        )
        reconnector = WriterAsyncIOReconnector(default_driver, settings)
        stream_writer = get_stream_writer()

        await reconnector.write_with_ack_future([PublicMessage(data=b"x" * 10, seqno=1)])
        await stream_writer.from_client.get()

        task2 = asyncio.create_task(reconnector.write_with_ack_future([PublicMessage(data=b"y" * 30, seqno=2)]))
        task3 = asyncio.create_task(reconnector.write_with_ack_future([PublicMessage(data=b"z" * 30, seqno=3)]))

        # Let both tasks start and reach their buffer-wait await point
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        assert not task2.done()
        assert not task3.done()

        # Ack msg1: buffer drops 74 → 0 < 74; one task proceeds and fills buffer again
        stream_writer.from_server.put_nowait(self.make_default_ack_message(seq_no=1))

        done, pending = await asyncio.wait([task2, task3], timeout=1.0, return_when=asyncio.FIRST_COMPLETED)
        assert len(done) == 1, "exactly one write should proceed after ack"
        assert len(pending) == 1, "other write should still be waiting for buffer space"
        assert not next(iter(pending)).done()

        pending_task = next(iter(pending))
        pending_task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await pending_task
        await reconnector.close(flush=False)

    async def test_buffer_messages_limit_raises_on_timeout(self, default_driver, get_stream_writer):
        settings = WriterSettings(
            PublicWriterSettings(
                topic="/local/topic",
                producer_id="test-producer",
                auto_seqno=False,
                auto_created_at=False,
                codec=PublicCodec.RAW,
                max_buffer_messages=1,
                buffer_wait_timeout_sec=0.1,
            )
        )
        reconnector = WriterAsyncIOReconnector(default_driver, settings)
        get_stream_writer()

        await reconnector.write_with_ack_future([PublicMessage(data=b"x", seqno=1)])

        with pytest.raises(TopicWriterBufferFullError, match="buffer full"):
            await reconnector.write_with_ack_future([PublicMessage(data=b"y", seqno=2)])

        await reconnector.close(flush=False)

    async def test_buffer_messages_limit_freed_by_ack(self, default_driver, get_stream_writer):
        settings = WriterSettings(
            PublicWriterSettings(
                topic="/local/topic",
                producer_id="test-producer",
                auto_seqno=False,
                auto_created_at=False,
                codec=PublicCodec.RAW,
                max_buffer_messages=1,
                buffer_wait_timeout_sec=5.0,
            )
        )
        reconnector = WriterAsyncIOReconnector(default_driver, settings)
        stream_writer = get_stream_writer()

        await reconnector.write_with_ack_future([PublicMessage(data=b"x", seqno=1)])
        await stream_writer.from_client.get()

        stream_writer.from_server.put_nowait(self.make_default_ack_message(seq_no=1))

        await reconnector.write_with_ack_future([PublicMessage(data=b"y", seqno=2)])

        stream_writer.from_server.put_nowait(self.make_default_ack_message(seq_no=2))
        await reconnector.close(flush=True)

    async def test_auto_seq_no(self, default_driver, default_settings, get_stream_writer):
        last_seq_no = 100
        with mock.patch.object(TestWriterAsyncIOReconnector, "init_last_seqno", last_seq_no):
            settings = copy.deepcopy(default_settings)
            settings.auto_seqno = True

            reconnector = WriterAsyncIOReconnector(default_driver, settings)

            await reconnector.write_with_ack_future([PublicMessage(data="123")])
            await reconnector.write_with_ack_future([PublicMessage(data="456")])

            stream_writer = get_stream_writer()

            sent = await stream_writer.from_client.get()
            assert [
                InternalMessage(PublicMessage(seqno=last_seq_no + 1, data="123")),
                InternalMessage(PublicMessage(seqno=last_seq_no + 2, data="456")),
            ] == sent

        with pytest.raises(TopicWriterError):
            await reconnector.write_with_ack_future([PublicMessage(seqno=last_seq_no + 3, data="123")])

        await reconnector.close(flush=False)

    async def test_write_multiple_messages_batched_into_single_send(
        self, reconnector: WriterAsyncIOReconnector, get_stream_writer
    ):
        stream_writer = get_stream_writer()
        messages = [
            PublicMessage(data="msg1", seqno=1),
            PublicMessage(data="msg2", seqno=2),
            PublicMessage(data="msg3", seqno=3),
        ]
        await reconnector.write_with_ack_future(messages)

        sent = await asyncio.wait_for(stream_writer.from_client.get(), 1)
        assert sent == [InternalMessage(m) for m in messages]
        assert stream_writer.from_client.empty()

        await reconnector.close(flush=False)

    async def test_buffered_messages_on_reconnect_sent_as_single_batch(
        self,
        reconnector: WriterAsyncIOReconnector,
        get_stream_writer,
    ):
        stream_writer = get_stream_writer()
        messages = [
            PublicMessage(data="msg1", seqno=1),
            PublicMessage(data="msg2", seqno=2),
            PublicMessage(data="msg3", seqno=3),
        ]
        await reconnector.write_with_ack_future(messages)

        sent = await asyncio.wait_for(stream_writer.from_client.get(), 5)
        assert len(sent) == 3

        # ack first message, then trigger retriable error
        stream_writer.from_server.put_nowait(self.make_default_ack_message(seq_no=1))
        stream_writer.from_server.put_nowait(issues.Overloaded("test"))

        second_writer = get_stream_writer()
        # backoff after Overloaded can sleep up to 1s, so allow generous timeout
        resent = await asyncio.wait_for(second_writer.from_client.get(), 5)

        # msg2 and msg3 must arrive as a single batch, not two separate sends
        assert resent == [InternalMessage(messages[1]), InternalMessage(messages[2])]
        assert second_writer.from_client.empty()

        second_writer.from_server.put_nowait(self.make_default_ack_message(seq_no=2))
        second_writer.from_server.put_nowait(self.make_default_ack_message(seq_no=3))
        await reconnector.close(flush=True)

    async def test_deny_double_seqno(self, reconnector: WriterAsyncIOReconnector, get_stream_writer):
        writer = get_stream_writer()

        await reconnector.write_with_ack_future([PublicMessage(seqno=10, data="123")])
        writer.from_server.put_nowait(self.make_default_ack_message(seq_no=10))

        with pytest.raises(TopicWriterError):
            await reconnector.write_with_ack_future([PublicMessage(seqno=9, data="123")])

        with pytest.raises(TopicWriterError):
            await reconnector.write_with_ack_future([PublicMessage(seqno=10, data="123")])

        await reconnector.write_with_ack_future([PublicMessage(seqno=11, data="123")])
        writer.from_server.put_nowait(self.make_default_ack_message(seq_no=11))

        await reconnector.close(flush=True)

    @freezegun.freeze_time("2022-01-13 20:50:00", tz_offset=0)
    async def test_auto_created_at(self, default_driver, default_settings, get_stream_writer):
        now = datetime.datetime.now(datetime.timezone.utc)

        settings = copy.deepcopy(default_settings)
        settings.auto_created_at = True
        reconnector = WriterAsyncIOReconnector(default_driver, settings)
        await reconnector.write_with_ack_future([PublicMessage(seqno=4, data="123")])

        stream_writer = get_stream_writer()
        sent = await stream_writer.from_client.get()

        assert [InternalMessage(PublicMessage(seqno=4, data="123", created_at=now))] == sent
        await reconnector.close(flush=False)

    @pytest.mark.parametrize(
        "codec,write_datas,expected_codecs,expected_datas",
        [
            (
                PublicCodec.RAW,
                [b"123"],
                [PublicCodec.RAW],
                [b"123"],
            ),
            (
                PublicCodec.GZIP,
                [b"123"],
                [PublicCodec.GZIP],
                [gzip.compress(b"123", mtime=time_for_mocks)],
            ),
            (
                None,
                [b"123", b"456", b"789", b"0" * 1000],
                [PublicCodec.RAW, PublicCodec.GZIP, PublicCodec.RAW, PublicCodec.RAW],
                [
                    b"123",
                    gzip.compress(b"456", mtime=time_for_mocks),
                    b"789",
                    b"0" * 1000,
                ],
            ),
            (
                None,
                [b"123", b"456", b"789" * 1000, b"0"],
                [PublicCodec.RAW, PublicCodec.GZIP, PublicCodec.GZIP, PublicCodec.GZIP],
                [
                    b"123",
                    gzip.compress(b"456", mtime=time_for_mocks),
                    gzip.compress(b"789" * 1000, mtime=time_for_mocks),
                    gzip.compress(b"0", mtime=time_for_mocks),
                ],
            ),
        ],
    )
    async def test_select_codecs(
        self,
        default_driver: aio.Driver,
        default_settings: WriterSettings,
        monkeypatch,
        write_datas: List[typing.Optional[bytes]],
        codec: typing.Optional[PublicCodec],
        expected_codecs: List[PublicCodec],
        expected_datas: List[bytes],
    ):
        assert len(write_datas) == len(expected_datas)
        assert len(expected_codecs) == len(expected_datas)

        settings = copy.copy(default_settings)
        settings.codec = codec
        settings.auto_seqno = True
        reconnector = WriterAsyncIOReconnector(default_driver, settings)

        added_messages = asyncio.Queue()  # type: asyncio.Queue[List[InternalMessage]]

        def add_messages(_self, messages: typing.List[InternalMessage]):
            added_messages.put_nowait(messages)

        monkeypatch.setattr(WriterAsyncIOReconnector, "_add_messages_to_send_queue", add_messages)
        monkeypatch.setattr("time.time", lambda: TestWriterAsyncIOReconnector.time_for_mocks)

        for i in range(len(expected_datas)):
            await reconnector.write_with_ack_future([PublicMessage(data=write_datas[i])])
            mess = await asyncio.wait_for(added_messages.get(), timeout=600)
            mess = mess[0]

            assert mess.codec == expected_codecs[i]
            if expected_codecs[i] == PublicCodec.GZIP:
                # The gzip header embeds an mtime that differs across Python
                # versions (3.14 defaults it to 0 regardless of time.time), so
                # compare the decompressed payload instead of the raw bytes.
                assert gzip.decompress(mess.get_data_bytes()) == gzip.decompress(expected_datas[i])
            else:
                assert mess.get_data_bytes() == expected_datas[i]

        await reconnector.close(flush=False)

    @pytest.mark.parametrize(
        "codec,data",
        [
            (
                PublicCodec.RAW,
                [b"123", b"456", b"789", b"0"],
            ),
            (
                PublicCodec.GZIP,
                [b"123", b"456", b"789", b"0"],
            ),
        ],
    )
    async def test_encode_data_inplace(
        self,
        reconnector: WriterAsyncIOReconnector,
        codec: PublicCodec,
        data: List[bytes],
    ):
        f = reconnector._codec_functions[codec]
        expected_datas = [f(item) for item in data]

        messages = [InternalMessage(PublicMessage(item)) for item in data]
        await reconnector._encode_data_inplace(codec, messages)

        for index, mess in enumerate(messages):
            assert mess.codec == codec
            assert mess.get_data_bytes() == expected_datas[index]

        await reconnector.close(flush=True)

    async def test_custom_encoder(self, default_driver, default_settings, get_stream_writer):
        codec = 10001

        settings = copy.copy(default_settings)
        settings.encoders = {codec: lambda x: bytes(reversed(x))}
        settings.codec = codec
        reconnector = WriterAsyncIOReconnector(default_driver, settings)

        now = datetime.datetime.now(datetime.timezone.utc)
        seqno = self.init_last_seqno + 1

        await reconnector.write_with_ack_future([PublicMessage(data=b"123", seqno=seqno, created_at=now)])

        stream_writer = get_stream_writer()
        sent_messages = await wait_for_fast(stream_writer.from_client.get())

        expected_mess = InternalMessage(PublicMessage(data=b"321", seqno=seqno, created_at=now))
        expected_mess.codec = codec

        assert sent_messages == [expected_mess]

        await reconnector.close(flush=False)


@pytest.mark.asyncio
class TestWriterAsyncIO:
    class ReconnectorMock:
        lock: asyncio.Lock
        messages: typing.List[InternalMessage]
        futures: typing.List[asyncio.Future]
        messages_writted: asyncio.Event

        def __init__(self):
            self.lock = asyncio.Lock()
            self.messages = []
            self.futures = []
            self.messages_writted = asyncio.Event()

        async def write_with_ack_future(self, messages: typing.List[InternalMessage]):
            async with self.lock:
                futures = [asyncio.Future() for _ in messages]
                self.messages.extend(messages)
                self.futures.extend(futures)
                self.messages_writted.set()
                return futures

        async def close(self, flush: bool):
            pass

    @pytest.fixture
    def default_settings(self) -> PublicWriterSettings:
        return PublicWriterSettings(
            topic="/local/topic",
            producer_id="producer-id",
        )

    @pytest.fixture(autouse=True)
    def mock_reconnector_init(self, monkeypatch, reconnector):
        def t(cls, driver, settings):
            return reconnector

        monkeypatch.setattr(WriterAsyncIOReconnector, "__new__", t)

    @pytest.fixture
    def reconnector(self, monkeypatch) -> TestWriterAsyncIO.ReconnectorMock:
        reconnector = TestWriterAsyncIO.ReconnectorMock()
        return reconnector

    @pytest.fixture
    async def writer(self, default_driver, default_settings):
        return WriterAsyncIO(default_driver, default_settings)

    async def test_write(self, writer: WriterAsyncIO, reconnector):
        m = PublicMessage(seqno=1, data="123")
        res = await writer.write(m)
        assert res is None

        assert reconnector.messages == [m]

    async def test_write_with_futures(self, writer: WriterAsyncIO, reconnector):
        m = PublicMessage(seqno=1, data="123")
        res = await writer.write_with_ack_future(m)

        assert reconnector.messages == [m]
        assert asyncio.isfuture(res)

    async def test_write_with_ack(self, writer: WriterAsyncIO, reconnector):
        reconnector.messages_writted.clear()

        async def ack_first_message():
            await reconnector.messages_writted.wait()
            async with reconnector.lock:
                reconnector.futures[0].set_result(PublicWriteResult.Written(offset=1))

        asyncio.create_task(ack_first_message())

        m = PublicMessage(seqno=1, data="123")
        res = await writer.write_with_ack(m)

        assert res == PublicWriteResult.Written(offset=1)

        reconnector.messages_writted.clear()
        async with reconnector.lock:
            reconnector.messages.clear()
            reconnector.futures.clear()

        async def ack_next_messages():
            await reconnector.messages_writted.wait()
            async with reconnector.lock:
                reconnector.futures[0].set_result(PublicWriteResult.Written(offset=2))
                reconnector.futures[1].set_result(PublicWriteResult.Skipped())

        asyncio.create_task(ack_next_messages())

        res = await writer.write_with_ack([PublicMessage(seqno=2, data="123"), PublicMessage(seqno=3, data="123")])
        assert res == [PublicWriteResult.Written(offset=2), PublicWriteResult.Skipped()]


_STREAM_WRITE_METHOD = "/Ydb.Topic.V1.TopicService/StreamWrite"


# The exact code object the leaked gRPC consumption thread blocks in. Matching the code
# object (instead of a module filename) avoids false positives from same-named modules in
# other dependencies and survives file renames / refactors.
_CONSUMER_NEXT_CODE = AsyncQueueToSyncIteratorAsyncIO.__next__.__code__


def _count_stranded_consumer_threads() -> int:
    """Number of threads parked in AsyncQueueToSyncIteratorAsyncIO.__next__ (the leak)."""
    count = 0
    for frame in sys._current_frames().values():
        f: typing.Optional[typing.Any] = frame
        while f is not None:
            if f.f_code is _CONSUMER_NEXT_CODE:
                count += 1
                break
            f = f.f_back
    return count


class _AbortingStreamServer:
    """In-process gRPC server that accepts StreamWrite then immediately drops the stream."""

    def __init__(self):
        def handler(request_iterator, context):
            try:
                next(request_iterator)  # consume the client's init request
            except Exception:
                pass
            context.abort(grpc.StatusCode.UNAVAILABLE, "simulated node down")

        rpc = grpc.stream_stream_rpc_method_handler(
            handler,
            request_deserializer=lambda b: b,
            response_serializer=lambda b: b,
        )

        class _Generic(grpc.GenericRpcHandler):
            def service(self, details):
                return rpc if details.method == _STREAM_WRITE_METHOD else None

        self._server = grpc.server(ThreadPoolExecutor(max_workers=4))
        self.port = self._server.add_insecure_port("127.0.0.1:0")
        self._server.add_generic_rpc_handlers((_Generic(),))
        self._server.start()

    def stop(self):
        self._server.stop(grace=1).wait(timeout=10)


class _FakeSyncDriver:
    """Minimal stand-in for ydb.Driver's call interface used by _start_sync_driver."""

    _credentials = None

    def __init__(self, channel: grpc.Channel):
        self._channel = channel

    def __call__(self, request_iterator, stub, method, executor=None, settings=None, **kwargs):
        multicallable = self._channel.stream_stream(
            _STREAM_WRITE_METHOD,
            request_serializer=lambda m: m.SerializeToString(),
            response_deserializer=lambda b: b,
        )
        return multicallable(request_iterator)


@pytest.mark.asyncio
async def test_writer_create_failure_does_not_leak_grpc_thread():
    """Regression: a failed WriterAsyncIOStream.create() must not strand a gRPC consumer thread.

    Uses a real in-process gRPC stream so the consumption thread is actually spawned;
    mocked-create tests cannot catch this leak.
    """
    server = _AbortingStreamServer()
    channel = grpc.insecure_channel("127.0.0.1:%d" % server.port)
    driver = _FakeSyncDriver(channel)
    init = WriterSettings(PublicWriterSettings("/local/topic", "producer-id")).create_init_request()

    try:
        baseline = _count_stranded_consumer_threads()
        attempts = 10
        for _ in range(attempts):
            with pytest.raises(issues.Error):
                await WriterAsyncIOStream.create(driver, init)  # type: ignore[arg-type]

        # Give closed streams a moment to let their consumption threads exit, then assert
        # the count returned to the baseline (no net new stranded threads vs other tests).
        leaked = attempts
        for _ in range(30):
            gc.collect()
            await asyncio.sleep(0.1)
            leaked = _count_stranded_consumer_threads() - baseline
            if leaked <= 0:
                break

        assert leaked <= 0, "%d gRPC consumer threads leaked after %d failed create() calls" % (
            leaked,
            attempts,
        )
    finally:
        channel.close()
        server.stop()


class _PublicDescription:
    def __init__(self, partitions):
        self.partitions = partitions


class _MultiFakeDescribeDriver:
    """Fake driver that answers DescribeTopic with a sequence of descriptions."""

    _credentials = AnonymousCredentials()

    def __init__(self, descriptions):
        self._descriptions = list(descriptions)
        self.describe_calls = 0

    async def __call__(self, request, stub, method, wrapper=None, *args, **kwargs):
        idx = min(self.describe_calls, len(self._descriptions) - 1)
        self.describe_calls += 1
        description = _PublicDescription(self._descriptions[idx])

        class _Result:
            def to_public(self):
                return description

        return _Result()


_real_sleep = asyncio.sleep


async def _no_sleep(_delay):
    """Run timer-driven loops at full speed. Holds the real sleep so patching
    asyncio.sleep with this does not make it call itself."""
    await _real_sleep(0)


# Per-partition last persisted seqno seen by the fakes' wait_init(); tests mutate it.
_FAKE_LAST_SEQNO: dict = {}


class _FakeSubWriter:
    """Stand-in for a per-partition WriterAsyncIO used by the multi-writer.

    Acks every write immediately.
    """

    def __init__(self, driver, settings):
        self.settings = settings
        self.partition_id = settings.partition_id
        self.producer_id = settings.producer_id
        self.split_hook = settings._on_check_retriable_error
        self.messages: List = []
        self.closed = False
        # The server keys persisted state by producer id, not by the partition a session happens
        # to be pinned to: that is why an unpinned probe session can still report the last_seqno
        # of a partition that has already gone inactive. Keying the fake on partition_id instead
        # would make every probe read 0 and hide whether the dedup cut works at all.
        self.producer_partition_id = int(settings.producer_id.rsplit("-", 1)[-1])

    async def wait_init(self):
        last_seqno = _FAKE_LAST_SEQNO.get(self.producer_partition_id, 0)
        return PublicWriterInitInfo(last_seqno=last_seqno, supported_codecs=[])

    async def write_with_ack_future(self, message):
        self.messages.append(message)
        future = asyncio.get_running_loop().create_future()
        future.set_result(PublicWriteResult.Written(offset=len(self.messages)))
        return future

    async def flush(self):
        pass

    async def close(self, flush=True):
        self.closed = True


class _ControllableSubWriter(_FakeSubWriter):
    """Sub-writer whose acks are resolved manually, to test split-resend."""

    def __init__(self, driver, settings):
        super().__init__(driver, settings)
        self.pending: List = []

    async def write_with_ack_future(self, message):
        self.messages.append(message)
        future = asyncio.get_running_loop().create_future()
        self.pending.append(future)
        return future

    def resolve_all(self):
        for i, future in enumerate(self.pending):
            if not future.done():
                future.set_result(PublicWriteResult.Written(offset=i))


class _KeyMapChooser(PublicPartitionChooser):
    """Deterministic chooser: routes by message key via a caller-controlled map."""

    def __init__(self, mapping):
        self._mapping = mapping
        self.partitions = set()

    def add_partitions(self, partitions):
        for p in partitions:
            self.partitions.add(p.partition_id)

    def remove_partition(self, partition_id):
        self.partitions.discard(partition_id)

    def choose_partition(self, message):
        return self._mapping[message.key]


class _FlushControlledSubWriter(_FakeSubWriter):
    """Sub-writer that acks buffered messages only when flush() is called."""

    def __init__(self, driver, settings):
        super().__init__(driver, settings)
        self.pending: List = []

    async def write_with_ack_future(self, message):
        self.messages.append(message)
        future = asyncio.get_running_loop().create_future()
        self.pending.append(future)
        return future

    async def flush(self):
        for i, future in enumerate(self.pending):
            if not future.done():
                future.set_result(PublicWriteResult.Written(offset=i))


class _RaisingSubWriter(_FakeSubWriter):
    """Sub-writer whose admission always fails."""

    async def write_with_ack_future(self, message):
        raise RuntimeError("admission failed")


class _CloseRaisesSubWriter(_ControllableSubWriter):
    """Sub-writer whose close() re-raises the split stop reason (like a real hook-stopped writer)."""

    async def close(self, flush=True):
        self.closed = True
        raise TopicWriterPartitionSplitError()


class _SeqnoGuardSubWriter(_ControllableSubWriter):
    """Sub-writer that enforces the real writer's explicit-seqno guard.

    With auto_seqno=False (what the multi-writer always uses) WriterAsyncIO seeds
    _last_known_seq_no from the server's last_seqno at init and then rejects any message with
    seq_no <= it -- see _prepare_internal_messages in topic_writer_asyncio.py. The plain fakes
    accept every seqno, which hides resend bugs on that boundary.
    """

    def __init__(self, driver, settings):
        super().__init__(driver, settings)
        self._last_known_seqno: Optional[int] = None

    async def wait_init(self):
        info = await super().wait_init()
        if self._last_known_seqno is None:
            self._last_known_seqno = info.last_seqno
        return info

    async def write_with_ack_future(self, message):
        if self._last_known_seqno is None:
            self._last_known_seqno = _FAKE_LAST_SEQNO.get(self.partition_id, 0)
        if message.seqno <= self._last_known_seqno:
            raise TopicWriterError("Message seqno is duplicated: %s" % message.seqno)
        self._last_known_seqno = message.seqno
        return await super().write_with_ack_future(message)


# Partitions whose sub-writer never finishes init; models a writer opened against a partition
# that is already inactive (observed live: such a writer hangs in init forever).
_FAKE_HANGING_INIT_PARTITIONS: set = set()


class _HangingInitSubWriter(_ControllableSubWriter):
    async def wait_init(self):
        if self.partition_id in _FAKE_HANGING_INIT_PARTITIONS:
            await asyncio.Event().wait()
        return await super().wait_init()


class _AckOnCloseSubWriter(_ControllableSubWriter):
    """Sub-writer whose outstanding acks land while the stream is being torn down.

    Models the server persisting (and acking) a message in the same moment the split is
    detected -- the ack races the quiesce that the repartition performs before reading its
    dedup cut.
    """

    async def close(self, flush=True):
        self.resolve_all()
        self.closed = True


def _retrieve_exceptions(futures) -> None:
    """Consume results so asyncio does not warn about never-retrieved exceptions."""
    for future in futures:
        if future.done() and not future.cancelled():
            future.exception()


def _multi_partition(partition_id, parents=None, children=None, from_bound=None, to_bound=None, active=True):
    key_range = None
    if from_bound is not None or to_bound is not None:
        key_range = PublicDescribeTopicResult.PartitionKeyRange(from_bound=from_bound or b"", to_bound=to_bound or b"")
    return PublicDescribeTopicResult.PartitionInfo(
        partition_id=partition_id,
        active=active,
        child_partition_ids=children or [],
        parent_partition_ids=parents or [],
        partition_stats=None,
        key_range=key_range,
    )


# Real YDB split topology (observed live against a cloud cluster): the split parent stays in the
# DescribeTopic result as an INACTIVE partition whose child_partition_ids point at the new leaves,
# and each child is active with parent_partition_ids == [parent]. Mocks below mirror that so the
# tests exercise the orchestrator's active/child filtering on realistic input.
def _split_parent(partition_id, children, parents=None):
    return _multi_partition(partition_id, parents=parents, children=children, active=False)


@pytest.mark.asyncio
class TestTopicWriterMultiAsyncIO:
    async def test_routes_messages_by_key(self):
        driver = _MultiFakeDescribeDriver([[_multi_partition(0), _multi_partition(1), _multi_partition(2)]])
        settings = MultiWriterSettings(
            topic="/local/topic",
            producer_id_prefix="pfx",
            partition_chooser=PublicPartitionByKeyKafka(),
        )
        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _FakeSubWriter):
            writer = TopicWriterMultiAsyncIO(driver, settings)
            await writer.wait_init()

            keys = ["a", "user-42", "hello", "мурмур2-хэш", "0", "zzz"]
            for key in keys:
                await writer.write(PublicMessage(b"payload", key=key))

            for key in keys:
                partition_id = (murmur2_32(key.encode("utf-8"), 0) & 0x7FFFFFFF) % 3
                sub = writer._writers[partition_id]
                assert sub.producer_id == "pfx-%d" % partition_id
                assert any(m.key == key for m in sub.messages)

            assert sum(len(w.messages) for w in writer._writers.values()) == len(keys)
            await writer.close(flush=False)

    async def test_split_reroutes_to_child_partitions(self):
        before = [_multi_partition(0), _multi_partition(1), _multi_partition(2)]
        after = [
            _split_parent(0, children=[3, 4]),  # split parent stays, inactive, with children
            _multi_partition(1),
            _multi_partition(2),
            _multi_partition(3, parents=[0]),
            _multi_partition(4, parents=[0]),
        ]
        driver = _MultiFakeDescribeDriver([before, after])
        settings = MultiWriterSettings(
            topic="/local/topic",
            producer_id_prefix="pfx",
            partition_chooser=PublicPartitionByKeyKafka(),
        )
        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _FakeSubWriter):
            writer = TopicWriterMultiAsyncIO(driver, settings)
            await writer.wait_init()

            sub0 = await writer._get_or_create_writer(0)
            await writer._on_partition_overloaded(0)

            assert sub0.closed
            assert 0 not in writer._writers
            assert 0 not in writer._partitions
            assert set(writer._partitions) == {1, 2, 3, 4}
            assert set(writer._chooser._partitions) == {1, 2, 3, 4}
            await writer.close(flush=False)

    async def test_split_resends_unacked_messages_with_dedup_cut(self):
        _FAKE_LAST_SEQNO.clear()
        # Route all three keys to partition 0 initially; after the split, spread them
        # across the two children.
        mapping = {"a": 0, "b": 0, "c": 0}
        chooser = _KeyMapChooser(mapping)
        before = [_multi_partition(0), _multi_partition(1)]
        after = [
            _split_parent(0, children=[2, 3]),  # split parent stays, inactive, with children
            _multi_partition(1),
            _multi_partition(2, parents=[0]),
            _multi_partition(3, parents=[0]),
        ]
        driver = _MultiFakeDescribeDriver([before, after])
        settings = MultiWriterSettings(topic="/local/topic", producer_id_prefix="pfx", partition_chooser=chooser)

        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _ControllableSubWriter):
            writer = TopicWriterMultiAsyncIO(driver, settings)
            await writer.wait_init()

            f_a = await writer.write_with_ack_future(PublicMessage(b"a", key="a"))  # partition 0, seqno 1
            f_b = await writer.write_with_ack_future(PublicMessage(b"b", key="b"))  # partition 0, seqno 2
            f_c = await writer.write_with_ack_future(PublicMessage(b"c", key="c"))  # partition 0, seqno 3
            assert set(writer._inflight[0]) == {1, 2, 3}

            # Ack the first message before the split: seqno 1 is now the dedup cut (max_acked),
            # and an acked message is already out of the in-flight set (never resent).
            writer._writers[0].pending[0].set_result(PublicWriteResult.Written(offset=0))
            await asyncio.sleep(0)
            assert f_a.done() and writer._max_acked.get(0) == 1
            assert set(writer._inflight[0]) == {2, 3}

            # Split: the un-acked b, c (seqno > cut) are re-routed to the children.
            mapping.update({"a": 2, "b": 3, "c": 2})
            await writer._on_partition_overloaded(0)

            assert 0 not in writer._inflight
            assert [m.key for m in writer._writers[3].messages] == ["b"]
            assert [m.key for m in writer._writers[2].messages] == ["c"]
            assert not f_b.done() and not f_c.done()

            writer._writers[2].resolve_all()
            writer._writers[3].resolve_all()
            await asyncio.sleep(0)
            assert f_b.done() and f_c.done()

            await writer.close(flush=False)

    async def test_adaptive_default_chooser(self):
        # A topic without key ranges -> Kafka hash chooser.
        driver_plain = _MultiFakeDescribeDriver([[_multi_partition(0), _multi_partition(1)]])
        # A topic that reports key ranges (auto-partitioning) -> bound chooser.
        driver_auto = _MultiFakeDescribeDriver(
            [[_multi_partition(0, from_bound=b"", to_bound=b"\x80"), _multi_partition(1, from_bound=b"\x80")]]
        )
        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _FakeSubWriter):
            plain = TopicWriterMultiAsyncIO(driver_plain, MultiWriterSettings(topic="/local/topic"))
            await plain.wait_init()
            assert isinstance(plain._chooser, PublicPartitionByKeyKafka)
            await plain.close(flush=False)

            auto = TopicWriterMultiAsyncIO(driver_auto, MultiWriterSettings(topic="/local/topic"))
            await auto.wait_init()
            assert isinstance(auto._chooser, PublicPartitionByKeyBound)
            await auto.close(flush=False)

    async def test_idle_writer_eviction(self):
        driver = _MultiFakeDescribeDriver([[_multi_partition(0), _multi_partition(1)]])
        chooser = _KeyMapChooser({"a": 0, "b": 1})
        settings = MultiWriterSettings(
            topic="/local/topic", producer_id_prefix="pfx", partition_chooser=chooser, writer_idle_timeout_sec=1000
        )
        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _ControllableSubWriter):
            writer = TopicWriterMultiAsyncIO(driver, settings)
            await writer.wait_init()

            f_a = await writer.write_with_ack_future(PublicMessage(b"a", key="a"))  # partition 0
            f_b = await writer.write_with_ack_future(PublicMessage(b"b", key="b"))  # partition 1
            assert set(writer._writers) == {0, 1}
            sub0 = writer._writers[0]

            # ack partition 0 (it goes idle); leave partition 1 un-acked
            sub0.resolve_all()
            await asyncio.sleep(0)
            assert not writer._inflight.get(0) and writer._inflight.get(1)

            # make both look old: only the idle partition 0 is evictable
            old = writer._loop.time() - 5000
            writer._last_write_at[0] = old
            writer._last_write_at[1] = old
            await writer._evict_idle_writers()

            assert 0 not in writer._writers and sub0.closed  # idle -> evicted
            assert 1 in writer._writers  # pending in-flight -> kept
            assert writer._seqno == 2  # writer-wide cursor survives eviction (a -> 1, b -> 2)

            # writing to partition 0 again recreates a fresh sub-writer; numbering continues from
            # the shared cursor rather than restarting for the re-opened partition
            f_a2 = await writer.write_with_ack_future(PublicMessage(b"a2", key="a"))
            assert 0 in writer._writers and writer._writers[0] is not sub0
            assert next(iter(writer._inflight[0])) == 3

            writer._writers[0].resolve_all()
            writer._writers[1].resolve_all()
            await asyncio.sleep(0)
            assert f_a.done() and f_b.done() and f_a2.done()
            await writer.close(flush=False)

    async def test_split_hook_detects_overloaded_only(self):
        # How the server signals a split (observed live): a split partition goes inactive, so the
        # next write to it fails on the write stream with OVERLOADED (status_code 400060),
        # message "Write to inactive partition N", surfaced by the SDK as issues.Overloaded.
        # The hook triggers on that exception TYPE (the message text is not inspected); any other
        # error is left to the writer's normal retry path.
        driver = _MultiFakeDescribeDriver([[_multi_partition(0)]])
        settings = MultiWriterSettings(topic="/local/topic", partition_chooser=PublicPartitionByKeyKafka())
        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _FakeSubWriter):
            writer = TopicWriterMultiAsyncIO(driver, settings)
            await writer.wait_init()

            observed: List[int] = []

            async def fake_split(partition_id):
                observed.append(partition_id)

            writer._on_partition_overloaded = fake_split
            hook = writer._make_overloaded_hook(0)

            split_signal = issues.Overloaded("status is not ok: Write to inactive partition 0")
            assert hook(split_signal) is True
            await asyncio.sleep(0)
            assert observed == [0]
            assert hook(RuntimeError("some other error")) is False

            await writer.close(flush=False)

    async def test_repartition_tolerates_subwriter_close_raising(self):
        # Regression: a hook-stopped sub-writer's close() re-raises TopicWriterPartitionSplitError.
        # Repartition must swallow it and still migrate to the child (not fall back to recovery).
        _FAKE_LAST_SEQNO.clear()
        mapping = {"a": 0}
        chooser = _KeyMapChooser(mapping)
        before = [_multi_partition(0), _multi_partition(1)]
        after = [
            _split_parent(0, children=[2, 3]),  # split parent stays, inactive, with children
            _multi_partition(1),
            _multi_partition(2, parents=[0]),
            _multi_partition(3, parents=[0]),
        ]
        driver = _MultiFakeDescribeDriver([before, after])
        settings = MultiWriterSettings(topic="/local/topic", producer_id_prefix="pfx", partition_chooser=chooser)

        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _CloseRaisesSubWriter):
            writer = TopicWriterMultiAsyncIO(driver, settings)
            await writer.wait_init()

            f_a = await writer.write_with_ack_future(PublicMessage(b"a", key="a"))  # partition 0
            mapping["a"] = 2  # after split, route to child 2

            await writer._on_partition_overloaded(0)  # must not raise despite close() raising

            assert 0 not in writer._partitions  # retired cleanly (no recovery fallback)
            assert [m.key for m in writer._writers[2].messages] == ["a"]  # migrated to the child
            assert 0 not in writer._inflight

            writer._writers[2].resolve_all()
            await asyncio.sleep(0)
            assert f_a.done()

            await writer.close(flush=False)

    async def test_merge_migrates_both_parents_to_shared_child(self):
        _FAKE_LAST_SEQNO.clear()
        # Two parents (0, 1) merge into one child (2), which lists both as parents. The bounds are
        # real ones: a merge child owns the ranges of BOTH parents, so it covers strictly more of
        # the key space than the parent whose OVERLOADED triggered the handler -- the child-range
        # coverage check must accept that, not just an exact tiling.
        mapping = {"x": 0, "y": 1}
        chooser = _KeyMapChooser(mapping)
        before = [
            _multi_partition(0, from_bound=b"", to_bound=b"\x80"),
            _multi_partition(1, from_bound=b"\x80", to_bound=b""),
        ]
        after = [_multi_partition(2, parents=[0, 1], from_bound=b"", to_bound=b"")]
        driver = _MultiFakeDescribeDriver([before, after])
        settings = MultiWriterSettings(topic="/local/topic", producer_id_prefix="pfx", partition_chooser=chooser)

        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _ControllableSubWriter):
            writer = TopicWriterMultiAsyncIO(driver, settings)
            await writer.wait_init()

            f_x = await writer.write_with_ack_future(PublicMessage(b"x", key="x"))  # partition 0
            f_y = await writer.write_with_ack_future(PublicMessage(b"y", key="y"))  # partition 1
            # One sequence for the whole writer, so the two partitions do not reuse a number and
            # the merge can carry both into the shared child unchanged.
            assert set(writer._inflight[0]) == {1} and set(writer._inflight[1]) == {2}

            # After the merge both keys route to the shared child 2.
            mapping.update({"x": 2, "y": 2})
            # Overloaded fired for partition 0 only; the handler must retire partition 1 too.
            await writer._on_partition_overloaded(0)

            assert set(writer._partitions) == {2}
            assert writer._chooser.partitions == {2}
            assert 0 not in writer._writers and 1 not in writer._writers
            assert sorted(m.key for m in writer._writers[2].messages) == ["x", "y"]
            assert 0 not in writer._inflight and 1 not in writer._inflight

            writer._writers[2].resolve_all()
            await asyncio.sleep(0)
            assert f_x.done() and f_y.done()

            await writer.close(flush=False)

    async def test_close_flushes_buffered_messages(self):
        driver = _MultiFakeDescribeDriver([[_multi_partition(0), _multi_partition(1), _multi_partition(2)]])
        settings = MultiWriterSettings(
            topic="/local/topic", producer_id_prefix="pfx", partition_chooser=PublicPartitionByKeyKafka()
        )
        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _FlushControlledSubWriter):
            writer = TopicWriterMultiAsyncIO(driver, settings)
            futures = [
                await writer.write_with_ack_future(PublicMessage(("m%d" % i).encode(), key="k%d" % i)) for i in range(5)
            ]
            assert not any(f.done() for f in futures)  # nothing acked yet

            await writer.close()  # flush=True must deliver the buffered messages

            assert all(f.done() and not f.cancelled() and f.exception() is None for f in futures)

    async def test_adaptive_chooser_single_open_range_partition(self):
        # A single auto-partitioned partition owns the fully-open range b""..b"".
        driver = _MultiFakeDescribeDriver([[_multi_partition(0, from_bound=b"", to_bound=b"")]])
        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _FakeSubWriter):
            writer = TopicWriterMultiAsyncIO(driver, MultiWriterSettings(topic="/local/topic"))
            await writer.wait_init()
            assert isinstance(writer._chooser, PublicPartitionByKeyBound)
            await writer.close(flush=False)

    async def test_transient_overload_recovers_partition_in_place(self):
        # DescribeTopic never shows children -> ordinary overload, not a repartition.
        driver = _MultiFakeDescribeDriver([[_multi_partition(0), _multi_partition(1)]])
        chooser = _KeyMapChooser({"a": 0})
        settings = MultiWriterSettings(topic="/local/topic", producer_id_prefix="pfx", partition_chooser=chooser)
        with mock.patch(
            "ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _ControllableSubWriter
        ), mock.patch("ydb._topic_writer.topic_writer_multi_asyncio._REPARTITION_DISCOVER_DELAY", 0), mock.patch(
            "ydb._topic_writer.topic_writer_multi_asyncio._REPARTITION_DISCOVER_ATTEMPTS", 2
        ):
            writer = TopicWriterMultiAsyncIO(driver, settings)
            await writer.wait_init()

            future = await writer.write_with_ack_future(PublicMessage(b"a", key="a"))
            old_sub = writer._writers[0]

            await writer._on_partition_overloaded(0)

            # partition kept (not retired); a fresh sub-writer resends the message
            assert 0 in writer._partitions
            new_sub = writer._writers[0]
            assert new_sub is not old_sub
            assert old_sub.closed
            assert [m.key for m in new_sub.messages] == ["a"]
            assert not future.done()

            new_sub.resolve_all()
            await asyncio.sleep(0)
            assert future.done()

            await writer.close(flush=False)

    async def test_enqueue_failure_does_not_leak_inflight(self):
        driver = _MultiFakeDescribeDriver([[_multi_partition(0), _multi_partition(1)]])
        chooser = _KeyMapChooser({"a": 0})
        settings = MultiWriterSettings(topic="/local/topic", producer_id_prefix="pfx", partition_chooser=chooser)
        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _RaisingSubWriter):
            writer = TopicWriterMultiAsyncIO(driver, settings)
            await writer.wait_init()

            with pytest.raises(RuntimeError):
                await writer.write_with_ack_future(PublicMessage(b"a", key="a"))

            assert not writer._inflight.get(0)  # no leaked entry, no pending future
            await writer.close(flush=False)

    async def test_duplicate_seqno_rejected_without_leak(self):
        driver = _MultiFakeDescribeDriver([[_multi_partition(0), _multi_partition(1)]])
        chooser = _KeyMapChooser({"a": 0, "b": 0})
        settings = MultiWriterSettings(
            topic="/local/topic", producer_id_prefix="pfx", partition_chooser=chooser, auto_seqno=False
        )
        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _ControllableSubWriter):
            writer = TopicWriterMultiAsyncIO(driver, settings)
            await writer.wait_init()

            first = await writer.write_with_ack_future(PublicMessage(b"a", key="a", seqno=5))
            with pytest.raises(TopicWriterError):
                await writer.write_with_ack_future(PublicMessage(b"b", key="b", seqno=5))

            assert set(writer._inflight[0]) == {5}
            await writer.close(flush=False)
            assert isinstance(first.exception(), TopicWriterStopped)  # retrieve to avoid warning

    async def test_unusable_partition_fails_its_inflight_instead_of_stranding_it(self):
        """When neither repartition nor recovery can serve a partition, its messages must fail.

        The children never complete the parent's range, so the topology is not committed; the
        parent is already inactive, so re-opening a writer for it times out too. Nothing is left
        that could ever ack these messages, and flush()/close(flush=True) wait on user futures
        without a deadline -- so leaving them pending hangs the caller forever.
        """
        _FAKE_LAST_SEQNO.clear()
        _FAKE_HANGING_INIT_PARTITIONS.clear()
        chooser = _KeyMapChooser({"a": 0})
        before = [_multi_partition(0, from_bound=b"", to_bound=b"")]
        # Only one child of the split ever shows up -> coverage check refuses to retire parent 0.
        partial = [
            _split_parent(0, children=[1, 2]),
            _multi_partition(1, parents=[0], from_bound=b"", to_bound=b"\x80"),
        ]
        driver = _MultiFakeDescribeDriver([before, partial])
        settings = MultiWriterSettings(topic="/local/topic", producer_id_prefix="pfx", partition_chooser=chooser)

        with mock.patch(
            "ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _HangingInitSubWriter
        ), mock.patch("ydb._topic_writer.topic_writer_multi_asyncio._WRITER_INIT_TIMEOUT", 0.1), mock.patch(
            "ydb._topic_writer.topic_writer_multi_asyncio._REPARTITION_DISCOVER_DELAY", 0
        ), mock.patch(
            "ydb._topic_writer.topic_writer_multi_asyncio._REPARTITION_DISCOVER_ATTEMPTS", 2
        ):
            writer = TopicWriterMultiAsyncIO(driver, settings)
            await writer.wait_init()
            future = await writer.write_with_ack_future(PublicMessage(b"a", key="a"))

            # Parent 0 has gone inactive: recovering it in place cannot finish init either.
            _FAKE_HANGING_INIT_PARTITIONS.add(0)
            try:
                await writer._on_partition_overloaded(0)

                assert future.done(), "in-flight message left without an owner"
                assert future.exception() is not None
                assert not writer._inflight.get(0)

                # The caller must be able to finish; both would hang on a pending future.
                await asyncio.wait_for(writer.flush(), timeout=1)
                await asyncio.wait_for(writer.close(flush=True), timeout=1)
            finally:
                _FAKE_HANGING_INIT_PARTITIONS.clear()
                await writer.close(flush=False)
                _retrieve_exceptions([future])

    async def test_repartition_tasks_are_coalesced_and_closed_with_the_writer(self):
        """Repartition must be owned by the writer, not fire-and-forget.

        A burst of OVERLOADED on one partition otherwise starts several concurrent recoveries of
        it, and any of them can outlive close() -- still describing the topic and opening
        sub-writers for a multi-writer the caller believes is shut down.
        """
        driver = _MultiFakeDescribeDriver([[_multi_partition(0), _multi_partition(1)]])
        settings = MultiWriterSettings(
            topic="/local/topic", producer_id_prefix="pfx", partition_chooser=PublicPartitionByKeyKafka()
        )
        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _FakeSubWriter):
            writer = TopicWriterMultiAsyncIO(driver, settings)
            await writer.wait_init()

            started: List[int] = []

            async def slow_repartition(partition_id):
                started.append(partition_id)
                await asyncio.sleep(30)

            writer._on_partition_overloaded = slow_repartition
            hook = writer._make_overloaded_hook(0)

            for _ in range(5):  # a burst for the same partition
                assert hook(issues.Overloaded("Write to inactive partition 0")) is True
            await asyncio.sleep(0)

            assert started == [0], "repeated signals for one partition must coalesce"
            task = writer._repartition_tasks[0]

            await writer.close(flush=False)
            assert task.done(), "close() must cancel and await the repartition task"
            assert not writer._repartition_tasks

            # After close no further signal may start work.
            assert hook(issues.Overloaded("again")) is True
            await asyncio.sleep(0)
            assert started == [0]

    async def test_merge_does_not_overwrite_a_colliding_manual_seqno(self):
        """Manual seqnos are unique per partition, so a merge can collide them in the child.

        Writing the migrated entry over the existing one would silently detach the displaced
        message: its ack callback becomes stale and its user future never resolves.
        """
        _FAKE_LAST_SEQNO.clear()
        mapping = {"x": 0, "y": 1}
        chooser = _KeyMapChooser(mapping)
        before = [_multi_partition(0), _multi_partition(1)]
        after = [_multi_partition(2, parents=[0, 1])]
        driver = _MultiFakeDescribeDriver([before, after])
        settings = MultiWriterSettings(
            topic="/local/topic", producer_id_prefix="pfx", partition_chooser=chooser, auto_seqno=False
        )

        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _ControllableSubWriter):
            writer = TopicWriterMultiAsyncIO(driver, settings)
            await writer.wait_init()

            # Same seqno on two different partitions: allowed today, both are in flight.
            f_x = await writer.write_with_ack_future(PublicMessage(b"x", key="x", seqno=7))
            f_y = await writer.write_with_ack_future(PublicMessage(b"y", key="y", seqno=7))
            assert set(writer._inflight[0]) == {7} and set(writer._inflight[1]) == {7}

            mapping.update({"x": 2, "y": 2})
            await writer._on_partition_overloaded(0)

            # Whatever the resolution, neither message may be silently dropped.
            assert len(writer._inflight.get(2, {})) + sum(f.done() for f in (f_x, f_y)) == 2

            writer._writers[2].resolve_all()
            await asyncio.sleep(0)
            assert f_x.done() and f_y.done(), "a colliding migration stranded a user future"

            await writer.close(flush=False)
            _retrieve_exceptions([f_x, f_y])

    async def test_message_persisted_with_a_lost_ack_is_not_resent_to_the_child(self):
        """The dedup cut has to come from the server, not from the acks we happened to receive.

        A split kills the session, and a message the server already persisted can lose its ack on
        the way back. Judging only by acks we saw, such a message looks unwritten, so it gets
        resent to the child -- where the parent's producer id no longer covers it, because each
        partition writes under its own. Nothing on the server can collapse the two, so the reader
        sees the message twice. Reading the cut from the retiring producer instead closes that
        window: the message is below it, and is reported written rather than resent.
        """
        _FAKE_LAST_SEQNO.clear()
        mapping = {"a": 0}
        chooser = _KeyMapChooser(mapping)
        before = [_multi_partition(0), _multi_partition(1)]
        after = [
            _split_parent(0, children=[2, 3]),
            _multi_partition(1),
            _multi_partition(2, parents=[0]),
            _multi_partition(3, parents=[0]),
        ]
        driver = _MultiFakeDescribeDriver([before, after])
        settings = MultiWriterSettings(topic="/local/topic", producer_id_prefix="pfx", partition_chooser=chooser)

        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _ControllableSubWriter):
            writer = TopicWriterMultiAsyncIO(driver, settings)
            await writer.wait_init()
            future = await writer.write_with_ack_future(PublicMessage(b"a", key="a"))  # seqno 1
            assert set(writer._inflight[0]) == {1}
            assert writer._max_acked.get(0, 0) == 0  # no ack ever reached us

            # The server did persist it: partition 0's producer is at seqno 1.
            _FAKE_LAST_SEQNO[0] = 1

            mapping["a"] = 2
            await writer._on_partition_overloaded(0)

            resent = [m.seqno for m in writer._writers[2].messages] if 2 in writer._writers else []
            assert resent == [], "a message the server had already persisted was resent to the child"
            assert future.done() and future.exception() is None, "the persisted message must resolve as written"
            assert not writer._inflight.get(0)

            await writer.close(flush=False)

    async def test_dedup_cut_covers_the_whole_lineage(self):
        """The cut must ask every ancestor, not just the partition being retired.

        Splits cascade, and a message keeps its seqno while its producer id changes with each
        move. So a number may have been persisted under a grandparent even though the partition
        we are retiring now knows nothing about it -- asking only the latest producer would
        under-report the cut and resend an already-written message.
        """
        _FAKE_LAST_SEQNO.clear()
        mapping = {"a": 2}
        chooser = _KeyMapChooser(mapping)
        # 0 split into 1 and 2 earlier; now 2 splits into 4 and 5.
        before = [_multi_partition(1, parents=[0]), _multi_partition(2, parents=[0])]
        after = [
            _split_parent(2, children=[4, 5], parents=[0]),
            _multi_partition(1, parents=[0]),
            _multi_partition(4, parents=[2]),
            _multi_partition(5, parents=[2]),
        ]
        driver = _MultiFakeDescribeDriver([before, after])
        settings = MultiWriterSettings(topic="/local/topic", producer_id_prefix="pfx", partition_chooser=chooser)

        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _ControllableSubWriter):
            writer = TopicWriterMultiAsyncIO(driver, settings)
            await writer.wait_init()
            future = await writer.write_with_ack_future(PublicMessage(b"a", key="a"))
            seqno = next(iter(writer._inflight[2]))

            # Grandparent 0 persisted this seqno; the retiring partition 2 reports nothing.
            _FAKE_LAST_SEQNO[0] = seqno
            assert writer._lineage(2) == [2, 0]

            mapping["a"] = 4
            await writer._on_partition_overloaded(2)

            resent = [m.seqno for m in writer._writers[4].messages] if 4 in writer._writers else []
            assert resent == [], "the grandparent's persisted seqno was ignored by the cut"
            assert future.done() and future.exception() is None

            await writer.close(flush=False)

    async def test_missing_manual_seqno_is_a_validation_error(self):
        driver = _MultiFakeDescribeDriver([[_multi_partition(0), _multi_partition(1)]])
        settings = MultiWriterSettings(
            topic="/local/topic",
            producer_id_prefix="pfx",
            partition_chooser=_KeyMapChooser({"a": 0}),
            auto_seqno=False,
        )
        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _ControllableSubWriter):
            writer = TopicWriterMultiAsyncIO(driver, settings)
            await writer.wait_init()

            # The writer is healthy; the message is what is wrong. Reporting this as
            # TopicWriterStopped tells the caller to give up on a writer that is still usable.
            with pytest.raises(TopicWriterError) as err:
                await writer.write_with_ack_future(PublicMessage(b"a", key="a"))
            assert not isinstance(err.value, TopicWriterStopped)

            await writer.close(flush=False)

    async def test_recovery_after_lost_ack_resends_the_remaining_messages(self):
        """A transient overload plus one ack lost with the stream must not strand the partition.

        The server persisted seqno 1 but its ack never reached us, so the message is still
        in-flight. _recover_partition resends the whole in-flight set to a fresh sub-writer for
        the same partition -- whose init reports last_seqno=1, so the real writer rejects seqno 1
        with "Message seqno is duplicated" before the server ever sees it. The resend loop is a
        plain `for`, so that exception also skips seqnos 2 and 3, which are never retried and
        never resolve.

        The comment on _recover_partition assumes the server dedups this retry; the client-side
        guard fires first, so it never gets the chance.
        """
        _FAKE_LAST_SEQNO.clear()
        driver = _MultiFakeDescribeDriver([[_multi_partition(0), _multi_partition(1)]])
        chooser = _KeyMapChooser({"a": 0})
        settings = MultiWriterSettings(topic="/local/topic", producer_id_prefix="pfx", partition_chooser=chooser)
        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _SeqnoGuardSubWriter), mock.patch(
            "ydb._topic_writer.topic_writer_multi_asyncio._REPARTITION_DISCOVER_DELAY", 0
        ), mock.patch("ydb._topic_writer.topic_writer_multi_asyncio._REPARTITION_DISCOVER_ATTEMPTS", 2):
            writer = TopicWriterMultiAsyncIO(driver, settings)
            await writer.wait_init()
            futures = [
                await writer.write_with_ack_future(PublicMessage(("m%d" % i).encode(), key="a")) for i in range(3)
            ]
            assert set(writer._inflight[0]) == {1, 2, 3}

            # The server persisted seqno 1 and acked it, but the ack died with the stream.
            _FAKE_LAST_SEQNO[0] = 1

            try:
                await writer._on_partition_overloaded(0)

                new_sub = writer._writers[0]
                assert [m.seqno for m in new_sub.messages] == [2, 3], "messages after the persisted one were dropped"
                assert futures[0].done() and futures[0].exception() is None, "persisted message must resolve as written"

                new_sub.resolve_all()
                await asyncio.sleep(0)
                assert all(f.done() for f in futures)
            finally:
                await writer.close(flush=False)
                _retrieve_exceptions(futures)

    async def test_split_migration_does_not_block_on_an_uninitializable_child(self):
        """Migration must not wedge the whole multi-writer when a child cannot be opened.

        Splits cascade (1->3->7 was observed live), so by the time we migrate, the child the
        chooser picked may itself have split and gone inactive. _get_or_create_writer awaits
        wait_init() on it while holding the orchestrator lock, and a writer against an inactive
        partition never finishes init -- so every write, flush and further repartition blocks
        behind it. This is the same failure the maxSeqNo probe caused before it was removed;
        the unbounded wait_init under the lock survived it.
        """
        _FAKE_LAST_SEQNO.clear()
        _FAKE_HANGING_INIT_PARTITIONS.clear()
        mapping = {"a": 0, "b": 1}
        chooser = _KeyMapChooser(mapping)
        before = [_multi_partition(0), _multi_partition(1)]
        after = [
            _split_parent(0, children=[2, 3]),
            _multi_partition(1),
            _multi_partition(2, parents=[0]),
            _multi_partition(3, parents=[0]),
        ]
        driver = _MultiFakeDescribeDriver([before, after])
        settings = MultiWriterSettings(topic="/local/topic", producer_id_prefix="pfx", partition_chooser=chooser)

        with mock.patch(
            "ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _HangingInitSubWriter
        ), mock.patch("ydb._topic_writer.topic_writer_multi_asyncio._WRITER_INIT_TIMEOUT", 0.1):
            writer = TopicWriterMultiAsyncIO(driver, settings)
            await writer.wait_init()
            future = await writer.write_with_ack_future(PublicMessage(b"a", key="a"))

            mapping["a"] = 2
            _FAKE_HANGING_INIT_PARTITIONS.add(2)  # child 2 split again before we got to it

            try:
                try:
                    await asyncio.wait_for(writer._on_partition_overloaded(0), timeout=1)
                except asyncio.TimeoutError:
                    pytest.fail("repartition blocked on an uninitializable child while holding the lock")

                # And the lock must be free afterwards: an unrelated partition still accepts writes.
                await asyncio.wait_for(writer.write_with_ack_future(PublicMessage(b"b", key="b")), timeout=1)
            finally:
                _FAKE_HANGING_INIT_PARTITIONS.clear()
                await writer.close(flush=False)
                _retrieve_exceptions([future])

    async def test_split_waits_for_children_to_cover_the_parent_range(self):
        """A partially visible split must not retire the parent.

        DescribeTopic can show one child before its sibling becomes active. Retiring the parent
        on that view drops its key range down to the single child, leaving the rest of the key
        space uncovered -- and since routing only compares from_bound, keys from the missing
        range then land in the left sibling. That puts one key on two branches of the partition
        graph, which is the invariant the whole design exists to protect.

        Per the C++ producer spec an incomplete graph is a retry-with-backoff state, not a
        successful split: "producer не должен выбирать случайную partition".
        """
        before = [_multi_partition(0, from_bound=b"", to_bound=b"")]
        partial = [
            _split_parent(0, children=[1, 2]),
            _multi_partition(1, parents=[0], from_bound=b"", to_bound=b"\x80"),
        ]
        complete = partial + [_multi_partition(2, parents=[0], from_bound=b"\x80", to_bound=b"")]
        driver = _MultiFakeDescribeDriver([before, partial, complete])
        settings = MultiWriterSettings(topic="/local/topic", producer_id_prefix="pfx")

        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _FakeSubWriter), mock.patch(
            "ydb._topic_writer.topic_writer_multi_asyncio._REPARTITION_DISCOVER_DELAY", 0
        ):
            writer = TopicWriterMultiAsyncIO(driver, settings)
            await writer.wait_init()
            assert isinstance(writer._chooser, PublicPartitionByKeyBound)

            await writer._on_partition_overloaded(0)

            assert set(writer._partitions) == {1, 2}, "parent retired before both children were visible"
            assert sorted(p[-1] for p in writer._chooser._partitions) == [1, 2]
            await writer.close(flush=False)

    async def test_ack_racing_the_split_is_not_resent_to_the_child(self):
        """An ack that lands during the quiesce must count towards the dedup cut.

        Closing a retired sub-writer fails the acks it still holds, and those failures must not
        reach the user because the messages are about to be migrated. Suppressing them must not
        also swallow a SUCCESS landing in the same window: that ack is real, and dropping it
        leaves _max_acked -- the dedup cut -- too low, so a message the parent already persisted
        is resent to the child. That is the duplicate the cut exists to prevent.
        """
        _FAKE_LAST_SEQNO.clear()
        mapping = {"a": 0}
        chooser = _KeyMapChooser(mapping)
        before = [_multi_partition(0), _multi_partition(1)]
        after = [
            _split_parent(0, children=[2, 3]),
            _multi_partition(1),
            _multi_partition(2, parents=[0]),
            _multi_partition(3, parents=[0]),
        ]
        driver = _MultiFakeDescribeDriver([before, after])
        settings = MultiWriterSettings(topic="/local/topic", producer_id_prefix="pfx", partition_chooser=chooser)

        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _AckOnCloseSubWriter):
            writer = TopicWriterMultiAsyncIO(driver, settings)
            await writer.wait_init()
            future = await writer.write_with_ack_future(PublicMessage(b"a", key="a"))

            mapping["a"] = 2
            try:
                await writer._on_partition_overloaded(0)
                await asyncio.sleep(0)

                resent = [m.key for m in writer._writers[2].messages] if 2 in writer._writers else []
                assert resent == [], "a message the parent persisted was resent to the child"
                assert future.done() and future.exception() is None
            finally:
                await writer.close(flush=False)
                _retrieve_exceptions([future])

    async def test_split_resend_preserves_the_original_seqno(self):
        """Both reference implementations keep a message's seqno when resending it to a child.

        C++ `TProducer::TMessagesWorker::ScheduleResendMessages` reassigns only the target
        partition and leaves `SeqNo` alone; Go's multiwriter does the same. That works because
        their counter is global: `CurrentSeqNo` is a single cursor per producer (C++
        `producer.h`), as is Go's `o.currentSeqNo`. A number drawn from one global sequence stays
        meaningful in whatever partition the message ends up in.

        Ours is per partition, so a migrated message would carry a number from the parent's
        sequence into a child that has its own -- hence the renumbering this test pins down.
        Adopting the reference model means replacing the per-partition cursors with one global
        counter first; preserving the seqno without that would break monotonicity in the child.

        Note this is not what makes dedup work: producer_id is per partition in C++ and Go too
        (`"{prefix}_{partitionId}"`), so the server cannot deduplicate across a split either way.
        Both implementations rely on a client-side maxSeqNo cut, exactly as we do.
        """
        _FAKE_LAST_SEQNO.clear()
        mapping = {"a": 0, "b": 0}
        chooser = _KeyMapChooser(mapping)
        before = [_multi_partition(0), _multi_partition(1)]
        after = [
            _split_parent(0, children=[2, 3]),
            _multi_partition(1),
            _multi_partition(2, parents=[0]),
            _multi_partition(3, parents=[0]),
        ]
        driver = _MultiFakeDescribeDriver([before, after])
        settings = MultiWriterSettings(topic="/local/topic", producer_id_prefix="pfx", partition_chooser=chooser)

        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _ControllableSubWriter):
            writer = TopicWriterMultiAsyncIO(driver, settings)
            await writer.wait_init()
            f_a = await writer.write_with_ack_future(PublicMessage(b"a", key="a"))  # partition 0, seqno 1
            f_b = await writer.write_with_ack_future(PublicMessage(b"b", key="b"))  # partition 0, seqno 2
            assert set(writer._inflight[0]) == {1, 2}

            # The split sends the two keys to different children; each keeps its own number.
            mapping.update({"a": 2, "b": 3})
            try:
                await writer._on_partition_overloaded(0)

                assert [m.seqno for m in writer._writers[2].messages] == [1]
                assert [m.seqno for m in writer._writers[3].messages] == [2]
                assert set(writer._inflight[2]) == {1} and set(writer._inflight[3]) == {2}
            finally:
                await writer.close(flush=False)
                _retrieve_exceptions([f_a, f_b])


@pytest.mark.asyncio
class TestTopicWriterMultiAsyncIOLifecycle:
    """Lifecycle and error-path behaviour of the orchestrator.

    Separate from the routing/split tests: these are about what happens around the happy path --
    shutdown, destructors, background tasks and the branches that only run when something fails.
    """

    def _driver(self, partitions=None):
        return _MultiFakeDescribeDriver([partitions or [_multi_partition(0), _multi_partition(1)]])

    def _settings(self, **kwargs):
        kwargs.setdefault("topic", "/local/topic")
        kwargs.setdefault("producer_id_prefix", "pfx")
        kwargs.setdefault("partition_chooser", _KeyMapChooser({"a": 0, "b": 1}))
        return MultiWriterSettings(**kwargs)

    async def test_context_manager_closes_and_keeps_body_errors(self):
        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _FakeSubWriter):
            async with TopicWriterMultiAsyncIO(self._driver(), self._settings()) as writer:
                await writer.write(PublicMessage(b"a", key="a"))
            assert writer._closed

            class TestException(Exception):
                pass

            # A failure inside the block must survive close(): losing it would report a real
            # error as an unrelated teardown problem.
            with pytest.raises(TestException):
                async with TopicWriterMultiAsyncIO(self._driver(), self._settings()) as writer:
                    raise TestException()
            assert writer._closed

    async def test_unclosed_writer_schedules_a_close_on_delete(self):
        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _FakeSubWriter):
            writer = TopicWriterMultiAsyncIO(self._driver(), self._settings())
            await writer.wait_init()

            writer.__del__()  # forgotten writer: the streams still have to be released
            await asyncio.sleep(0)
            await asyncio.sleep(0)
            assert writer._closed

            writer.__del__()  # already closed -> nothing scheduled, still no raise

    async def test_writes_are_refused_after_close(self):
        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _FakeSubWriter):
            writer = TopicWriterMultiAsyncIO(self._driver(), self._settings())
            await writer.wait_init()
            await writer.close(flush=False)

            with pytest.raises(TopicWriterClosedError):
                await writer.write(PublicMessage(b"a", key="a"))
            with pytest.raises(TopicWriterClosedError):
                await writer.flush()

    async def test_close_cancels_an_init_that_never_finished(self):
        class NeverDescribes(_MultiFakeDescribeDriver):
            async def __call__(self, *args, **kwargs):
                await asyncio.Event().wait()

        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _FakeSubWriter):
            writer = TopicWriterMultiAsyncIO(NeverDescribes([[]]), self._settings())
            await asyncio.wait_for(writer.close(), timeout=1)

            # An init left running would keep describing a topic nobody writes to any more.
            with pytest.raises(asyncio.CancelledError):
                await writer._init_task

    async def test_close_tolerates_a_failing_flush(self):
        class FlushRaises(_FakeSubWriter):
            async def flush(self):
                raise RuntimeError("flush failed")

        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", FlushRaises):
            writer = TopicWriterMultiAsyncIO(self._driver(), self._settings())
            await writer.write(PublicMessage(b"a", key="a"))
            # close(flush=True) must still shut the writer down, not propagate the flush error.
            await writer.close()
            assert writer._closed

    async def test_write_with_ack_returns_results_for_one_and_many(self):
        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _FakeSubWriter):
            writer = TopicWriterMultiAsyncIO(self._driver(), self._settings())

            single = await writer.write_with_ack(PublicMessage(b"a", key="a"))
            assert isinstance(single, PublicWriteResult.Written)

            many = await writer.write_with_ack([PublicMessage(b"a", key="a"), PublicMessage(b"b", key="b")])
            assert isinstance(many, list) and len(many) == 2

            await writer.close(flush=False)

    async def test_a_failed_ack_reaches_the_caller(self):
        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _ControllableSubWriter):
            writer = TopicWriterMultiAsyncIO(self._driver(), self._settings())
            future = await writer.write_with_ack_future(PublicMessage(b"a", key="a"))

            writer._writers[0].pending[0].set_exception(RuntimeError("write rejected"))
            await asyncio.sleep(0)

            assert isinstance(future.exception(), RuntimeError)
            assert not writer._inflight.get(0), "a settled message must not stay in flight"
            await writer.close(flush=False)

    async def test_a_cancelled_ack_leaves_the_message_in_flight(self):
        """Cancellation is not an outcome: the writer is being torn down, and the message is
        still owned by the orchestrator until a repartition or recovery decides its fate."""
        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _ControllableSubWriter):
            writer = TopicWriterMultiAsyncIO(self._driver(), self._settings())
            future = await writer.write_with_ack_future(PublicMessage(b"a", key="a"))

            writer._writers[0].pending[0].cancel()
            await asyncio.sleep(0)

            assert not future.done()
            assert set(writer._inflight[0]) == {1}
            await writer.close(flush=False)
            _retrieve_exceptions([future])

    async def test_ack_failures_are_suppressed_while_the_partition_is_being_retired(self):
        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _ControllableSubWriter):
            writer = TopicWriterMultiAsyncIO(self._driver(), self._settings())
            future = await writer.write_with_ack_future(PublicMessage(b"a", key="a"))

            writer._retiring.add(0)
            writer._writers[0].pending[0].set_exception(RuntimeError("session closed by us"))
            await asyncio.sleep(0)

            # Expected noise from our own teardown: the message waits to be resent instead.
            assert not future.done()
            assert set(writer._inflight[0]) == {1}
            await writer.close(flush=False)
            _retrieve_exceptions([future])

    async def test_probe_result_is_cached_per_producer(self):
        _FAKE_LAST_SEQNO.clear()
        _FAKE_LAST_SEQNO[0] = 42
        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _FakeSubWriter):
            writer = TopicWriterMultiAsyncIO(self._driver(), self._settings())
            await writer.wait_init()

            assert await writer._probe_server_seqno(0) == 42
            # A retired producer receives no further writes, so the answer is final: changing
            # what the server would say must not change the cached cut.
            _FAKE_LAST_SEQNO[0] = 99
            assert await writer._probe_server_seqno(0) == 42

            await writer.close(flush=False)

    async def test_lineage_walks_a_merge_graph_without_repeating(self):
        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _FakeSubWriter):
            writer = TopicWriterMultiAsyncIO(self._driver(), self._settings())
            await writer.wait_init()

            # 3 merged from 1 and 2, both of which split off 0: 0 is reachable twice.
            writer._parents = {3: [1, 2], 1: [0], 2: [0]}
            lineage = writer._lineage(3)

            assert sorted(lineage) == [0, 1, 2, 3]
            assert len(lineage) == len(set(lineage)), "an ancestor must be visited once"
            await writer.close(flush=False)

    async def test_repartition_task_deregisters_itself_when_done(self):
        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _FakeSubWriter):
            writer = TopicWriterMultiAsyncIO(self._driver(), self._settings())
            await writer.wait_init()

            async def noop(partition_id):
                return

            writer._on_partition_overloaded = noop
            writer._schedule_repartition(0)
            task = writer._repartition_tasks[0]
            await task
            await asyncio.sleep(0)

            # Left registered, a finished task would block every later signal for this partition.
            assert 0 not in writer._repartition_tasks
            await writer.close(flush=False)

    async def test_repartition_of_an_unknown_partition_is_a_no_op(self):
        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _FakeSubWriter):
            driver = self._driver()
            writer = TopicWriterMultiAsyncIO(driver, self._settings())
            await writer.wait_init()
            describes = driver.describe_calls

            # Already retired by a sibling's event: nothing left to do, and re-describing would
            # only race the handler that did retire it.
            await writer._handle_repartition(99)

            assert driver.describe_calls == describes
            await writer.close(flush=False)

    async def test_failing_inflight_of_an_empty_partition_is_a_no_op(self):
        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _FakeSubWriter):
            writer = TopicWriterMultiAsyncIO(self._driver(), self._settings())
            await writer.wait_init()
            writer._fail_partition_inflight(0, RuntimeError("boom"))  # must not raise
            await writer.close(flush=False)

    async def test_idle_reaper_evicts_and_survives_a_failing_pass(self):
        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _FakeSubWriter):
            writer = TopicWriterMultiAsyncIO(self._driver(), self._settings(writer_idle_timeout_sec=3))
            await writer.write(PublicMessage(b"a", key="a"))
            assert 0 in writer._writers

            writer._last_write_at[0] = writer._loop.time() - 1000

            # One failing pass must not kill the reaper: it has to keep collecting later.
            failed = {"once": False}
            real_evict = writer._evict_idle_writers

            async def flaky():
                if not failed["once"]:
                    failed["once"] = True
                    raise RuntimeError("eviction failed")
                await real_evict()

            async def flaky_then_stop():
                await flaky()
                if failed["once"] and 0 not in writer._writers:
                    writer._closed = True  # end the reaper loop once it has done its job

            writer._evict_idle_writers = flaky_then_stop
            with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.asyncio.sleep", _no_sleep):
                await asyncio.wait_for(TopicWriterMultiAsyncIO._idle_reaper(weakref.ref(writer), 3), timeout=2)

            assert failed["once"]
            assert 0 not in writer._writers, "an idle sub-writer should have been closed"
            await writer.close(flush=False)

    async def test_idle_reaper_stops_when_the_writer_is_gone(self):
        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.asyncio.sleep", _no_sleep):
            # A dead weakref is how the reaper learns the writer was garbage collected; it must
            # end rather than keep a task alive forever.
            await asyncio.wait_for(TopicWriterMultiAsyncIO._idle_reaper(lambda: None, 3), timeout=2)

    async def test_a_busy_partition_is_never_evicted(self):
        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _ControllableSubWriter):
            writer = TopicWriterMultiAsyncIO(self._driver(), self._settings(writer_idle_timeout_sec=3))
            future = await writer.write_with_ack_future(PublicMessage(b"a", key="a"))

            writer._last_write_at[0] = writer._loop.time() - 1000
            await writer._evict_idle_writers()

            # Closing it would strand the un-acked message on a dead session.
            assert 0 in writer._writers
            await writer.close(flush=False)
            _retrieve_exceptions([future])

    async def test_close_failure_on_exit_is_raised_only_on_a_clean_body(self):
        class CloseRaises(_FakeSubWriter):
            async def close(self, flush=True):
                raise RuntimeError("close failed")

        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _FakeSubWriter):
            writer = TopicWriterMultiAsyncIO(self._driver(), self._settings())
            await writer.wait_init()
            writer._flush_impl = mock.AsyncMock(side_effect=RuntimeError("close failed"))
            writer.close = mock.AsyncMock(side_effect=RuntimeError("close failed"))

            with pytest.raises(RuntimeError, match="close failed"):
                await writer.__aexit__(None, None, None)

            # With an exception already travelling, the close failure must not replace it.
            await writer.__aexit__(TypeError, TypeError("original"), None)

    async def test_delete_survives_a_loop_that_cannot_schedule(self):
        """__del__ can run at interpreter shutdown, when scheduling no longer works."""
        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _FakeSubWriter):
            writer = TopicWriterMultiAsyncIO(self._driver(), self._settings())
            await writer.wait_init()
            writer._loop = mock.Mock(is_closed=lambda: False, create_task=mock.Mock(side_effect=RuntimeError))

            writer.__del__()  # must not raise

            writer._closed = True

    async def test_close_survives_a_failing_flush(self):
        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _FakeSubWriter):
            writer = TopicWriterMultiAsyncIO(self._driver(), self._settings())
            await writer.wait_init()
            writer._flush_impl = mock.AsyncMock(side_effect=RuntimeError("flush failed"))

            # Refusing to close on a flush error would leak every stream the writer holds.
            await writer.close()
            assert writer._closed

    async def test_repartition_cancellation_is_not_swallowed(self):
        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _FakeSubWriter):
            writer = TopicWriterMultiAsyncIO(self._driver(), self._settings())
            await writer.wait_init()

            async def cancelled(partition_id):
                raise asyncio.CancelledError()

            # Cancellation means "we are shutting down", not "this partition failed": turning it
            # into a recovery attempt would restart work close() is trying to stop.
            writer._handle_repartition = cancelled
            with pytest.raises(asyncio.CancelledError):
                await writer._on_partition_overloaded(0)

            writer._handle_repartition = mock.AsyncMock(side_effect=RuntimeError("boom"))
            writer._recover_partition = cancelled
            with pytest.raises(asyncio.CancelledError):
                await writer._on_partition_overloaded(0)

            await writer.close(flush=False)

    async def test_recovery_after_a_failed_repartition_keeps_the_partition(self):
        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _ControllableSubWriter):
            writer = TopicWriterMultiAsyncIO(self._driver(), self._settings())
            future = await writer.write_with_ack_future(PublicMessage(b"a", key="a"))

            writer._handle_repartition = mock.AsyncMock(side_effect=RuntimeError("describe blew up"))
            await writer._on_partition_overloaded(0)

            # Repartition failed, but the partition is still ours, so the message is resent
            # rather than failed.
            assert 0 in writer._partitions
            assert not future.done()
            writer._writers[0].resolve_all()
            await asyncio.sleep(0)
            assert future.done()

            await writer.close(flush=False)

    async def test_migration_refuses_a_seqno_the_child_already_persisted(self):
        _FAKE_LAST_SEQNO.clear()
        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _FakeSubWriter):
            writer = TopicWriterMultiAsyncIO(self._driver(), self._settings())
            await writer.wait_init()
            writer._server_init_seqno[2] = 100

            # Resending it anyway would be rejected by the child's writer as a duplicate seqno,
            # taking down the migration of everything behind it.
            conflict = writer._migration_conflict(2, 50, {})
            assert isinstance(conflict, TopicWriterError)
            assert "already persisted" in str(conflict)

            await writer.close(flush=False)

    async def test_idle_eviction_leaves_recently_used_writers_alone(self):
        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _FakeSubWriter):
            writer = TopicWriterMultiAsyncIO(self._driver(), self._settings(writer_idle_timeout_sec=1000))
            await writer.write(PublicMessage(b"a", key="a"))
            await asyncio.sleep(0)  # let the ack settle so the writer counts as idle
            assert not writer._inflight.get(0)

            await writer._evict_idle_writers()

            assert 0 in writer._writers, "a writer used a moment ago is not idle"
            await writer.close(flush=False)


def test_children_must_cover_the_parent_range():
    """Coverage decides whether a split may be committed to, so each way it can fail matters."""
    cover = TopicWriterMultiAsyncIO._children_cover_parent
    parent = _multi_partition(0, from_bound=b"", to_bound=b"")

    # A child with no range at all cannot be reconciled with a bounded parent.
    assert cover(parent, [_multi_partition(1, parents=[0])]) is False

    # A hole between the children: keys in it would fall back to the left sibling.
    assert (
        cover(
            parent,
            [
                _multi_partition(1, parents=[0], from_bound=b"", to_bound=b"\x40"),
                _multi_partition(2, parents=[0], from_bound=b"\x80", to_bound=b""),
            ],
        )
        is False
    )

    # A bounded parent fully tiled by its children.
    bounded = _multi_partition(0, from_bound=b"a", to_bound=b"m")
    assert (
        cover(
            bounded,
            [
                _multi_partition(1, parents=[0], from_bound=b"a", to_bound=b"f"),
                _multi_partition(2, parents=[0], from_bound=b"f", to_bound=b"m"),
            ],
        )
        is True
    )

    # The same parent left short: the tail of its range has no owner.
    assert cover(bounded, [_multi_partition(1, parents=[0], from_bound=b"a", to_bound=b"f")]) is False


class _AckOnChildInitSubWriter(_ControllableSubWriter):
    """Child sub-writer whose init settles the parent's outstanding ack.

    Models the real race: opening the child's session yields, and the parent's ack can land in
    that window -- after the migration decided to resend the message, but before it does.
    """

    parent_writer = None
    child_partition_id = None

    async def wait_init(self):
        # Only when the CHILD's own session is opened. The dedup-cut probe also opens a session
        # (unpinned, so no partition id); acking there would settle the message through the cut
        # instead of the race this is meant to reproduce.
        parent = type(self).parent_writer
        if parent is not None and self.partition_id == type(self).child_partition_id:
            type(self).parent_writer = None
            parent.resolve_all()
            await asyncio.sleep(0)
        return await super().wait_init()


@pytest.mark.asyncio
async def test_message_acked_while_opening_the_child_is_not_resent():
    """An ack that arrives mid-migration means the message is already written.

    Resending it would duplicate it, and the ack has already completed the caller's future, so
    the migration has to notice it lost ownership rather than push it again.
    """
    _FAKE_LAST_SEQNO.clear()
    mapping = {"a": 0}
    chooser = _KeyMapChooser(mapping)
    before = [_multi_partition(0), _multi_partition(1)]
    after = [
        _split_parent(0, children=[2, 3]),
        _multi_partition(1),
        _multi_partition(2, parents=[0]),
        _multi_partition(3, parents=[0]),
    ]
    driver = _MultiFakeDescribeDriver([before, after])
    settings = MultiWriterSettings(topic="/local/topic", producer_id_prefix="pfx", partition_chooser=chooser)

    with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _AckOnChildInitSubWriter):
        writer = TopicWriterMultiAsyncIO(driver, settings)
        await writer.wait_init()
        future = await writer.write_with_ack_future(PublicMessage(b"a", key="a"))

        _AckOnChildInitSubWriter.parent_writer = writer._writers[0]
        _AckOnChildInitSubWriter.child_partition_id = 2
        mapping["a"] = 2
        await writer._on_partition_overloaded(0)

        assert future.done() and future.exception() is None
        resent = [m.seqno for m in writer._writers[2].messages] if 2 in writer._writers else []
        assert resent == [], "a message acked mid-migration was resent anyway"

        await writer.close(flush=False)
