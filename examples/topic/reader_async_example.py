import asyncio
import json
import time

import ydb


async def connect():
    db = ydb.aio.Driver(
        connection_string="grpc://localhost:2135?database=/local",
        credentials=ydb.credentials.AnonymousCredentials(),
    )
    reader = ydb.TopicClientAsyncIO(db).topic_reader(
        "/local/topic", consumer="consumer"
    )
    return reader


async def create_reader_and_close_with_context_manager(db: ydb.aio.Driver):
    with ydb.TopicClientAsyncIO(db).topic_reader(
        "/database/topic/path", consumer="consumer"
    ) as reader:
        async for message in reader.messages():
            pass


async def print_message_content(reader: ydb.TopicReaderAsyncIO):
    async for message in reader.messages():
        print("text", message.data.read().decode("utf-8"))
        # await and async_commit need only for sync commit mode - for wait ack from servr
        await reader.commit(message)


async def process_messages_batch_explicit_commit(reader: ydb.TopicReaderAsyncIO):
    # Explicit commit example
    async for batch in reader.batches(max_messages=100, timeout=2):
        async with asyncio.TaskGroup() as tg:
            for message in batch.messages:
                tg.create_task(_process(message))

        # wait complete of process all messages from batch be taskgroup context manager
        # and commit complete batch
        await reader.commit(batch)


async def process_messages_batch_context_manager_commit(reader: ydb.TopicReaderAsyncIO):
    # Commit with context manager
    async for batch in reader.batches():
        async with reader.commit_on_exit(batch), asyncio.TaskGroup() as tg:
            for message in batch.messages:
                tg.create_task(_process(message))


async def get_message_with_timeout(reader: ydb.TopicReaderAsyncIO):
    try:
        message = await asyncio.wait_for(reader.receive_message(), timeout=1)
    except TimeoutError:
        print("Have no new messages in a second")
        return

    print("mess", message.data)


async def get_all_messages_with_small_wait(reader: ydb.TopicReaderAsyncIO):
    async for message in reader.messages(timeout=1):
        await _process(message)
    print("Have no new messages in a second")


async def get_a_message_from_external_loop(reader: ydb.TopicReaderAsyncIO):
    for i in range(10):
        try:
            message = await asyncio.wait_for(reader.receive_message(), timeout=1)
        except TimeoutError:
            return
        await _process(message)


async def get_one_batch_from_external_loop_async(reader: ydb.TopicReaderAsyncIO):
    for i in range(10):
        try:
            batch = await asyncio.wait_for(reader.receive_batch(), timeout=2)
        except TimeoutError:
            return

        for message in batch.messages:
            await _process(message)
        await reader.commit(batch)


async def auto_deserialize_message(db: ydb.aio.Driver):
    # async, batch work similar to this

    async with ydb.TopicClientAsyncIO(db).topic_reader(
        "/database/topic/path", consumer="asd", deserializer=json.loads
    ) as reader:
        async for message in reader.messages():
            print(
                message.data.Name
            )  # message.data replaces by json.loads(message.data) of raw message
            reader.commit(message)


async def commit_batch_with_context(reader: ydb.TopicReaderAsyncIO):
    async for batch in reader.batches():
        async with reader.commit_on_exit(batch):
            for message in batch.messages:
                if not batch.is_alive:
                    break
                await _process(message)


async def handle_partition_stop(reader: ydb.TopicReaderAsyncIO):
    async for message in reader.messages():
        time.sleep(1)  # some work
        if message.is_alive:
            time.sleep(123)  # some other work
            await reader.commit(message)


async def handle_partition_stop_batch(reader: ydb.TopicReaderAsyncIO):
    def process_batch(batch):
        for message in batch.messages:
            if not batch.is_alive:
                # no reason work with expired batch
                # go read next - good batch
                return
            await _process(message)
        await reader.commit(batch)

    async for batch in reader.batches():
        process_batch(batch)


async def connect_and_read_few_topics(db: ydb.aio.Driver):
    with ydb.TopicClientAsyncIO(db).topic_reader(
        [
            "/database/topic/path",
            ydb.TopicSelector("/database/second-topic", partitions=3),
        ]
    ) as reader:
        async for message in reader.messages():
            await _process(message)
            await reader.commit(message)


async def handle_partition_graceful_stop_batch(reader: ydb.TopicReaderAsyncIO):
    # no special handle, but batch will contain less than prefer count messages
    async for batch in reader.batches():
        await _process(batch)
        reader.commit(batch)


async def advanced_commit_notify(db: ydb.aio.Driver):
    def on_commit(event: ydb.TopicReaderEvents.OnCommit) -> None:
        print(event.topic)
        print(event.offset)

    async with ydb.TopicClientAsyncIO(db).topic_reader(
        "/local", consumer="consumer", commit_batch_time=4, on_commit=on_commit
    ) as reader:
        async for message in reader.messages():
            await _process(message)
            await reader.commit(message)


async def advanced_read_with_own_progress_storage(db: ydb.TopicReaderAsyncIO):
    async def on_get_partition_start_offset(
        req: ydb.TopicReaderEvents.OnPartitionGetStartOffsetRequest,
    ) -> ydb.TopicReaderEvents.OnPartitionGetStartOffsetResponse:
        # read current progress from database
        resp = ydb.TopicReaderEvents.OnPartitionGetStartOffsetResponse()
        resp.start_offset = 123
        return resp

    async with ydb.TopicClient(db).topic_reader(
        "/local/test",
        consumer="consumer",
        on_get_partition_start_offset=on_get_partition_start_offset,
    ) as reader:
        async for mess in reader.messages():
            await _process(mess)
            # save progress to own database

            # no commit progress to topic service
            # reader.commit(mess)


async def _process(msg):
    raise NotImplementedError()
