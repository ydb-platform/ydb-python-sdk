from __future__ import annotations

import asyncio
import concurrent.futures
import gzip
import typing
from asyncio import Task
from collections import deque
from typing import Optional, Set, Dict

from .. import _apis, issues, RetrySettings
from .._utilities import AtomicCounter
from ..aio import Driver
from ..issues import Error as YdbError, _process_response
from . import datatypes
from . import topic_reader
from .._grpc.grpcwrapper.common_utils import (
    IGrpcWrapperAsyncIO,
    SupportedDriverType,
    GrpcWrapperAsyncIO,
)
from .._grpc.grpcwrapper.ydb_topic import StreamReadMessage, Codec
from .._errors import check_retriable_error


class TopicReaderError(YdbError):
    pass


class TopicReaderUnexpectedCodec(YdbError):
    pass


class TopicReaderCommitToExpiredPartition(TopicReaderError):
    """
    Commit message when partition read session are dropped.
    It is ok - the message/batch will not commit to server and will receive in other read session
    (with this or other reader).
    """

    def __init__(self, message: str = "Topic reader partition session is closed"):
        super().__init__(message)


class TopicReaderStreamClosedError(TopicReaderError):
    def __init__(self):
        super().__init__("Topic reader stream is closed")


class TopicReaderClosedError(TopicReaderError):
    def __init__(self):
        super().__init__("Topic reader is closed already")


class PublicAsyncIOReader:
    _loop: asyncio.AbstractEventLoop
    _closed: bool
    _reconnector: ReaderReconnector

    def __init__(self, driver: Driver, settings: topic_reader.PublicReaderSettings):
        self._loop = asyncio.get_running_loop()
        self._closed = False
        self._reconnector = ReaderReconnector(driver, settings)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def __del__(self):
        if not self._closed:
            self._loop.create_task(self.close(), name="close reader")

    async def sessions_stat(self) -> typing.List["topic_reader.SessionStat"]:
        """
        Receive stat from the server

        use asyncio.wait_for for wait with timeout.
        """
        raise NotImplementedError()

    def messages(
        self, *, timeout: typing.Union[float, None] = None
    ) -> typing.AsyncIterable[topic_reader.PublicMessage]:
        """
        Block until receive new message

        if no new messages in timeout seconds: stop iteration by raise StopAsyncIteration
        """
        raise NotImplementedError()

    async def receive_message(self) -> typing.Union[topic_reader.PublicMessage, None]:
        """
        Block until receive new message

        use asyncio.wait_for for wait with timeout.
        """
        raise NotImplementedError()

    def batches(
        self,
        *,
        max_messages: typing.Union[int, None] = None,
        max_bytes: typing.Union[int, None] = None,
        timeout: typing.Union[float, None] = None,
    ) -> typing.AsyncIterable[datatypes.PublicBatch]:
        """
        Block until receive new batch.
        All messages in a batch from same partition.

        if no new message in timeout seconds (default - infinite): stop iterations by raise StopIteration
        """
        raise NotImplementedError()

    async def receive_batch(
        self,
        *,
        max_messages: typing.Union[int, None] = None,
        max_bytes: typing.Union[int, None] = None,
    ) -> typing.Union[datatypes.PublicBatch, None]:
        """
        Get one messages batch from reader.
        All messages in a batch from same partition.

        use asyncio.wait_for for wait with timeout.
        """
        await self._reconnector.wait_message()
        return self._reconnector.receive_batch_nowait()

    async def commit_on_exit(
        self, mess: datatypes.ICommittable
    ) -> typing.AsyncContextManager:
        """
        commit the mess match/message if exit from context manager without exceptions

        reader will close if exit from context manager with exception
        """
        raise NotImplementedError()

    def commit(
        self, batch: typing.Union[datatypes.PublicMessage, datatypes.PublicBatch]
    ):
        """
        Write commit message to a buffer.

        For the method no way check the commit result
        (for example if lost connection - commits will not re-send and committed messages will receive again)
        """
        self._reconnector.commit(batch)

    async def commit_with_ack(
        self, batch: typing.Union[datatypes.PublicMessage, datatypes.PublicBatch]
    ):
        """
        write commit message to a buffer and wait ack from the server.

        use asyncio.wait_for for wait with timeout.
        """
        waiter = self._reconnector.commit(batch)
        await waiter.future

    async def flush(self):
        """
        force send all commit messages from internal buffers to server and wait acks for all of them.

        use asyncio.wait_for for wait with timeout.
        """
        raise NotImplementedError()

    async def close(self):
        if self._closed:
            raise TopicReaderClosedError()

        self._closed = True
        await self._reconnector.close()


