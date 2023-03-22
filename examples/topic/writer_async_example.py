import asyncio
import datetime
from typing import Dict, List

import ydb
from ydb import TopicWriterMessage


async def create_writer(db: ydb.aio.Driver):
    async with db.topic_client.writer(
        "/database/topic/path",
        producer_id="producer-id",
    ) as writer:
        await writer.write(TopicWriterMessage("asd"))


async def connect_and_wait(db: ydb.aio.Driver):
    async with db.topic_client.writer(
        "/database/topic/path",
        producer_id="producer-id",
    ) as writer:
        info = await writer.wait_init()  # noqa
        ...


async def connect_without_context_manager(db: ydb.aio.Driver):
    writer = db.topic_client.writer(
        "/database/topic/path",
        producer_id="producer-id",
    )
    try:
        pass  # some code
    finally:
        await writer.close()


async def send_messages(writer: ydb.TopicWriterAsyncIO):
    # simple str/bytes without additional metadata
    await writer.write("mess")  # send text
    await writer.write(bytes([1, 2, 3]))  # send single message with bytes 1,2,3
    await writer.write(["mess-1", "mess-2"])  # send two messages

    # full forms
    await writer.write(ydb.TopicWriterMessage("mess"))  # send text
    await writer.write(ydb.TopicWriterMessage(bytes([1, 2, 3])))  # send bytes
    await writer.write(
        [ydb.TopicWriterMessage("mess-1"), ydb.TopicWriterMessage("mess-2")]
    )  # send few messages by one call

    # with meta
    await writer.write(
        ydb.TopicWriterMessage("asd", seqno=123, created_at=datetime.datetime.now())
    )


async def send_message_without_block_if_internal_buffer_is_full(
    writer: ydb.TopicWriterAsyncIO, msg
) -> bool:
    try:
        # put message to internal queue for send, but if buffer is full - fast return
        # without wait
        await asyncio.wait_for(writer.write(msg), 0)
        return True
    except TimeoutError():
        return False


async def send_messages_with_manual_seqno(writer: ydb.TopicWriter):
    await writer.write(ydb.TopicWriterMessage("mess"))  # send text


async def send_messages_with_wait_ack(writer: ydb.TopicWriterAsyncIO):
    # future wait
    await writer.write_with_ack(
        [
            ydb.TopicWriterMessage("mess", seqno=1),
            ydb.TopicWriterMessage("mess", seqno=2),
        ]
    )

    # send with flush
    await writer.write(["1", "2", "3"])
    await writer.flush()


async def send_messages_and_wait_all_commit_with_flush(writer: ydb.TopicWriterAsyncIO):
    for i in range(10):
        await writer.write(ydb.TopicWriterMessage("%s" % i))
    await writer.flush()


async def send_messages_and_wait_all_commit_with_results(
    writer: ydb.TopicWriterAsyncIO,
):
    for i in range(10):
        content = "%s" % i
        await writer.write(content)

    await writer.flush()


async def switch_messages_with_many_producers(
    writers: Dict[str, ydb.TopicWriterAsyncIO], messages: List[str]
):
    futures = []  # type:  List[asyncio.Future]

    for msg in messages:
        # select writer for the msg
        writer_idx = msg[:1]
        writer = writers[writer_idx]
        future = await writer.write_with_ack_future(msg)
        futures.append(future)

    # wait acks from all writes
    await asyncio.wait(futures)
    for future in futures:
        if future.exception() is not None:
            raise future.exception()

    # all ok, explicit return - for better
    return
