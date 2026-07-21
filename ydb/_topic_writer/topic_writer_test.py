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
from .topic_writer_partition_chooser import (
    murmur2_32,
    murmur64a,
    default_bound_key_hasher,
    PublicPartitionByKeyKafka,
    PublicPartitionByKeyBound,
    PARTITION_KEY_METADATA_KEY,
)
from .._grpc.grpcwrapper.ydb_topic_public_types import PublicDescribeTopicResult


def _partition_info(partition_id: int, from_bound: bytes = None):
    key_range = None
    if from_bound is not None:
        key_range = PublicDescribeTopicResult.PartitionKeyRange(from_bound=from_bound, to_bound=b"")
    return PublicDescribeTopicResult.PartitionInfo(
        partition_id=partition_id,
        active=True,
        child_partition_ids=[],
        parent_partition_ids=[],
        partition_stats=None,
        key_range=key_range,
    )


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


# Golden vectors generated from the YDB Go SDK pkg/xhash reference implementation
# (Murmur2Hash32 / Murmur2Hash64A, seed=0). A mismatch means keys would route to
# the wrong partition, so these are byte-exact assertions.
_MURMUR_GOLDEN = [
    ("", 0, 0),
    ("a", 2456313694, 510903276987443985),
    ("hello", 3848350155, 2191231550387646743),
    ("hello world, murmur2 hash", 1305234166, 15193844207144850389),
    ("мурмур2-хэш", 1364064206, 2094682108092698226),
    ("user-42", 3766944517, 17854748655353381905),
    ("0", 1111412596, 5533571732986600803),
    ("key-with-длинный-unicode-🚀", 901185517, 8765931500921732560),
]


@pytest.mark.parametrize("text,h32,h64", _MURMUR_GOLDEN)
def test_murmur_hashes_match_go_golden_vectors(text, h32, h64):
    data = text.encode("utf-8")
    assert murmur2_32(data, 0) == h32
    assert murmur64a(data, 0) == h64


def test_default_bound_key_hasher_is_big_endian_murmur64a():
    for text, _h32, h64 in _MURMUR_GOLDEN:
        assert default_bound_key_hasher(text) == h64.to_bytes(8, "big")


def test_kafka_chooser_routes_by_murmur2_modulo():
    chooser = PublicPartitionByKeyKafka()
    chooser.add_partitions([_partition_info(0), _partition_info(1), _partition_info(2)])
    for key in ["", "a", "user-42", "hello", "мурмур2-хэш"]:
        expected = (murmur2_32(key.encode("utf-8"), 0) & 0x7FFFFFFF) % 3
        assert chooser.choose_partition(PublicMessage(b"x", key=key)) == expected


def test_kafka_chooser_matches_apache_kafka_partition():
    # Apache Kafka DefaultPartitioner: toPositive(murmur2(key)) % numPartitions.
    # Golden index for key "a" with 3 partitions is 2 (not 1, which the raw hash gives).
    chooser = PublicPartitionByKeyKafka()
    chooser.add_partitions([_partition_info(i) for i in range(3)])
    assert chooser.choose_partition(PublicMessage(b"x", key="a")) == 2


def test_kafka_chooser_rejects_key_ranges():
    chooser = PublicPartitionByKeyKafka()
    with pytest.raises(ValueError):
        chooser.add_partitions([_partition_info(0, from_bound=b"\x10")])


def test_kafka_chooser_raises_without_partitions():
    with pytest.raises(ValueError):
        PublicPartitionByKeyKafka().choose_partition(PublicMessage(b"x", key="k"))


def test_bound_chooser_routes_into_owning_key_range():
    lo = b"\x55" * 8
    hi = b"\xaa" * 8
    chooser = PublicPartitionByKeyBound()
    chooser.add_partitions([_partition_info(0), _partition_info(1, from_bound=lo), _partition_info(2, from_bound=hi)])

    for key in ["a", "b", "user-42", "hello", "zzz", "мурмур2-хэш", "0"]:
        hashed = default_bound_key_hasher(key)
        if hashed < lo:
            expected = 0
        elif hashed < hi:
            expected = 1
        else:
            expected = 2
        assert chooser.choose_partition(PublicMessage(b"x", key=key)) == expected


def test_bound_chooser_stamps_partition_key_metadata():
    chooser = PublicPartitionByKeyBound()
    chooser.add_partitions([_partition_info(0)])
    message = PublicMessage(b"x", key="user-42")
    chooser.choose_partition(message)
    assert message.metadata_items[PARTITION_KEY_METADATA_KEY] == default_bound_key_hasher("user-42")


def test_bound_chooser_requires_from_bound_on_non_first_partition():
    chooser = PublicPartitionByKeyBound()
    with pytest.raises(ValueError):
        chooser.add_partitions([_partition_info(0), _partition_info(1)])
