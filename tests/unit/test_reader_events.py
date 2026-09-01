# -*- coding: utf-8 -*-
import pytest

from ydb._topic_reader import events
from ydb.issues import ClientInternalError


def test_event_dataclasses():
    commit = events.OnCommit(topic="t", offset=5)
    assert commit.topic == "t"
    assert commit.offset == 5

    request = events.OnPartitionGetStartOffsetRequest(topic="t", partition_id=3)
    assert request.topic == "t"
    assert request.partition_id == 3

    response = events.OnPartitionGetStartOffsetResponse(start_offset=10)
    assert response.start_offset == 10

    assert isinstance(events.OnInitPartition(), events.OnInitPartition)
    assert isinstance(events.OnShutdownPartition(), events.OnShutdownPartition)


def test_default_event_handler_returns():
    handler = events.EventHandler()
    assert handler.on_commit(events.OnCommit("t", 1)) is None

    response = handler.on_partition_get_start_offset(events.OnPartitionGetStartOffsetRequest("t", 0))
    assert isinstance(response, events.OnPartitionGetStartOffsetResponse)
    assert response.start_offset is None

    assert handler.on_init_partition(events.OnInitPartition()) is None
    assert handler.on_shutdown_partition(events.OnShutdownPartition()) is None


async def test_dispatch_sync_handlers():
    handler = events.EventHandler()
    assert await handler._dispatch(events.OnCommit("t", 1)) is None

    response = await handler._dispatch(events.OnPartitionGetStartOffsetRequest("t", 0))
    assert response.start_offset is None

    assert await handler._dispatch(events.OnInitPartition()) is None
    assert await handler._dispatch(events.OnShutdownPartition()) is None


async def test_dispatch_async_handlers():
    class AsyncHandler(events.EventHandler):
        async def on_commit(self, event):
            return None

        async def on_partition_get_start_offset(self, event):
            return events.OnPartitionGetStartOffsetResponse(start_offset=42)

        async def on_init_partition(self, event):
            return None

        async def on_shutdown_partition(self, event):
            return None

    handler = AsyncHandler()
    assert await handler._dispatch(events.OnCommit("t", 1)) is None

    response = await handler._dispatch(events.OnPartitionGetStartOffsetRequest("t", 0))
    assert response.start_offset == 42

    assert await handler._dispatch(events.OnInitPartition()) is None
    assert await handler._dispatch(events.OnShutdownPartition()) is None


async def test_dispatch_unsupported_event_raises():
    class UnknownEvent(events.BaseReaderEvent):
        pass

    with pytest.raises(ClientInternalError):
        await events.EventHandler()._dispatch(UnknownEvent())
