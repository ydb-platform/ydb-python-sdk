from __future__ import annotations

import asyncio
import copy
import dataclasses
import datetime
import typing
from queue import Queue, Empty
from unittest import mock

import freezegun
import pytest


from .. import aio
from .. import StatusCode, issues
from .._grpc.grpcwrapper.ydb_topic import Codec, StreamWriteMessage
from .._grpc.grpcwrapper.common_utils import ServerStatus
from .topic_writer import (
    InternalMessage,
    PublicMessage,
    WriterSettings,
    PublicWriterSettings,
    PublicWriterInitInfo,
    PublicWriteResult,
    TopicWriterError,
)
from .._topic_common.test_helpers import StreamMock, wait_for_fast

from .topic_writer_asyncio import (
    WriterAsyncIOStream,
    WriterAsyncIOReconnector,
    WriterAsyncIO,
)


@pytest.fixture
def default_driver() -> aio.Driver:
    driver = mock.Mock(spec=aio.Driver)
    driver._credentials = mock.Mock()
    return driver


@pytest.mark.asyncio
class TestWriterAsyncIOStream:
    @dataclasses.dataclass
    class WriterWithMockedStream:
        writer: WriterAsyncIOStream
        stream: StreamMock

    @pytest.fixture
    def stream(self):
        return StreamMock()

    @pytest.fixture
    async def writer_and_stream(self, stream) -> WriterWithMockedStream:
        stream.from_server.put_nowait(
            StreamWriteMessage.InitResponse(
                last_seq_no=4,
                session_id="123",
                partition_id=3,
                supported_codecs=[Codec.CODEC_RAW, Codec.CODEC_GZIP],
                status=ServerStatus(StatusCode.SUCCESS, []),
            )
        )

        writer = WriterAsyncIOStream(None)
        await writer._start(
            stream,
            init_message=StreamWriteMessage.InitRequest(
                path="/local/test",
                producer_id="producer-id",
                write_session_meta={"a": "b"},
                partitioning=StreamWriteMessage.PartitioningMessageGroupID(
                    message_group_id="message-group-id"
                ),
                get_last_seq_no=False,
            ),
        )
        await stream.from_client.get()

        return TestWriterAsyncIOStream.WriterWithMockedStream(
            stream=stream,
            writer=writer,
        )

    async def test_init_writer(self, stream):
        init_seqno = 4
        init_message = StreamWriteMessage.InitRequest(
            path="/local/test",
            producer_id="producer-id",
            write_session_meta={"a": "b"},
            partitioning=StreamWriteMessage.PartitioningMessageGroupID(
                message_group_id="message-group-id"
            ),
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

        writer = WriterAsyncIOStream(None)
        await writer._start(stream, init_message)

        sent_message = await stream.from_client.get()
        expected_message = StreamWriteMessage.FromClient(init_message)

        assert expected_message == sent_message
        assert writer.last_seqno == init_seqno

    async def test_write_a_message(self, writer_and_stream: WriterWithMockedStream):
        data = "123".encode()
        now = datetime.datetime.now()
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
                messages=[
                    StreamWriteMessage.WriteRequest.MessageData(
                        seq_no=1,
                        created_at=now,
                        data=data,
                        uncompressed_size=len(data),
                        partitioning=None,
                    )
                ],
            )
        )

        sent_message = await writer_and_stream.stream.from_client.get()
        assert expected_message == sent_message


