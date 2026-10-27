import asyncio
import datetime
import threading
from unittest import mock

import pytest

from .. import connection
from .._grpc.grpcwrapper.ydb_topic import StreamWriteMessage, TransactionIdentity
from .._grpc.grpcwrapper.ydb_topic_public_types import PublicCodec
from .topic_writer import (
    InternalMessage,
    PublicMessage,
    PublicWriterSettings,
    TopicWriterBufferFullError,
    messages_to_proto_requests,
)
from .topic_writer_asyncio import WriterAsyncIOReconnector
from .topic_writer_sync import WriterSync


def _make_msg(data: bytes, codec: PublicCodec = PublicCodec.RAW, seqno: int = 1) -> InternalMessage:
    msg = InternalMessage(PublicMessage(data=data, seqno=seqno, created_at=datetime.datetime(2026, 1, 1)))
    msg.codec = codec
    return msg


def _request_size(messages, tx_identity=None):
    return (
        StreamWriteMessage.FromClient(
            StreamWriteMessage.WriteRequest(
                messages=[msg.to_message_data() for msg in messages],
                codec=messages[0].codec,
                tx_identity=tx_identity,
            )
        )
        .to_proto()
        .ByteSize()
    )


class TestMessagesToProtoRequests:
    def test_alternating_codecs_keep_message_order(self):
        messages = [
            _make_msg(b"a", PublicCodec.RAW, seqno=1),
            _make_msg(b"b", PublicCodec.GZIP, seqno=2),
            _make_msg(b"c", PublicCodec.RAW, seqno=3),
        ]

        requests = messages_to_proto_requests(messages, None)

        assert [request.write_request.codec for request in requests] == [
            PublicCodec.RAW,
            PublicCodec.GZIP,
            PublicCodec.RAW,
        ]
        assert [[message.seq_no for message in request.write_request.messages] for request in requests] == [
            [1],
            [2],
            [3],
        ]

    @pytest.mark.parametrize("body_size", [0, 100, 127, 128, 16383, 16384])
    @pytest.mark.parametrize("limit_delta", [-1, 0, 1])
    @pytest.mark.parametrize("with_tx", [False, True])
    def test_serialized_size_controls_splitting(self, monkeypatch, body_size, limit_delta, with_tx):
        tx_identity = TransactionIdentity(tx_id="tx" * 100, session_id="session" * 100) if with_tx else None
        messages = [_make_msg(b"x" * body_size, seqno=i) for i in range(1, 4)]
        for message in messages:
            message.metadata_items = {"key-\N{SNOWMAN}": b"m" * 200, "empty": b""}
        limit = _request_size(messages, tx_identity) + limit_delta
        monkeypatch.setattr(connection, "_DEFAULT_MAX_GRPC_MESSAGE_SIZE", limit)

        requests = messages_to_proto_requests(messages, tx_identity)

        assert [len(request.write_request.messages) for request in requests] == ([2, 1] if limit_delta < 0 else [3])
        assert all(request.ByteSize() <= limit for request in requests)
        assert [message.seq_no for request in requests for message in request.write_request.messages] == [1, 2, 3]
        if tx_identity is not None:
            assert all(request.write_request.tx == tx_identity.to_proto() for request in requests)
        else:
            assert all(not request.write_request.HasField("tx") for request in requests)

    @pytest.mark.parametrize("with_metadata", [False, True])
    def test_oversized_message_is_sent_on_its_own(self, monkeypatch, with_metadata):
        message = _make_msg(b"x" * 200, seqno=2)
        if with_metadata:
            message.metadata_items = {"key": b"m" * 300}
        monkeypatch.setattr(connection, "_DEFAULT_MAX_GRPC_MESSAGE_SIZE", _request_size([message]) - 1)

        requests = messages_to_proto_requests([_make_msg(b"before"), message, _make_msg(b"after", seqno=3)], None)

        assert [[msg.seq_no for msg in request.write_request.messages] for request in requests] == [[1], [2], [3]]
        assert requests[1].ByteSize() > connection._DEFAULT_MAX_GRPC_MESSAGE_SIZE

    def test_empty(self):
        assert messages_to_proto_requests([], tx_identity=None) == []

    def test_single_message_produces_one_request(self):
        msg = _make_msg(b"hello", PublicCodec.RAW, seqno=1)
        requests = messages_to_proto_requests([msg], tx_identity=None)
        assert len(requests) == 1

    def test_request_codec_matches_messages(self):
        raw = _make_msg(b"a", PublicCodec.RAW, seqno=1)
        requests = messages_to_proto_requests([raw], tx_identity=None)
        assert requests[0].write_request.codec == PublicCodec.RAW

        gzip = _make_msg(b"b", PublicCodec.GZIP, seqno=1)
        requests = messages_to_proto_requests([gzip], tx_identity=None)
        assert requests[0].write_request.codec == PublicCodec.GZIP

    def test_same_codec_produces_single_request(self):
        msgs = [_make_msg(b"x", PublicCodec.RAW, seqno=i) for i in range(1, 4)]
        requests = messages_to_proto_requests(msgs, tx_identity=None)
        assert len(requests) == 1
        assert len(requests[0].write_request.messages) == 3

    def test_different_codecs_produce_separate_requests(self):
        raw = _make_msg(b"a", PublicCodec.RAW, seqno=1)
        gzip = _make_msg(b"b", PublicCodec.GZIP, seqno=2)
        requests = messages_to_proto_requests([raw, gzip], tx_identity=None)
        assert len(requests) == 2
        assert requests[0].write_request.codec == PublicCodec.RAW
        assert requests[1].write_request.codec == PublicCodec.GZIP

    def test_size_exceeded_produces_multiple_requests(self, monkeypatch):
        m1 = _make_msg(b"hello", PublicCodec.RAW, seqno=1)
        m2 = _make_msg(b"x", PublicCodec.RAW, seqno=2)
        monkeypatch.setattr(connection, "_DEFAULT_MAX_GRPC_MESSAGE_SIZE", _request_size([m1]))
        requests = messages_to_proto_requests([m1, m2], tx_identity=None)
        assert len(requests) == 2
        assert requests[0].write_request.messages[0].seq_no == 1
        assert requests[1].write_request.messages[0].seq_no == 2

    def test_messages_order_preserved_within_request(self):
        msgs = [_make_msg(f"msg{i}".encode(), PublicCodec.RAW, seqno=i) for i in range(1, 5)]
        requests = messages_to_proto_requests(msgs, tx_identity=None)
        assert len(requests) == 1
        seq_nos = [m.seq_no for m in requests[0].write_request.messages]
        assert seq_nos == [1, 2, 3, 4]


