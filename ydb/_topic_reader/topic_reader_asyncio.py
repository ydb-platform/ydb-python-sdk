from __future__ import annotations

import asyncio
import enum
import typing
from collections import deque
from dataclasses import dataclass
from typing import Optional, Set, Dict

import ydb
from .datatypes import PartitionSession, PublicMessage, PublicBatch
from .topic_reader import PublicReaderSettings
from .._topic_wrapper.common import TokenGetterFuncType, IGrpcWrapperAsyncIO
from .._topic_wrapper.reader import StreamReadMessage


class TopicReaderError(ydb.Error):
    pass


class PublicAsyncIOReader:
    pass


class ReaderReconnector:
    pass


class ReaderStream:
    _token_getter: Optional[TokenGetterFuncType]
    _session_id: str
    _init_completed: asyncio.Future[None]
    _stream: Optional[IGrpcWrapperAsyncIO]

    _lock: asyncio.Lock
    _started: bool
    _closed: bool
    _first_error: Optional[ydb.Error]
    _background_tasks: Set[asyncio.Task]
    _partition_sessions: Dict[int, PartitionSession]
    _buffer_size_bytes: int  # use for init request, then for debug purposes only
    _message_batches: typing.Deque

    def __init__(self, settings: PublicReaderSettings):
        self._token_getter = settings._token_getter
        self._session_id = "not initialized"
        self._stream = None

        self._lock = asyncio.Lock()
        self._started = False
        self._closed = False
        self._first_error = None
        self._background_tasks = set()
        self._partition_sessions = dict()
        self._buffer_size_bytes = settings.buffer_size_bytes
        self._message_batches = deque()

    async def start(self, stream: IGrpcWrapperAsyncIO, init_message: StreamReadMessage.InitRequest):
        async with self._lock:
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

            read_messages_task = asyncio.create_task(self._read_messages(stream))
            self._background_tasks.add(read_messages_task)

    async def _read_messages(self, stream: IGrpcWrapperAsyncIO):
        try:
            self._stream.write(StreamReadMessage.FromClient(
                client_message=StreamReadMessage.ReadRequest(
                    bytes_size=self._buffer_size_bytes,
                ),
            ))
            while True:
                message = await stream.receive()  # type: StreamReadMessage.FromServer
                if isinstance(message.server_message, StreamReadMessage.ReadResponse):
                    await self._on_read_response(message.server_message)
                elif isinstance(message.server_message, StreamReadMessage.StartPartitionSessionRequest):
                    await self._on_start_partition_session_start(message.server_message)
                elif isinstance(message.server_message, StreamReadMessage.StopPartitionSessionRequest):
                    await self._on_partition_session_stop(message.server_message)
                else:
                    raise NotImplementedError(
                        "Unexpected type of StreamReadMessage.FromServer message: %s" % message.server_message
                    )
        except Exception as e:
            await self._set_first_error(e)
            raise e

    async def _on_start_partition_session_start(self, message: StreamReadMessage.StartPartitionSessionRequest):
        async with self._lock:
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
            except ydb.Error as err:
                self._set_first_error_locked(err)

    async def _on_partition_session_stop(self, message: StreamReadMessage.StopPartitionSessionRequest):
        async with self._lock:
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

    async def _on_read_response(self, message: StreamReadMessage.ReadResponse):
        batches = await self._read_response_to_batches(message)

        async with self._lock:
            self._message_batches.extend(batches)
            self._buffer_size_bytes -= message.bytes_size

    async def _read_response_to_batches(self, message: StreamReadMessage.ReadResponse) -> typing.List[PublicBatch]:
        batches = []

        batch_count = 0
        for partition_data in message.partition_data:
            batch_count += len(partition_data.batches)

        if batch_count == 0:
            return []

        bytes_per_batch = message.bytes_size // batch_count
        additional_bytes_to_last_batch = message.bytes_size - bytes_per_batch * batch_count

        for partition_data in message.partition_data:
            async with self._lock:
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

    async def _set_first_error(self, err):
        async with self._lock:
            self._set_first_error_locked(err)

    def _set_first_error_locked(self, err):
        if self._first_error is None:
            self._first_error = err

    async def close(self):
        async with self._lock:
            if self._closed:
                raise TopicReaderError(message="Double closed ReaderStream")
            self._closed = True
            self._set_first_error_locked(TopicReaderError("Reader closed"))

        for task in self._background_tasks:
            task.cancel()

        await asyncio.wait(self._background_tasks)