@pytest.mark.asyncio
class TestWriterAsyncIOReconnector:
    init_last_seqno = 0

    class StreamWriterMock:
        last_seqno: int

        from_client: asyncio.Queue
        from_server: asyncio.Queue

        _closed: bool

        def __init__(self):
            self.last_seqno = 0
            self.from_server = asyncio.Queue()
            self.from_client = asyncio.Queue()
            self._closed = False

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

        def close(self):
            if self._closed:
                return

            self.from_server.put_nowait(
                Exception("waited message while StreamWriterMock closed")
            )

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

        async def async_create(driver, init_message, token_getter):
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
                producer_and_message_group_id="test-producer",
                auto_seqno=False,
                auto_created_at=False,
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

    @pytest.fixture
    async def reconnector(
        self, default_driver, default_settings
    ) -> WriterAsyncIOReconnector:
        return WriterAsyncIOReconnector(default_driver, default_settings)

    async def test_reconnect_and_resent_non_acked_messages_on_retriable_error(
        self,
        reconnector: WriterAsyncIOReconnector,
        get_stream_writer,
        default_write_statistic,
    ):
        now = datetime.datetime.now()
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
        await reconnector.write_with_ack([message1, message2])

        # sent to first stream
        stream_writer = get_stream_writer()

        messages = await stream_writer.from_client.get()
        assert [InternalMessage(message1)] == messages
        messages = await stream_writer.from_client.get()
        assert [InternalMessage(message2)] == messages

        # ack first message
        stream_writer.from_server.put_nowait(
            StreamWriteMessage.WriteResponse(
                partition_id=1,
                acks=[
                    StreamWriteMessage.WriteResponse.WriteAck(
                        seq_no=1,
                        message_write_status=StreamWriteMessage.WriteResponse.WriteAck.StatusWritten(
                            offset=1
                        ),
                    )
                ],
                write_statistics=default_write_statistic,
            )
        )

        stream_writer.from_server.put_nowait(issues.Overloaded("test"))

        second_writer = get_stream_writer()
        second_sent_msg = await second_writer.from_client.get()

        expected_messages = [InternalMessage(message2)]
        assert second_sent_msg == expected_messages
        await reconnector.close()

    async def test_stop_on_unexpected_exception(
        self, reconnector: WriterAsyncIOReconnector, get_stream_writer
    ):
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
                    await reconnector.write_with_ack([message])
                    await asyncio.sleep(0.1)

            await asyncio.wait_for(wait_stop(), 1)

        with pytest.raises(TestException):
            await reconnector.close()

    async def test_wait_init(self, default_driver, default_settings, get_stream_writer):
        init_seqno = 100
        expected_init_info = PublicWriterInitInfo(init_seqno)
        with mock.patch.object(
            TestWriterAsyncIOReconnector, "init_last_seqno", init_seqno
        ):
            reconnector = WriterAsyncIOReconnector(default_driver, default_settings)
            info = await reconnector.wait_init()
            assert info == expected_init_info

        reconnector._stream_connected.clear()

        # force reconnect
        with mock.patch.object(
            TestWriterAsyncIOReconnector, "init_last_seqno", init_seqno + 1
        ):
            stream_writer = get_stream_writer()
            stream_writer.from_server.put_nowait(
                issues.Overloaded("test")
            )  # some retriable error
            await reconnector._stream_connected.wait()

            info = await reconnector.wait_init()
            assert info == expected_init_info

        await reconnector.close()

    async def test_write_message(
        self, reconnector: WriterAsyncIOReconnector, get_stream_writer
    ):
        stream_writer = get_stream_writer()
        message = PublicMessage(
            data="123",
            seqno=3,
        )
        await reconnector.write_with_ack([message])

        sent_messages = await asyncio.wait_for(stream_writer.from_client.get(), 1)
        assert sent_messages == [InternalMessage(message)]

        await reconnector.close()

    async def test_auto_seq_no(
        self, default_driver, default_settings, get_stream_writer
    ):
        last_seq_no = 100
        with mock.patch.object(
            TestWriterAsyncIOReconnector, "init_last_seqno", last_seq_no
        ):
            settings = copy.deepcopy(default_settings)
            settings.auto_seqno = True

            reconnector = WriterAsyncIOReconnector(default_driver, settings)

            await reconnector.write_with_ack([PublicMessage(data="123")])
            await reconnector.write_with_ack([PublicMessage(data="456")])

            stream_writer = get_stream_writer()

            sent = await stream_writer.from_client.get()
            assert [
                InternalMessage(PublicMessage(seqno=last_seq_no + 1, data="123"))
            ] == sent

            sent = await stream_writer.from_client.get()
            assert [
                InternalMessage(PublicMessage(seqno=last_seq_no + 2, data="456"))
            ] == sent

        with pytest.raises(TopicWriterError):
            await reconnector.write_with_ack(
                [PublicMessage(seqno=last_seq_no + 3, data="123")]
            )

        await reconnector.close()

    async def test_deny_double_seqno(self, reconnector: WriterAsyncIOReconnector):
        await reconnector.write_with_ack([PublicMessage(seqno=10, data="123")])

        with pytest.raises(TopicWriterError):
            await reconnector.write_with_ack([PublicMessage(seqno=9, data="123")])

        with pytest.raises(TopicWriterError):
            await reconnector.write_with_ack([PublicMessage(seqno=10, data="123")])

        await reconnector.write_with_ack([PublicMessage(seqno=11, data="123")])

        await reconnector.close()

    @freezegun.freeze_time("2022-01-13 20:50:00", tz_offset=0)
    async def test_auto_created_at(
        self, default_driver, default_settings, get_stream_writer
    ):
        now = datetime.datetime.now()

        settings = copy.deepcopy(default_settings)
        settings.auto_created_at = True
        reconnector = WriterAsyncIOReconnector(default_driver, settings)
        await reconnector.write_with_ack([PublicMessage(seqno=4, data="123")])

        stream_writer = get_stream_writer()
        sent = await wait_for_fast(stream_writer.from_client.get())

        assert [
            InternalMessage(PublicMessage(seqno=4, data="123", created_at=now))
        ] == sent
        await reconnector.close()


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

        async def write_with_ack(self, messages: typing.List[InternalMessage]):
            async with self.lock:
                futures = [asyncio.Future() for _ in messages]
                self.messages.extend(messages)
                self.futures.extend(futures)
                self.messages_writted.set()
                return futures

        async def close(self):
            pass

    @pytest.fixture
    def default_settings(self) -> PublicWriterSettings:
        return PublicWriterSettings(
            topic="/local/topic",
            producer_and_message_group_id="producer-id",
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

        res = await writer.write_with_ack(
            [PublicMessage(seqno=2, data="123"), PublicMessage(seqno=3, data="123")]
        )
        assert res == [PublicWriteResult.Written(offset=2), PublicWriteResult.Skipped()]
