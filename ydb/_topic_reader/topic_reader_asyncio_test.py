import asyncio
from unittest import mock

import pytest

from ydb import aio
from ydb._topic_reader.topic_reader import PublicReaderSettings
from ydb._topic_reader.topic_reader_asyncio import ReaderStream, PartitionSession
from ydb._topic_wrapper.common import OffsetsRange
from ydb._topic_wrapper.reader import StreamReadMessage
from ydb._topic_wrapper.test_helpers import StreamMock, wait_condition, wait_for_fast


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
    async def stream_reader(self, stream, partition_session, default_reader_settings) -> ReaderStream:
        reader = ReaderStream(default_reader_settings)
        init_message = object()

        # noinspection PyTypeChecker
        start = asyncio.create_task(reader.start(stream, init_message))

        stream.from_server.put_nowait(StreamReadMessage.FromServer(
            StreamReadMessage.InitResponse(session_id="test-session")
        ))

        init_request = await wait_for_fast(stream.from_client.get())
        assert init_request.client_message == init_message

        read_request = await wait_for_fast(stream.from_client.get())
        assert isinstance(read_request.client_message, StreamReadMessage.ReadRequest)

        stream.from_server.put_nowait(
            StreamReadMessage.FromServer(server_message=StreamReadMessage.StartPartitionSessionRequest(
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

        await asyncio.sleep(0)
        with pytest.raises(asyncio.QueueEmpty):
            stream.from_client.get_nowait()

        yield reader

        assert reader._first_error is None

        await reader.close()

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
        start_task = asyncio.create_task(reader.start(stream, init_message))

        sent_message = await wait_for_fast(stream.from_client.get())
        expected_sent_init_message = StreamReadMessage.FromClient(client_message=init_message)
        assert sent_message == expected_sent_init_message

        stream.from_server.put_nowait(StreamReadMessage.FromServer(
            server_message=StreamReadMessage.InitResponse(session_id="test"))
        )

        await start_task

        read_request = await wait_for_fast(stream.from_client.get())
        assert read_request.client_message == StreamReadMessage.ReadRequest(
            bytes_size=default_reader_settings.buffer_size_bytes,
        )

        assert reader._session_id == "test"
        await reader.close()

    async def test_start_partition(self, stream_reader: ReaderStream, stream, default_reader_settings, partition_session):
        def session_count():
            return len(stream_reader._partition_sessions)

        initial_session_count = session_count()

        test_partition_id = partition_session.partition_id+1
        test_partition_session_id = partition_session.id + 1
        test_topic_path = default_reader_settings.topic + "-asd"

        stream.from_server.put_nowait(StreamReadMessage.FromServer(
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
            server_message=StreamReadMessage.StopPartitionSessionRequest(
                partition_session_id=partition_session.id,
                graceful=True,
                committed_offset=0,
            )
        ))

        resp = await wait_for_fast(stream.from_client.get())  # type: StreamReadMessage.FromClient
        assert session_count() == initial_session_count-1
        assert partition_session.id not in stream_reader._partition_sessions
        assert resp.client_message == StreamReadMessage.StopPartitionSessionResponse(
            partition_session_id=partition_session.id

        )

        stream.from_server.put_nowait(StreamReadMessage.FromServer(
            server_message=StreamReadMessage.StopPartitionSessionRequest(
                partition_session_id=partition_session.id,
                graceful=False,
                committed_offset=0,
            )
        ))

        await asyncio.sleep(0)  # wait next loop
        with pytest.raises(asyncio.QueueEmpty):
            stream.from_client.get_nowait()

