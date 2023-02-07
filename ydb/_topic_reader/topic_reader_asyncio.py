from __future__ import annotations

import asyncio
import typing
from asyncio import Task
from collections import deque
from typing import Optional, Set, Dict


from .. import _apis, issues, RetrySettings
from ..aio import Driver
from ..issues import (
    Error as YdbError,
    _process_response
)
from .datatypes import PartitionSession, PublicMessage, PublicBatch
from .topic_reader import PublicReaderSettings
from .._topic_wrapper.common import TokenGetterFuncType, IGrpcWrapperAsyncIO, SupportedDriverType, GrpcWrapperAsyncIO
from .._topic_wrapper.reader import StreamReadMessage
from .._errors import check_retriable_error


class TopicReaderError(YdbError):
    pass


class TopicReaderStreamClosedError(TopicReaderError):
    def __init__(self):
        super().__init__("Topic reader is closed")


class PublicAsyncIOReader:
    _loop: asyncio.AbstractEventLoop
    _reconnector: ReaderReconnector

    def __init__(self, driver: Driver, settings: PublicReaderSettings):
        self._loop = asyncio.get_running_loop()
        self._reconnector = ReaderReconnector(driver, settings)

    async def wait_messages(self):
        await self._reconnector.wait_message()

    def receive_batch(self):
        return self._reconnector.receive_batch_nowait()


class ReaderReconnector:
    _settings: PublicReaderSettings
    _driver: Driver
    _background_tasks: Set[Task]

    _state_changed: asyncio.Event
    _stream_reader: Optional["ReaderStream"]
    _first_error: asyncio.Future[YdbError]

    def __init__(self, driver: Driver, settings: PublicReaderSettings):
        self._settings = settings
        self._driver = driver
        self._background_tasks = set()
        self._retry_settins = RetrySettings(idempotent=True)  # get from settings

        self._state_changed = asyncio.Event()
        self._stream_reader = None
        self._background_tasks.add(asyncio.create_task(self._connection_loop()))
        self._first_error = asyncio.get_running_loop().create_future()

    async def _connection_loop(self):
        attempt = 0
        while True:
            try:
                self._stream_reader = await ReaderStream.create(self._driver, self._settings)
                attempt = 0
                self._state_changed.set()
                await self._stream_reader.wait_error()
            except issues.Error as err:
                retry_info = check_retriable_error(err, self._settings._retry_settings(), attempt)
                if not retry_info.is_retriable:
                    self._set_first_error(err)
                    return
                await asyncio.sleep(retry_info.sleep_timeout_seconds)

                attempt += 1

    async def wait_message(self):
        while True:
            if self._first_error.done():
                raise self._first_error.result()

            if self._stream_reader is not None:
                try:
                    await self._stream_reader.wait_messages()
                    return
                except YdbError:
                    pass  # handle errors in reconnection loop

            await self._state_changed.wait()
            self._state_changed.clear()

    def receive_batch_nowait(self):
        return self._stream_reader.receive_batch_nowait()

    async def close(self):
        await self._stream_reader.close()
        for task in self._background_tasks:
            task.cancel()

        await asyncio.wait(self._background_tasks)

    def _set_first_error(self, err: issues.Error):
        try:
            self._first_error.set_result(err)
            self._state_changed.set()
        except asyncio.InvalidStateError:
            # skip if already has result
            pass


