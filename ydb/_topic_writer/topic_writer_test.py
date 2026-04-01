import asyncio
import threading
from typing import List
from unittest import mock

import pytest

from .._grpc.grpcwrapper.ydb_topic_public_types import PublicCodec
from .topic_writer import (
    InternalMessage,
    PublicMessage,
    PublicWriterSettings,
    TopicWriterBufferFullError,
    _split_messages_by_size,
    _split_messages_for_send,
    messages_to_proto_requests,
)
from .topic_writer_asyncio import WriterAsyncIOReconnector
from .topic_writer_sync import WriterSync


@pytest.mark.parametrize(
    "messages,split_size,expected",
    [
        (
            [1, 2, 3],
            0,
            [[1], [2], [3]],
        ),
        (
            [1, 2, 3],
            1,
            [[1], [2], [3]],
        ),
        (
            [1, 2, 3],
            3,
            [[1, 2], [3]],
        ),
        (
            [1, 2, 3],
            100,
            [[1, 2, 3]],
        ),
        (
            [100, 2, 3],
            100,
            [[100], [2, 3]],
        ),
        (
            [],
            100,
            [],
        ),
        (
            [],
            100,
            [],
        ),
    ],
)
def test_split_messages_by_size(messages: List[int], split_size: int, expected: List[List[int]]):
    res = _split_messages_by_size(messages, split_size, lambda x: x)  # noqa
    assert res == expected


def _make_msg(data: bytes, codec: PublicCodec = PublicCodec.RAW, seqno: int = 1) -> InternalMessage:
    msg = InternalMessage(PublicMessage(data=data, seqno=seqno))
    msg.codec = codec
    return msg


class TestSplitMessagesForSend:
    def test_empty(self):
        assert _split_messages_for_send([]) == []

    def test_single_message(self):
        msg = _make_msg(b"hello")
        assert _split_messages_for_send([msg]) == [[msg]]

    def test_same_codec_kept_together(self):
        msgs = [_make_msg(b"a", PublicCodec.RAW, i) for i in range(1, 4)]
        assert _split_messages_for_send(msgs) == [msgs]

    def test_different_codecs_split_into_separate_groups(self):
        raw = _make_msg(b"a", PublicCodec.RAW, seqno=1)
        gzip = _make_msg(b"b", PublicCodec.GZIP, seqno=2)
        result = _split_messages_for_send([raw, gzip])
        assert result == [[raw], [gzip]]

    def test_alternating_codecs_each_run_is_own_group(self):
        # RAW, GZIP, RAW must produce 3 separate groups, not 2
        r1 = _make_msg(b"a", PublicCodec.RAW, seqno=1)
        g1 = _make_msg(b"b", PublicCodec.GZIP, seqno=2)
        r2 = _make_msg(b"c", PublicCodec.RAW, seqno=3)
        result = _split_messages_for_send([r1, g1, r2])
        assert result == [[r1], [g1], [r2]]

    def test_size_limit_splits_same_codec_group(self, monkeypatch):
        from .topic_writer import _message_data_overhead
        from .. import connection

        # patch limit so that one 5-byte message fits but two do not
        monkeypatch.setattr(connection, "_DEFAULT_MAX_GRPC_MESSAGE_SIZE", _message_data_overhead + 5)
        m1 = _make_msg(b"hello", PublicCodec.RAW, seqno=1)
        m2 = _make_msg(b"x", PublicCodec.RAW, seqno=2)
        result = _split_messages_for_send([m1, m2])
        assert result == [[m1], [m2]]

    def test_size_limit_not_exceeded_keeps_group(self):
        m1 = _make_msg(b"hello", PublicCodec.RAW, seqno=1)
        m2 = _make_msg(b"world", PublicCodec.RAW, seqno=2)
        result = _split_messages_for_send([m1, m2])
        assert result == [[m1, m2]]

    def test_codec_split_takes_priority_over_size(self):
        # tiny messages but different codecs — must still split by codec
        r = _make_msg(b"a", PublicCodec.RAW, seqno=1)
        g = _make_msg(b"b", PublicCodec.GZIP, seqno=2)
        result = _split_messages_for_send([r, g])
        assert len(result) == 2
        assert result[0][0].codec == PublicCodec.RAW
        assert result[1][0].codec == PublicCodec.GZIP


class TestMessagesToProtoRequests:
    def test_empty(self):
        assert messages_to_proto_requests([], tx_identity=None) == []

    def test_single_message_produces_one_request(self):
        msg = _make_msg(b"hello", PublicCodec.RAW, seqno=1)
        requests = messages_to_proto_requests([msg], tx_identity=None)
        assert len(requests) == 1

    def test_request_codec_matches_messages(self):
        raw = _make_msg(b"a", PublicCodec.RAW, seqno=1)
        requests = messages_to_proto_requests([raw], tx_identity=None)
        assert requests[0].value.codec == PublicCodec.RAW

        gzip = _make_msg(b"b", PublicCodec.GZIP, seqno=1)
        requests = messages_to_proto_requests([gzip], tx_identity=None)
        assert requests[0].value.codec == PublicCodec.GZIP

    def test_same_codec_produces_single_request(self):
        msgs = [_make_msg(b"x", PublicCodec.RAW, seqno=i) for i in range(1, 4)]
        requests = messages_to_proto_requests(msgs, tx_identity=None)
        assert len(requests) == 1
        assert len(requests[0].value.messages) == 3

    def test_different_codecs_produce_separate_requests(self):
        raw = _make_msg(b"a", PublicCodec.RAW, seqno=1)
        gzip = _make_msg(b"b", PublicCodec.GZIP, seqno=2)
        requests = messages_to_proto_requests([raw, gzip], tx_identity=None)
        assert len(requests) == 2
        assert requests[0].value.codec == PublicCodec.RAW
        assert requests[1].value.codec == PublicCodec.GZIP

    def test_size_exceeded_produces_multiple_requests(self, monkeypatch):
        from .topic_writer import _message_data_overhead
        from .. import connection

        monkeypatch.setattr(connection, "_DEFAULT_MAX_GRPC_MESSAGE_SIZE", _message_data_overhead + 5)
        m1 = _make_msg(b"hello", PublicCodec.RAW, seqno=1)
        m2 = _make_msg(b"x", PublicCodec.RAW, seqno=2)
        requests = messages_to_proto_requests([m1, m2], tx_identity=None)
        assert len(requests) == 2
        assert requests[0].value.messages[0].seq_no == 1
        assert requests[1].value.messages[0].seq_no == 2

    def test_messages_order_preserved_within_request(self):
        msgs = [_make_msg(f"msg{i}".encode(), PublicCodec.RAW, seqno=i) for i in range(1, 5)]
        requests = messages_to_proto_requests(msgs, tx_identity=None)
        assert len(requests) == 1
        seq_nos = [m.seq_no for m in requests[0].value.messages]
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