class ReaderReconnector:
    _static_reader_reconnector_counter = AtomicCounter()

    _id: int
    _settings: topic_reader.PublicReaderSettings
    _driver: Driver
    _background_tasks: Set[Task]

    _state_changed: asyncio.Event
    _stream_reader: Optional["ReaderStream"]
    _first_error: asyncio.Future[YdbError]

    def __init__(self, driver: Driver, settings: topic_reader.PublicReaderSettings):
        self._id = self._static_reader_reconnector_counter.inc_and_get()

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
                self._stream_reader = await ReaderStream.create(
                    self._id, self._driver, self._settings
                )
                attempt = 0
                self._state_changed.set()
                await self._stream_reader.wait_error()
            except issues.Error as err:
                retry_info = check_retriable_error(
                    err, self._settings._retry_settings(), attempt
                )
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

    def commit(
        self, batch: datatypes.ICommittable
    ) -> datatypes.PartitionSession.CommitAckWaiter:
        return self._stream_reader.commit(batch)

    async def close(self):
        if self._stream_reader:
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
    _static_id_counter = AtomicCounter()

    _loop: asyncio.AbstractEventLoop
    _id: int
    _reader_reconnector_id: int
    _session_id: str
    _stream: Optional[IGrpcWrapperAsyncIO]
    _started: bool
    _background_tasks: Set[asyncio.Task]
    _partition_sessions: Dict[int, datatypes.PartitionSession]
    _buffer_size_bytes: int  # use for init request, then for debug purposes only
    _decode_executor: concurrent.futures.Executor
    _decoders: Dict[
        int, typing.Callable[[bytes], bytes]
    ]  # dict[codec_code] func(encoded_bytes)->decoded_bytes

    if typing.TYPE_CHECKING:
        _batches_to_decode: asyncio.Queue[datatypes.PublicBatch]
    else:
        _batches_to_decode: asyncio.Queue

    _state_changed: asyncio.Event
    _closed: bool
    _message_batches: typing.Deque[datatypes.PublicBatch]
    _first_error: asyncio.Future[YdbError]

    def __init__(
        self, reader_reconnector_id: int, settings: topic_reader.PublicReaderSettings
    ):
        self._loop = asyncio.get_running_loop()
        self._id = ReaderStream._static_id_counter.inc_and_get()
        self._reader_reconnector_id = reader_reconnector_id
        self._session_id = "not initialized"
        self._stream = None
        self._started = False
        self._background_tasks = set()
        self._partition_sessions = dict()
        self._buffer_size_bytes = settings.buffer_size_bytes
        self._decode_executor = settings.decoder_executor

        self._decoders = {Codec.CODEC_GZIP: gzip.decompress}
        if settings.decoders:
            self._decoders.update(settings.decoders)

        self._state_changed = asyncio.Event()
        self._closed = False
        self._first_error = asyncio.get_running_loop().create_future()
        self._batches_to_decode = asyncio.Queue()
        self._message_batches = deque()

    @staticmethod
    async def create(
        reader_reconnector_id: int,
        driver: SupportedDriverType,
        settings: topic_reader.PublicReaderSettings,
    ) -> "ReaderStream":
        stream = GrpcWrapperAsyncIO(StreamReadMessage.FromServer.from_proto)

        await stream.start(
            driver, _apis.TopicService.Stub, _apis.TopicService.StreamRead
        )

        reader = ReaderStream(reader_reconnector_id, settings)
        await reader._start(stream, settings._init_message())
        return reader

    async def _start(
        self, stream: IGrpcWrapperAsyncIO, init_message: StreamReadMessage.InitRequest
    ):
        if self._started:
            raise TopicReaderError("Double start ReaderStream")

        self._started = True
        self._stream = stream

        stream.write(StreamReadMessage.FromClient(client_message=init_message))
        init_response = await stream.receive()  # type: StreamReadMessage.FromServer
        if isinstance(init_response.server_message, StreamReadMessage.InitResponse):
            self._session_id = init_response.server_message.session_id
        else:
            raise TopicReaderError(
                "Unexpected message after InitRequest: %s", init_response
            )

        self._background_tasks.add(
            asyncio.create_task(self._read_messages_loop(stream))
        )
        self._background_tasks.add(asyncio.create_task(self._decode_batches_loop()))

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

    def commit(
        self, batch: datatypes.ICommittable
    ) -> datatypes.PartitionSession.CommitAckWaiter:
        partition_session = batch._commit_get_partition_session()

        if partition_session.reader_reconnector_id != self._reader_reconnector_id:
            raise TopicReaderError("reader can commit only self-produced messages")

        if partition_session.reader_stream_id != self._id:
            raise TopicReaderCommitToExpiredPartition(
                "commit messages after reconnect to server"
            )

        if partition_session.id not in self._partition_sessions:
            raise TopicReaderCommitToExpiredPartition(
                "commit messages after server stop the partition read session"
            )

        commit_range = batch._commit_get_offsets_range()
        waiter = partition_session.add_waiter(commit_range.end)

        if not waiter.future.done():
            client_message = StreamReadMessage.CommitOffsetRequest(
                commit_offsets=[
                    StreamReadMessage.CommitOffsetRequest.PartitionCommitOffset(
                        partition_session_id=partition_session.id,
                        offsets=[commit_range],
                    )
                ]
            )
            self._stream.write(
                StreamReadMessage.FromClient(client_message=client_message)
            )

        return waiter

    async def _read_messages_loop(self, stream: IGrpcWrapperAsyncIO):
        try:
            self._stream.write(
                StreamReadMessage.FromClient(
                    client_message=StreamReadMessage.ReadRequest(
                        bytes_size=self._buffer_size_bytes,
                    ),
                )
            )
            while True:
                message = await stream.receive()  # type: StreamReadMessage.FromServer
                _process_response(message.server_status)
                if isinstance(message.server_message, StreamReadMessage.ReadResponse):
                    self._on_read_response(message.server_message)
                elif isinstance(
                    message.server_message, StreamReadMessage.CommitOffsetResponse
                ):
                    self._on_commit_response(message.server_message)
                elif isinstance(
                    message.server_message,
                    StreamReadMessage.StartPartitionSessionRequest,
                ):
                    self._on_start_partition_session(message.server_message)
                elif isinstance(
                    message.server_message,
                    StreamReadMessage.StopPartitionSessionRequest,
                ):
                    self._on_partition_session_stop(message.server_message)
                else:
                    raise NotImplementedError(
                        "Unexpected type of StreamReadMessage.FromServer message: %s"
                        % message.server_message
                    )

                self._state_changed.set()
        except Exception as e:
            self._set_first_error(e)
            raise e

    def _on_start_partition_session(
        self, message: StreamReadMessage.StartPartitionSessionRequest
    ):
        try:
            if (
                message.partition_session.partition_session_id
                in self._partition_sessions
            ):
                raise TopicReaderError(
                    "Double start partition session: %s"
                    % message.partition_session.partition_session_id
                )

            self._partition_sessions[
                message.partition_session.partition_session_id
            ] = datatypes.PartitionSession(
                id=message.partition_session.partition_session_id,
                state=datatypes.PartitionSession.State.Active,
                topic_path=message.partition_session.path,
                partition_id=message.partition_session.partition_id,
                committed_offset=message.committed_offset,
                reader_reconnector_id=self._reader_reconnector_id,
                reader_stream_id=self._id,
            )
            self._stream.write(
                StreamReadMessage.FromClient(
                    client_message=StreamReadMessage.StartPartitionSessionResponse(
                        partition_session_id=message.partition_session.partition_session_id,
                        read_offset=None,
                        commit_offset=None,
                    )
                ),
            )
        except YdbError as err:
            self._set_first_error(err)

    def _on_partition_session_stop(
        self, message: StreamReadMessage.StopPartitionSessionRequest
    ):
        try:
            partition = self._partition_sessions[message.partition_session_id]
        except KeyError:
            # may if receive stop partition with graceful=false after response on stop partition
            # with graceful=true and remove partition from internal dictionary
            return

        del self._partition_sessions[message.partition_session_id]
        partition.close()

        if message.graceful:
            self._stream.write(
                StreamReadMessage.FromClient(
                    client_message=StreamReadMessage.StopPartitionSessionResponse(
                        partition_session_id=message.partition_session_id,
                    )
                )
            )

    def _on_read_response(self, message: StreamReadMessage.ReadResponse):
        self._buffer_consume_bytes(message.bytes_size)

        batches = self._read_response_to_batches(message)
        for batch in batches:
            self._batches_to_decode.put_nowait(batch)

    def _on_commit_response(self, message: StreamReadMessage.CommitOffsetResponse):
        for partition_offset in message.partitions_committed_offsets:
            session = self._partition_sessions.get(
                partition_offset.partition_session_id
            )
            if session is None:
                continue
            session.ack_notify(partition_offset.committed_offset)

    def _buffer_consume_bytes(self, bytes_size):
        self._buffer_size_bytes -= bytes_size

    def _buffer_release_bytes(self, bytes_size):
        self._buffer_size_bytes += bytes_size
        self._stream.write(
            StreamReadMessage.FromClient(
                client_message=StreamReadMessage.ReadRequest(
                    bytes_size=bytes_size,
                )
            )
        )

    def _read_response_to_batches(
        self, message: StreamReadMessage.ReadResponse
    ) -> typing.List[datatypes.PublicBatch]:
        batches = []

        batch_count = 0
        for partition_data in message.partition_data:
            batch_count += len(partition_data.batches)

        if batch_count == 0:
            return []

        bytes_per_batch = message.bytes_size // batch_count
        additional_bytes_to_last_batch = (
            message.bytes_size - bytes_per_batch * batch_count
        )

        for partition_data in message.partition_data:
            partition_session = self._partition_sessions[
                partition_data.partition_session_id
            ]
            for server_batch in partition_data.batches:
                messages = []
                for message_data in server_batch.message_data:
                    mess = datatypes.PublicMessage(
                        seqno=message_data.seq_no,
                        created_at=message_data.created_at,
                        message_group_id=message_data.message_group_id,
                        session_metadata=server_batch.write_session_meta,
                        offset=message_data.offset,
                        written_at=server_batch.written_at,
                        producer_id=server_batch.producer_id,
                        data=message_data.data,
                        _partition_session=partition_session,
                        _commit_start_offset=partition_session._next_message_start_commit_offset,
                        _commit_end_offset=message_data.offset + 1,
                    )
                    messages.append(mess)

                    partition_session._next_message_start_commit_offset = (
                        mess._commit_end_offset
                    )

                if len(messages) > 0:
                    batch = datatypes.PublicBatch(
                        session_metadata=server_batch.write_session_meta,
                        messages=messages,
                        _partition_session=partition_session,
                        _bytes_size=bytes_per_batch,
                        _codec=Codec(server_batch.codec),
                    )
                    batches.append(batch)

        batches[-1]._bytes_size += additional_bytes_to_last_batch
        return batches

    async def _decode_batches_loop(self):
        while True:
            batch = await self._batches_to_decode.get()
            await self._decode_batch_inplace(batch)
            self._message_batches.append(batch)
            self._state_changed.set()

    async def _decode_batch_inplace(self, batch):
        if batch._codec == Codec.CODEC_RAW:
            return

        try:
            decode_func = self._decoders[batch._codec]
        except KeyError:
            raise TopicReaderUnexpectedCodec(
                "Receive message with unexpected codec: %s" % batch._codec
            )

        decode_data_futures = []
        for message in batch.messages:
            future = self._loop.run_in_executor(
                self._decode_executor, decode_func, message.data
            )
            decode_data_futures.append(future)

        decoded_data = await asyncio.gather(*decode_data_futures)
        for index, message in enumerate(batch.messages):
            message.data = decoded_data[index]

        batch._codec = Codec.CODEC_RAW

    def _set_first_error(self, err: YdbError):
        try:
            self._first_error.set_result(err)
            self._state_changed.set()
        except asyncio.InvalidStateError:
            # skip later set errors
            pass

    def _get_first_error(self) -> Optional[YdbError]:
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
        self._stream.close()

        for session in self._partition_sessions.values():
            session.close()

        for task in self._background_tasks:
            task.cancel()

        await asyncio.wait(self._background_tasks)