@pytest.fixture
def background_loop():
    loop = asyncio.new_event_loop()
    ready = threading.Event()

    def run():
        asyncio.set_event_loop(loop)
        loop.call_soon(ready.set)
        loop.run_forever()

    t = threading.Thread(target=run, daemon=True)
    t.start()
    assert ready.wait(timeout=5), "background event loop thread did not start in time"
    yield loop
    loop.call_soon_threadsafe(loop.stop)
    t.join(timeout=5)
    assert not t.is_alive(), "background event loop thread did not stop in time"
    loop.close()


@pytest.fixture
def mock_reconnector(monkeypatch):
    def factory(reconnector_instance):
        monkeypatch.setattr(WriterAsyncIOReconnector, "__new__", lambda cls, *a, **kw: reconnector_instance)
        return reconnector_instance

    return factory


class TestWriterSyncBuffer:
    def _make_writer(self, background_loop, reconnector, mock_reconnector):
        mock_reconnector(reconnector)
        settings = PublicWriterSettings(topic="/local/topic", producer_id="test-producer")
        return WriterSync(mock.Mock(), settings, eventloop=background_loop)

    def test_buffer_full_error_propagates(self, background_loop, mock_reconnector):
        class ImmediateFullReconnector:
            async def write_with_ack_future(self, messages):
                raise TopicWriterBufferFullError("buffer full")

            async def close(self, flush):
                pass

        writer = self._make_writer(background_loop, ImmediateFullReconnector(), mock_reconnector)
        with pytest.raises(TopicWriterBufferFullError):
            writer.write(PublicMessage(data=b"hello", seqno=1))
        writer.close(flush=False)

    def test_write_blocks_until_buffer_freed(self, background_loop, mock_reconnector):
        write_started = threading.Event()

        class BlockingReconnector:
            _release_event = None

            async def write_with_ack_future(self, messages):
                self._release_event = asyncio.Event()
                write_started.set()
                await self._release_event.wait()
                loop = asyncio.get_running_loop()
                futures = [loop.create_future() for _ in messages]
                for f in futures:
                    f.set_result(None)
                return futures

            async def release(self):
                if self._release_event:
                    self._release_event.set()

            async def close(self, flush):
                pass

        reconnector = BlockingReconnector()
        writer = self._make_writer(background_loop, reconnector, mock_reconnector)

        write_errors = []

        def do_write():
            try:
                writer.write(PublicMessage(data=b"hello", seqno=1))
            except Exception as e:
                write_errors.append(e)

        write_thread = threading.Thread(target=do_write, daemon=True)
        write_thread.start()

        assert write_started.wait(timeout=1.0), "write did not start"

        # Write thread is now blocked; release the mock to simulate buffer freed
        asyncio.run_coroutine_threadsafe(reconnector.release(), background_loop).result(timeout=1.0)

        write_thread.join(timeout=1.0)
        assert not write_thread.is_alive(), "write should have completed after buffer was freed"
        assert not write_errors, f"unexpected error: {write_errors}"

        writer.close(flush=False)
