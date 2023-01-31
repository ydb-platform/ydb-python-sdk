import asyncio
from unittest import mock

import pytest

from ydb import aio
from ydb._topic_reader.topic_reader_asyncio import ReaderStream
from ydb._topic_wrapper.reader import StreamReadMessage
from ydb._topic_wrapper.test_helpers import StreamMock


def default_driver() -> aio.Driver:
    driver = mock.Mock(spec=aio.Driver)
    driver._credentials = mock.Mock()
    return driver


@pytest.mark.asyncio
class TestReaderStream:
    @pytest.fixture()
    def stream(self):
        return StreamMock()

    async def test_init_reader(self, stream):
        reader = ReaderStream(None)
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

        sent_message = await stream.from_client.get()
        expected_sent_init_message = StreamReadMessage.FromClient(client_message=init_message)
        assert sent_message == expected_sent_init_message

        stream.from_server.put_nowait(StreamReadMessage.FromServer(
            server_message=StreamReadMessage.InitResponse(session_id="test"))
        )

        await start_task
        assert reader._session_id == "test"
