import asyncio
import datetime
from unittest import mock

import grpc
import pytest

import ydb
from ydb import aio
from .datatypes import PublicBatch, PublicMessage
from .topic_reader import PublicReaderSettings
from .topic_reader_asyncio import ReaderStream, PartitionSession
from .._topic_wrapper.common import OffsetsRange, Codec, ServerStatus
from .._topic_wrapper.reader import StreamReadMessage
from .._topic_wrapper.test_helpers import StreamMock, wait_condition, wait_for_fast
from ..issues import Unavailable

# Workaround for good autocomplete in IDE and universal import at runtime
# noinspection PyUnreachableCode
if False:
    from .._grpc.v4.protos import ydb_status_codes_pb2
else:
    from .._grpc.common.protos import ydb_status_codes_pb2


@pytest.fixture()
def default_reader_settings():
    return PublicReaderSettings(
        consumer="test-consumer",
        topic="test-topic",
    )


class StreamMockForReader(StreamMock):
    async def receive(self) -> StreamReadMessage.FromServer:
        return await super(self).receive()

    def write(self, message: StreamReadMessage.FromClient):
        return super().write(message)


@pytest.mark.asyncio
class TestReaderStream:
    default_batch_size = 1

    @pytest.fixture()
    def stream(self):
        return StreamMock()

    @pytest.fixture()
    def partition_session(self, default_reader_settings):
        return PartitionSession(
            id=2,
            topic_path=default_reader_settings.topic,
            partition_id=4,
            state=PartitionSession.State.Active,
        )

    @pytest.fixture()
    def second_partition_session(self, default_reader_settings):
        return PartitionSession(
            id=12,
            topic_path=default_reader_settings.topic,
            partition_id=10,
            state=PartitionSession.State.Active,
        )

    @pytest.fixture()
    async def stream_reader_started(self, stream, default_reader_settings, partition_session,
                            second_partition_session) -> ReaderStream:
        reader = ReaderStream(default_reader_settings)
        init_message = object()

        # noinspection PyTypeChecker
        start = asyncio.create_task(reader._start(stream, init_message))

        stream.from_server.put_nowait(StreamReadMessage.FromServer(
            server_status=ServerStatus(ydb_status_codes_pb2.StatusIds.SUCCESS, []),
            server_message=StreamReadMessage.InitResponse(session_id="test-session"),
        ))

        init_request = await wait_for_fast(stream.from_client.get())
        assert init_request.client_message == init_message

        read_request = await wait_for_fast(stream.from_client.get())
        assert isinstance(read_request.client_message, StreamReadMessage.ReadRequest)

        stream.from_server.put_nowait(
            StreamReadMessage.FromServer(
                server_status=ServerStatus(ydb_status_codes_pb2.StatusIds.SUCCESS, []),
                server_message=StreamReadMessage.StartPartitionSessionRequest(
                partition_session=StreamReadMessage.PartitionSession(
                    partition_session_id=partition_session.id,
                    path=partition_session.topic_path,
                    partition_id=partition_session.partition_id,
                ),
                committed_offset=0,
                partition_offsets=OffsetsRange(
                    start=0,
                    end=0,
                )
            ))
        )
        await start

        start_partition_resp = await wait_for_fast(stream.from_client.get())
        assert isinstance(start_partition_resp.client_message, StreamReadMessage.StartPartitionSessionResponse)

        stream.from_server.put_nowait(
            StreamReadMessage.FromServer(
                server_status=ServerStatus(ydb_status_codes_pb2.StatusIds.SUCCESS, []),
                server_message=StreamReadMessage.StartPartitionSessionRequest(
                partition_session=StreamReadMessage.PartitionSession(
                    partition_session_id=second_partition_session.id,
                    path=second_partition_session.topic_path,
                    partition_id=second_partition_session.partition_id,
                ),
                committed_offset=0,
                partition_offsets=OffsetsRange(
                    start=0,
                    end=0,
                )
            ))
        )
        start_partition_resp = await wait_for_fast(stream.from_client.get())
        assert isinstance(start_partition_resp.client_message, StreamReadMessage.StartPartitionSessionResponse)

        await asyncio.sleep(0)
        with pytest.raises(asyncio.QueueEmpty):
            stream.from_client.get_nowait()

        return reader

    @pytest.fixture()
    async def stream_reader(self, stream_reader_started: ReaderStream):
        yield stream_reader_started

        assert stream_reader_started._first_error is None
        await stream_reader_started.close()

    @pytest.fixture()
    async def stream_reader_finish_with_error(self, stream_reader_started: ReaderStream):
        yield stream_reader_started

        assert stream_reader_started._first_error is not None
        await stream_reader_started.close()


    @staticmethod
    def create_message(partition_session: PartitionSession, seqno: int):
        return PublicMessage(
            seqno=seqno,
            created_at=datetime.datetime(2023, 2, 3, 14, 15),
            message_group_id="test-message-group",
            session_metadata={},
            offset=seqno+1,
            written_at=datetime.datetime(2023, 2, 3, 14, 16),
            producer_id="test-producer-id",
            data=bytes(),
            _partition_session=partition_session
        )

    async def send_message(self, stream_reader, message: PublicMessage):
        def batch_count():
            return len(stream_reader._message_batches)

        initial_batches = batch_count()

        stream = stream_reader._stream  # type: StreamMock
        stream.from_server.put_nowait(StreamReadMessage.FromServer(
            server_status=ServerStatus(ydb_status_codes_pb2.StatusIds.SUCCESS, []),
            server_message=StreamReadMessage.ReadResponse(
            partition_data=[StreamReadMessage.ReadResponse.PartitionData(
                partition_session_id=message._partition_session.id,
                batches=[
                    StreamReadMessage.ReadResponse.Batch(
                        message_data=[
                            StreamReadMessage.ReadResponse.MessageData(
                                offset=message.offset,
                                seq_no=message.seqno,
                                created_at=message.created_at,
                                data=message.data,
                                uncompresed_size=len(message.data),
                                message_group_id=message.message_group_id,
                            )
                        ],
                        producer_id=message.producer_id,
                        write_session_meta=message.session_metadata,
                        codec=Codec.CODEC_RAW,
                        written_at=message.written_at,
                    )
                ]
            )],
            bytes_size=self.default_batch_size,
        )))
        await wait_condition(lambda: batch_count() > initial_batches)

    async def test_first_error(self, stream, stream_reader_finish_with_error):
        class TestError(grpc.RpcError, grpc.Call):
            def __init__(self):
                pass

            def code(self):
                return grpc.StatusCode.UNAUTHENTICATED

            def details(self):
                return "test error"

        test_err = TestError()
        stream.from_server.put_nowait(test_err)

        with pytest.raises(TestError):
            await wait_for_fast(stream_reader_finish_with_error.wait_messages())

        with pytest.raises(TestError):
            stream_reader_finish_with_error.receive_batch_nowait()

    async def test_init_reader(self, stream, default_reader_settings):
        reader = ReaderStream(default_reader_settings)
        init_message = StreamReadMessage.InitRequest(
            consumer="test-consumer",
            topics_read_settings=[StreamReadMessage.InitRequest.TopicReadSettings(
                path="/local/test-topic",
                partition_ids=[],
                max_lag_seconds=None,
                read_from=None,
            )]
        )
        start_task = asyncio.create_task(reader._start(stream, init_message))

        sent_message = await wait_for_fast(stream.from_client.get())
        expected_sent_init_message = StreamReadMessage.FromClient(client_message=init_message)
        assert sent_message == expected_sent_init_message

        stream.from_server.put_nowait(StreamReadMessage.FromServer(
            server_status=ServerStatus(ydb_status_codes_pb2.StatusIds.SUCCESS, []),
            server_message=StreamReadMessage.InitResponse(session_id="test"))
        )

        await start_task

        read_request = await wait_for_fast(stream.from_client.get())
        assert read_request.client_message == StreamReadMessage.ReadRequest(
            bytes_size=default_reader_settings.buffer_size_bytes,
        )

        assert reader._session_id == "test"
        await reader.close()

    async def test_start_partition(self,
                                   stream_reader: ReaderStream,
                                   stream,
                                   default_reader_settings,
                                   partition_session,
                                   ):
        def session_count():
            return len(stream_reader._partition_sessions)

        initial_session_count = session_count()

        test_partition_id = partition_session.partition_id + 1
        test_partition_session_id = partition_session.id + 1
        test_topic_path = default_reader_settings.topic + "-asd"

        stream.from_server.put_nowait(StreamReadMessage.FromServer(
            server_status=ServerStatus(ydb_status_codes_pb2.StatusIds.SUCCESS, []),
            server_message=StreamReadMessage.StartPartitionSessionRequest(
                partition_session=StreamReadMessage.PartitionSession(
                    partition_session_id=test_partition_session_id,
                    path=test_topic_path,
                    partition_id=test_partition_id,
                ),
                committed_offset=0,
                partition_offsets=OffsetsRange(
                    start=0,
                    end=0,
                ),
            )),
        )
        response = await wait_for_fast(stream.from_client.get())
        assert response == StreamReadMessage.FromClient(client_message=StreamReadMessage.StartPartitionSessionResponse(
            partition_session_id=test_partition_session_id,
            read_offset=0,
            commit_offset=0,
        ))

        assert len(stream_reader._partition_sessions) == initial_session_count + 1
        assert stream_reader._partition_sessions[test_partition_session_id] == PartitionSession(
            id=test_partition_session_id,
            state=PartitionSession.State.Active,
            topic_path=test_topic_path,
            partition_id=test_partition_id,
        )

    async def test_partition_stop_force(self, stream, stream_reader, partition_session):
        def session_count():
            return len(stream_reader._partition_sessions)

        initial_session_count = session_count()

        stream.from_server.put_nowait(StreamReadMessage.FromServer(
            server_status=ServerStatus(ydb_status_codes_pb2.StatusIds.SUCCESS, []),
            server_message=StreamReadMessage.StopPartitionSessionRequest(
                partition_session_id=partition_session.id,
                graceful=False,
                committed_offset=0,
            )
        ))

        await asyncio.sleep(0)  # wait next loop
        with pytest.raises(asyncio.QueueEmpty):
            stream.from_client.get_nowait()

        assert session_count() == initial_session_count - 1
        assert partition_session.id not in stream_reader._partition_sessions

    async def test_partition_stop_graceful(self, stream, stream_reader, partition_session):
        def session_count():
            return len(stream_reader._partition_sessions)

        initial_session_count = session_count()

        stream.from_server.put_nowait(StreamReadMessage.FromServer(
            server_status=ServerStatus(ydb_status_codes_pb2.StatusIds.SUCCESS, []),
            server_message=StreamReadMessage.StopPartitionSessionRequest(
                partition_session_id=partition_session.id,
                graceful=True,
                committed_offset=0,
            )
        ))

        resp = await wait_for_fast(stream.from_client.get())  # type: StreamReadMessage.FromClient
        assert session_count() == initial_session_count - 1
        assert partition_session.id not in stream_reader._partition_sessions
        assert resp.client_message == StreamReadMessage.StopPartitionSessionResponse(
            partition_session_id=partition_session.id

        )

        stream.from_server.put_nowait(StreamReadMessage.FromServer(
            server_status=ServerStatus(ydb_status_codes_pb2.StatusIds.SUCCESS, []),
            server_message=StreamReadMessage.StopPartitionSessionRequest(
                partition_session_id=partition_session.id,
                graceful=False,
                committed_offset=0,
            )
        ))

        await asyncio.sleep(0)  # wait next loop
        with pytest.raises(asyncio.QueueEmpty):
            stream.from_client.get_nowait()

    async def test_receive_message_from_server(self, stream_reader, stream, partition_session,
                                                second_partition_session):
        def reader_batch_count():
            return len(stream_reader._message_batches)

        initial_buffer_size = stream_reader._buffer_size_bytes
        initial_batch_count = reader_batch_count()

        bytes_size = 10
        created_at = datetime.datetime(2020, 1, 1, 18, 12)
        written_at = datetime.datetime(2023, 2, 1, 18, 12)
        producer_id = "test-producer-id"
        data = "123".encode()
        session_meta = {"a": "b"}
        message_group_id = "test-message-group-id"

        stream.from_server.put_nowait(StreamReadMessage.FromServer(
            server_status=ServerStatus(ydb_status_codes_pb2.StatusIds.SUCCESS, []),
            server_message=StreamReadMessage.ReadResponse(
            bytes_size=bytes_size,
            partition_data=[
                StreamReadMessage.ReadResponse.PartitionData(
                    partition_session_id=partition_session.id,
                    batches=[
                        StreamReadMessage.ReadResponse.Batch(
                            message_data=[
                                StreamReadMessage.ReadResponse.MessageData(
                                    offset=1,
                                    seq_no=2,
                                    created_at=created_at,
                                    data=data,
                                    uncompresed_size=len(data),
                                    message_group_id=message_group_id,
                                )
                            ],
                            producer_id=producer_id,
                            write_session_meta=session_meta,
                            codec=Codec.CODEC_RAW,
                            written_at=written_at,
                        )
                    ]
                )
            ]
        ))),

        await wait_condition(lambda: reader_batch_count() == initial_batch_count + 1)

        assert stream_reader._buffer_size_bytes == initial_buffer_size - bytes_size

        last_batch = stream_reader._message_batches[-1]
        assert last_batch == PublicBatch(
            session_metadata=session_meta,
            messages=[
                PublicMessage(
                    seqno=2,
                    created_at=created_at,
                    message_group_id=message_group_id,
                    session_metadata=session_meta,
                    offset=1,
                    written_at=written_at,
                    producer_id=producer_id,
                    data=data,
                    _partition_session=partition_session,
                )
            ],
            _partition_session=partition_session,
            _bytes_size=bytes_size,
        )

    async def test_read_batches(self, stream_reader, partition_session, second_partition_session):
        created_at = datetime.datetime(2020, 2, 1, 18, 12)
        created_at2 = datetime.datetime(2020, 2, 2, 18, 12)
        created_at3 = datetime.datetime(2020, 2, 3, 18, 12)
        created_at4 = datetime.datetime(2020, 2, 4, 18, 12)
        written_at = datetime.datetime(2023, 3, 1, 18, 12)
        written_at2 = datetime.datetime(2023, 3, 2, 18, 12)
        producer_id = "test-producer-id"
        producer_id2 = "test-producer-id"
        data = "123".encode()
        data2 = "1235".encode()
        session_meta = {"a": "b"}
        session_meta2 = {"b": "c"}

        message_group_id = "test-message-group-id"
        message_group_id2 = "test-message-group-id-2"

        batches = stream_reader._read_response_to_batches(
            StreamReadMessage.ReadResponse(
                bytes_size=3,
                partition_data=[
                    StreamReadMessage.ReadResponse.PartitionData(
                        partition_session_id=partition_session.id,
                        batches=[
                            StreamReadMessage.ReadResponse.Batch(
                                message_data=[
                                    StreamReadMessage.ReadResponse.MessageData(
                                        offset=2,
                                        seq_no=3,
                                        created_at=created_at,
                                        data=data,
                                        uncompresed_size=len(data),
                                        message_group_id=message_group_id,
                                    )
                                ],
                                producer_id=producer_id,
                                write_session_meta=session_meta,
                                codec=Codec.CODEC_RAW,
                                written_at=written_at,
                            )
                        ]
                    ),
                    StreamReadMessage.ReadResponse.PartitionData(
                        partition_session_id=second_partition_session.id,
                        batches=[
                            StreamReadMessage.ReadResponse.Batch(
                                message_data=[
                                    StreamReadMessage.ReadResponse.MessageData(
                                        offset=1,
                                        seq_no=2,
                                        created_at=created_at2,
                                        data=data,
                                        uncompresed_size=len(data),
                                        message_group_id=message_group_id,
                                    )
                                ],
                                producer_id=producer_id,
                                write_session_meta=session_meta,
                                codec=Codec.CODEC_RAW,
                                written_at=written_at2,
                            ),
                            StreamReadMessage.ReadResponse.Batch(
                                message_data=[
                                    StreamReadMessage.ReadResponse.MessageData(
                                        offset=2,
                                        seq_no=3,
                                        created_at=created_at3,
                                        data=data2,
                                        uncompresed_size=len(data2),
                                        message_group_id=message_group_id,
                                    ),
                                    StreamReadMessage.ReadResponse.MessageData(
                                        offset=4,
                                        seq_no=5,
                                        created_at=created_at4,
                                        data=data,
                                        uncompresed_size=len(data),
                                        message_group_id=message_group_id2,
                                    )
                                ],
                                producer_id=producer_id2,
                                write_session_meta=session_meta2,
                                codec=Codec.CODEC_RAW,
                                written_at=written_at2,
                            )
                        ]
                    ),
                ]
            )
        )

        last0 = batches[0]
        last1 = batches[1]
        last2 = batches[2]

        assert last0 == PublicBatch(
            session_metadata=session_meta,
            messages=[
                PublicMessage(
                    seqno=3,
                    created_at=created_at,
                    message_group_id=message_group_id,
                    session_metadata=session_meta,
                    offset=2,
                    written_at=written_at,
                    producer_id=producer_id,
                    data=data,
                    _partition_session=partition_session,
                )
            ],
            _partition_session=partition_session,
            _bytes_size=1,
        )
        assert last1 == PublicBatch(
            session_metadata=session_meta,
            messages=[
                PublicMessage(
                    seqno=2,
                    created_at=created_at2,
                    message_group_id=message_group_id,
                    session_metadata=session_meta,
                    offset=1,
                    written_at=written_at2,
                    producer_id=producer_id,
                    data=data,
                    _partition_session=second_partition_session,
                )
            ],
            _partition_session=second_partition_session,
            _bytes_size=1,
        )
        assert last2 == PublicBatch(
            session_metadata=session_meta2,
            messages=[
                PublicMessage(
                    seqno=3,
                    created_at=created_at3,
                    message_group_id=message_group_id,
                    session_metadata=session_meta2,
                    offset=2,
                    written_at=written_at2,
                    producer_id=producer_id2,
                    data=data2,
                    _partition_session=second_partition_session,
                ),
                PublicMessage(
                    seqno=5,
                    created_at=created_at4,
                    message_group_id=message_group_id2,
                    session_metadata=session_meta2,
                    offset=4,
                    written_at=written_at2,
                    producer_id=producer_id,
                    data=data,
                    _partition_session=second_partition_session,
                )
            ],
            _partition_session=second_partition_session,
            _bytes_size=1,
        )

    async def test_receive_batch_nowait(self, stream, stream_reader, partition_session):
        assert stream_reader.receive_batch_nowait() is None

        mess1 = self.create_message(partition_session, 1)
        await self.send_message(stream_reader, mess1)

        mess2 = self.create_message(partition_session, 2)
        await self.send_message(stream_reader, mess2)

        initial_buffer_size = stream_reader._buffer_size_bytes

        received = stream_reader.receive_batch_nowait()
        assert received == PublicBatch(
            mess1.session_metadata,
            messages=[
                mess1
            ],
            _partition_session=mess1._partition_session,
            _bytes_size=self.default_batch_size,
        )

        received = stream_reader.receive_batch_nowait()
        assert received == PublicBatch(
            mess2.session_metadata,
            messages=[
                mess2
            ],
            _partition_session=mess2._partition_session,
            _bytes_size=self.default_batch_size,
        )

        assert stream_reader._buffer_size_bytes == initial_buffer_size + 2 * self.default_batch_size

        assert StreamReadMessage.ReadRequest(self.default_batch_size) == stream.from_client.get_nowait().client_message
        assert StreamReadMessage.ReadRequest(self.default_batch_size) == stream.from_client.get_nowait().client_message

        with pytest.raises(asyncio.QueueEmpty):
            stream.from_client.get_nowait()

@pytest.mark.asyncio
class TestReaderReconnector:
    async def test_start(self):
        pass