class ReaderStream:
    _token_getter: Optional[TokenGetterFuncType]
    _session_id: str
    _stream: Optional[IGrpcWrapperAsyncIO]
    _started: bool
    _background_tasks: Set[asyncio.Task]
    _partition_sessions: Dict[int, PartitionSession]
    _buffer_size_bytes: int  # use for init request, then for debug purposes only

    _state_changed: asyncio.Event
    _closed: bool
    _message_batches: typing.Deque[PublicBatch]
    _first_error: asyncio.Future[YdbError]

    def __init__(self, settings: PublicReaderSettings):
        self._token_getter = settings._token_getter
        self._session_id = "not initialized"
        self._stream = None
        self._started = False
        self._background_tasks = set()
        self._partition_sessions = dict()
        self._buffer_size_bytes = settings.buffer_size_bytes

        self._state_changed = asyncio.Event()
        self._closed = False
        self._first_error = asyncio.get_running_loop().create_future()
        self._message_batches = deque()

    @staticmethod
    async def create(
        driver: SupportedDriverType,
        settings: PublicReaderSettings,
    ) -> "ReaderStream":
        stream = GrpcWrapperAsyncIO(StreamReadMessage.FromServer.from_proto)

        await stream.start(
            driver, _apis.TopicService.Stub, _apis.TopicService.StreamRead
        )

        reader = ReaderStream(settings)
        await reader._start(stream, settings._init_message())
        return reader

    async def _start(self, stream: IGrpcWrapperAsyncIO, init_message: StreamReadMessage.InitRequest):
        if self._started:
            raise TopicReaderError("Double start ReaderStream")

        self._started = True
        self._stream = stream

        stream.write(StreamReadMessage.FromClient(client_message=init_message))
        init_response = await stream.receive()  # type: StreamReadMessage.FromServer
        if isinstance(init_response.server_message, StreamReadMessage.InitResponse):
            self._session_id = init_response.server_message.session_id
        else:
            raise TopicReaderError("Unexpected message after InitRequest: %s", init_response)

        read_messages_task = asyncio.create_task(self._read_messages_loop(stream))
        self._background_tasks.add(read_messages_task)

    async def wait_error(self):
        raise await self._first_error

    async def wait_messages(self):
        while True:
            if self._get_first_error() is not None:
                raise self._get_first_error()

            if len(self._message_batches) > 0:
                return

            await self._state_changed.wait()
            self._state_changed.clear()

    def receive_batch_nowait(self):
        if self._get_first_error() is not None:
            raise self._get_first_error()

        try:
            batch = self._message_batches.popleft()
            self._buffer_release_bytes(batch._bytes_size)
            return batch
        except IndexError:
            return None

    async def _read_messages_loop(self, stream: IGrpcWrapperAsyncIO):
        try:
            self._stream.write(StreamReadMessage.FromClient(
                client_message=StreamReadMessage.ReadRequest(
                    bytes_size=self._buffer_size_bytes,
                ),
            ))
            while True:
                message = await stream.receive()  # type: StreamReadMessage.FromServer
                _process_response(message.server_status)
                if isinstance(message.server_message, StreamReadMessage.ReadResponse):
                    self._on_read_response(message.server_message)
                elif isinstance(message.server_message, StreamReadMessage.StartPartitionSessionRequest):
                    self._on_start_partition_session_start(message.server_message)
                elif isinstance(message.server_message, StreamReadMessage.StopPartitionSessionRequest):
                    self._on_partition_session_stop(message.server_message)
                else:
                    raise NotImplementedError(
                        "Unexpected type of StreamReadMessage.FromServer message: %s" % message.server_message
                    )

                self._state_changed.set()
        except Exception as e:
            self._set_first_error(e)
            raise e

    def _on_start_partition_session_start(self, message: StreamReadMessage.StartPartitionSessionRequest):
        try:
            if message.partition_session.partition_session_id in self._partition_sessions:
                raise TopicReaderError(
                    "Double start partition session: %s" % message.partition_session.partition_session_id
                )

            self._partition_sessions[message.partition_session.partition_session_id] = PartitionSession(
                id=message.partition_session.partition_session_id,
                state=PartitionSession.State.Active,
                topic_path=message.partition_session.path,
                partition_id=message.partition_session.partition_id,
            )
            self._stream.write(StreamReadMessage.FromClient(
                client_message=StreamReadMessage.StartPartitionSessionResponse(
                    partition_session_id=message.partition_session.partition_session_id,
                    read_offset=0,
                    commit_offset=0,
                )),
            )
        except YdbError as err:
            self._set_first_error(err)

    def _on_partition_session_stop(self, message: StreamReadMessage.StopPartitionSessionRequest):
        partition = self._partition_sessions.get(message.partition_session_id)
        if partition is None:
            # may if receive stop partition with graceful=false after response on stop partition
            # with graceful=true and remove partition from internal dictionary
            return

        del self._partition_sessions[message.partition_session_id]
        partition.stop()

        if message.graceful:
            self._stream.write(StreamReadMessage.FromClient(
                client_message=StreamReadMessage.StopPartitionSessionResponse(
                    partition_session_id=message.partition_session_id,
                ))
            )

    def _on_read_response(self, message: StreamReadMessage.ReadResponse):
        batches = self._read_response_to_batches(message)
        self._message_batches.extend(batches)
        self._buffer_consume_bytes(message.bytes_size)

    def _buffer_consume_bytes(self, bytes_size):
        self._buffer_size_bytes -= bytes_size

    def _buffer_release_bytes(self, bytes_size):
        self._buffer_size_bytes += bytes_size
        self._stream.write(StreamReadMessage.FromClient(client_message=StreamReadMessage.ReadRequest(
            bytes_size=bytes_size,
        )))

    def _read_response_to_batches(self, message: StreamReadMessage.ReadResponse) -> typing.List[PublicBatch]:
        batches = []

        batch_count = 0
        for partition_data in message.partition_data:
            batch_count += len(partition_data.batches)

        if batch_count == 0:
            return []

        bytes_per_batch = message.bytes_size // batch_count
        additional_bytes_to_last_batch = message.bytes_size - bytes_per_batch * batch_count

        for partition_data in message.partition_data:
            partition_session = self._partition_sessions[partition_data.partition_session_id]
            for server_batch in partition_data.batches:
                messages = []
                for message_data in server_batch.message_data:
                    mess = PublicMessage(
                        seqno=message_data.seq_no,
                        created_at=message_data.created_at,
                        message_group_id=message_data.message_group_id,
                        session_metadata=server_batch.write_session_meta,
                        offset=message_data.offset,
                        written_at=server_batch.written_at,
                        producer_id=server_batch.producer_id,
                        data=message_data.data,
                        _partition_session=partition_session,
                    )
                    messages.append(mess)
                batch = PublicBatch(
                    session_metadata=server_batch.write_session_meta,
                    messages=messages,
                    _partition_session=partition_session,
                    _bytes_size=bytes_per_batch,
                )
                batches.append(batch)

        batches[-1]._bytes_size += additional_bytes_to_last_batch
        return batches

    def _set_first_error(self, err: ydb.Error):
        try:
            self._first_error.set_result(err)
            self._state_changed.set()
        except asyncio.InvalidStateError:
            # skip later set errors
            pass

    def _get_first_error(self) -> Optional[ydb.Error]:
        if self._first_error.done():
            return self._first_error.result()
        else:
            return None

    async def close(self):
        if self._closed:
            raise TopicReaderError(message="Double closed ReaderStream")

        self._closed = True
        self._set_first_error(TopicReaderStreamClosedError())
        self._state_changed.set()

        for task in self._background_tasks:
            task.cancel()

        await asyncio.wait(self._background_tasks)
