from __future__ import annotations

import asyncio
import copy
import dataclasses
import datetime
import gc
import gzip
import sys
import typing
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
        "codec,datas",
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
        datas: List[bytes],
    ):
        f = reconnector._codec_functions[codec]
        expected_datas = [f(data) for data in datas]

        messages = [InternalMessage(PublicMessage(data)) for data in datas]
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

    async def wait_init(self):
        return PublicWriterInitInfo(last_seqno=_FAKE_LAST_SEQNO.get(self.partition_id, 0), supported_codecs=[])

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
            assert writer._partition_seqno.get(0) == 1  # seqno cursor preserved for continuity

            # writing to partition 0 again recreates a fresh sub-writer, continuing the seqno
            f_a2 = await writer.write_with_ack_future(PublicMessage(b"a2", key="a"))
            assert 0 in writer._writers and writer._writers[0] is not sub0
            assert next(iter(writer._inflight[0])) == 2  # continued from cursor (1 -> 2)

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
        # Two parents (0, 1) merge into one child (2), which lists both as parents.
        mapping = {"x": 0, "y": 1}
        chooser = _KeyMapChooser(mapping)
        before = [_multi_partition(0), _multi_partition(1)]
        after = [_multi_partition(2, parents=[0, 1])]
        driver = _MultiFakeDescribeDriver([before, after])
        settings = MultiWriterSettings(topic="/local/topic", producer_id_prefix="pfx", partition_chooser=chooser)

        with mock.patch("ydb._topic_writer.topic_writer_multi_asyncio.WriterAsyncIO", _ControllableSubWriter):
            writer = TopicWriterMultiAsyncIO(driver, settings)
            await writer.wait_init()

            f_x = await writer.write_with_ack_future(PublicMessage(b"x", key="x"))  # partition 0
            f_y = await writer.write_with_ack_future(PublicMessage(b"y", key="y"))  # partition 1
            assert set(writer._inflight[0]) == {1} and set(writer._inflight[1]) == {1}

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
