import json
import time

import ydb


def connect():
    db = ydb.Driver(
        connection_string="grpc://localhost:2135?database=/local",
        credentials=ydb.credentials.AnonymousCredentials(),
    )
    reader = db.topic_client.reader("/local/topic", consumer="consumer")
    return reader


def create_reader_and_close_with_context_manager(db: ydb.Driver):
    with db.topic_client.reader(
        "/database/topic/path", consumer="consumer", buffer_size_bytes=123
    ) as reader:
        while True:
            message = reader.receive_message()  # noqa
            pass


def print_message_content(reader: ydb.TopicReader):
    while True:
        message = reader.receive_message()
        print("text", message.data.read().decode("utf-8"))
        reader.commit(message)


def process_messages_batch_explicit_commit(reader: ydb.TopicReader):
    while True:
        batch = reader.receive_batch()
        for message in batch.messages:
            _process(message)
        reader.commit(batch)


def process_messages_batch_context_manager_commit(reader: ydb.TopicReader):
    while True:
        batch = reader.receive_batch()
        with reader.commit_on_exit(batch):
            for message in batch.messages:
                _process(message)


def get_message_with_timeout(reader: ydb.TopicReader):
    try:
        message = reader.receive_message(timeout=1)
    except TimeoutError:
        print("Have no new messages in a second")
        return

    print("mess", message.data)


def get_all_messages_with_small_wait(reader: ydb.TopicReader):
    while True:
        try:
            message = reader.receive_message(timeout=1)
            _process(message)
        except TimeoutError:
            print("Have no new messages in a second")


def get_a_message_from_external_loop(reader: ydb.TopicReader):
    for i in range(10):
        try:
            message = reader.receive_message(timeout=1)
        except TimeoutError:
            return
        _process(message)


def get_one_batch_from_external_loop(reader: ydb.TopicReader):
    for i in range(10):
        try:
            batch = reader.receive_batch(timeout=2)
        except TimeoutError:
            return

        for message in batch.messages:
            _process(message)
        reader.commit(batch)


def auto_deserialize_message(db: ydb.Driver):
    # async, batch work similar to this

    reader = db.topic_client.reader(
        "/database/topic/path", consumer="asd", deserializer=json.loads
    )
    while True:
        message = reader.receive_message()
        print(
            message.data.Name
        )  # message.data replaces by json.loads(message.data) of raw message
        reader.commit(message)


def handle_partition_stop(reader: ydb.TopicReader):
    while True:
        message = reader.receive_message()
        time.sleep(123)  # some work
        if message.is_alive:
            time.sleep(1)  # some other work
            reader.commit(message)


def handle_partition_stop_batch(reader: ydb.TopicReader):
    def process_batch(batch):
        for message in batch.messages:
            if not batch.is_alive:
                # no reason work with expired batch
                # go read next - good batch
                return
            _process(message)
        reader.commit(batch)

    while True:
        batch = reader.receive_batch()
        process_batch(batch)


def connect_and_read_few_topics(db: ydb.Driver):
    with db.topic_client.reader(
        [
            "/database/topic/path",
            ydb.TopicSelector("/database/second-topic", partitions=3),
        ]
    ) as reader:
        while True:
            message = reader.receive_message()
            _process(message)
            reader.commit(message)


def handle_partition_graceful_stop_batch(reader: ydb.TopicReader):
    # no special handle, but batch will contain less than prefer count messages
    while True:
        batch = reader.receive_batch()
        _process(batch)
        reader.commit(batch)


def advanced_commit_notify(db: ydb.Driver):
    def on_commit(event: ydb.TopicReaderEvents.OnCommit) -> None:
        print(event.topic)
        print(event.offset)

    with db.topic_client.reader(
        "/local", consumer="consumer", commit_batch_time=4, on_commit=on_commit
    ) as reader:
        while True:
            message = reader.receive_message()
            with reader.commit_on_exit(message):
                _process(message)


def advanced_read_with_own_progress_storage(db: ydb.TopicReader):
    def on_get_partition_start_offset(
        req: ydb.TopicReaderEvents.OnPartitionGetStartOffsetRequest,
    ) -> ydb.TopicReaderEvents.OnPartitionGetStartOffsetResponse:

        # read current progress from database
        resp = ydb.TopicReaderEvents.OnPartitionGetStartOffsetResponse()
        resp.start_offset = 123
        return resp

    with db.topic_client.reader(
        "/local/test",
        consumer="consumer",
        on_get_partition_start_offset=on_get_partition_start_offset,
    ) as reader:
        while True:
            mess = reader.receive_message()
            _process(mess)
            # save progress to own database

            # no commit progress to topic service
            # reader.commit(mess)


def get_current_statistics(reader: ydb.TopicReader):
    # sync
    stat = reader.sessions_stat()
    print(stat)

    # with feature
    f = reader.async_sessions_stat()
    stat = f.result()
    print(stat)


def _process(msg):
    raise NotImplementedError()
