import concurrent.futures
import datetime
from typing import Dict, List
from concurrent.futures import Future, wait

import ydb
from ydb import TopicWriterMessage


def connect():
    db = ydb.Driver(
        connection_string="grpc://localhost:2135?database=/local",
        credentials=ydb.credentials.AnonymousCredentials(),
    )
    writer = db.topic_client.writer(
        "/local/topic",
        producer_id="producer-id",
    )
    writer.write(TopicWriterMessage("asd"))


def create_writer(db: ydb.Driver):
    with db.topic_client.writer(
        "/database/topic/path",
        producer_id="producer-id",
    ) as writer:
        writer.write(TopicWriterMessage("asd"))


def connect_and_wait(db: ydb.Driver):
    with db.topic_client.writer(
        "/database/topic/path",
        producer_id="producer-id",
    ) as writer:
        info = writer.wait_init()  # noqa


def connect_without_context_manager(db: ydb.Driver):
    writer = db.topic_client.writer(
        "/database/topic/path",
        producer_id="producer-id",
    )
    try:
        pass  # some code
    finally:
        writer.close()


def send_messages(writer: ydb.TopicWriter):
    # simple str/bytes without additional metadata
    writer.write("mess")  # send text
    writer.write(bytes([1, 2, 3]))  # send single message with bytes 1,2,3
    writer.write(["mess-1", "mess-2"])  # send two messages

    # full forms
    writer.write(ydb.TopicWriterMessage("mess"))  # send text
    writer.write(ydb.TopicWriterMessage(bytes([1, 2, 3])))  # send bytes
    writer.write([ydb.TopicWriterMessage("mess-1"), ydb.TopicWriterMessage("mess-2")])  # send few messages by one call

    # with meta
    writer.write(ydb.TopicWriterMessage("asd", seqno=123, created_at=datetime.datetime.now()))


def send_message_without_block_if_internal_buffer_is_full(writer: ydb.TopicWriter, msg) -> bool:
    try:
        # put message to internal queue for send, but if buffer is full - fast return
        # without wait
        writer.write(msg, timeout=0)
        return True
    except TimeoutError():
        return False


def send_messages_with_manual_seqno(writer: ydb.TopicWriter):
    writer.write(ydb.TopicWriterMessage("mess"))  # send text


def send_messages_with_wait_ack(writer: ydb.TopicWriter):
    # Explicit future wait
    writer.async_write_with_ack(
        [
            ydb.TopicWriterMessage("mess", seqno=1),
            ydb.TopicWriterMessage("mess", seqno=2),
        ]
    ).result()

    # implicit, by sync call
    writer.write_with_ack(
        [
            ydb.TopicWriterMessage("mess", seqno=1),
            ydb.TopicWriterMessage("mess", seqno=2),
        ]
    )
    # write_with_ack

    # send with flush
    writer.write(["1", "2", "3"])
    writer.flush()


def send_messages_and_wait_all_commit_with_flush(writer: ydb.TopicWriter):
    for i in range(10):
        content = "%s" % i
        writer.write(content)
    writer.flush()


def send_messages_and_wait_all_commit_with_results(writer: ydb.TopicWriter):
    futures = []  # type: List[concurrent.futures.Future]
    for i in range(10):
        future = writer.async_write_with_ack()
        futures.append(future)

    concurrent.futures.wait(futures)
    for future in futures:
        if future.exception() is not None:
            raise future.exception()


def switch_messages_with_many_producers(writers: Dict[str, ydb.TopicWriter], messages: List[str]):
    futures = []  # type:  List[Future]

    for msg in messages:
        # select writer for the msg
        writer_idx = msg[:1]
        writer = writers[writer_idx]
        future = writer.async_write_with_ack(msg)
        futures.append(future)

    # wait acks from all writes
    wait(futures)
