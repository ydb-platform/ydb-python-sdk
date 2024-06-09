import asyncio
import concurrent.futures
import typing
from typing import List, Union, Optional

from ydb._grpc.grpcwrapper.common_utils import SupportedDriverType
from ydb._topic_common.common import (
    _get_shared_event_loop,
    CallFromSyncToAsync,
    TimeoutType,
)
from ydb._topic_reader import datatypes
from ydb._topic_reader.datatypes import PublicBatch
from ydb._topic_reader.topic_reader import (
    PublicReaderSettings,
    CommitResult,
)
from ydb._topic_reader.topic_reader_asyncio import (
    PublicAsyncIOReader,
    TopicReaderClosedError,
)


class TopicReaderSync:
    _caller: CallFromSyncToAsync
    _async_reader: PublicAsyncIOReader
    _closed: bool
    _parent: typing.Any  # need for prevent stop the client by GC

    def __init__(
        self,
        driver: SupportedDriverType,
        settings: PublicReaderSettings,
        *,
        eventloop: Optional[asyncio.AbstractEventLoop] = None,
        _parent=None,  # need for prevent stop the client by GC
    ):
        self._closed = False

        if eventloop:
            loop = eventloop
        else:
            loop = _get_shared_event_loop()

        self._caller = CallFromSyncToAsync(loop)

        async def create_reader():
            return PublicAsyncIOReader(driver, settings)

        self._async_reader = asyncio.run_coroutine_threadsafe(create_reader(), loop).result()

        self._parent = _parent

    def __del__(self):
        self.close(flush=False)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def receive_message(self, *, timeout: TimeoutType = None) -> datatypes.PublicMessage:
        """
        Block until receive new message
        It has no async_ version for prevent lost messages, use async_wait_message as signal for new batches available.
        receive_message(timeout=0) may return None even right after async_wait_message() is ok - because lost of partition
        or connection to server lost

        if no new message in timeout seconds (default - infinite): raise TimeoutError()
        if timeout <= 0 - it will fast wait only one event loop cycle - without wait any i/o operations or pauses, get messages from internal buffer only.
        """
        self._check_closed()

        return self._caller.safe_call_with_result(self._async_reader.receive_message(), timeout)

    def async_wait_message(self) -> concurrent.futures.Future:
        """
        Returns a future, which will complete when the reader has at least one message in queue.
        If the reader already has a message - the future will complete immediately.

        A message may expire before it gets read so that the attempt to receive the massage will fail
        despite the future has signaled about its availability.
        """
        self._check_closed()

        return self._caller.unsafe_call_with_future(self._async_reader.wait_message())

    def _make_batch_slice(
        self,
        batch: Union[PublicBatch, None],
        max_messages: typing.Union[int, None] = None,
        max_bytes: typing.Union[int, None] = None,
    ) -> Union[PublicBatch, None]:
        all_amount = float("inf")

        # A non-empty batch must stay non-empty regardless of the max messages value
        if max_messages is not None:
            max_messages = max(max_messages, 1)
        else:
            max_messages = all_amount

        if max_bytes is not None:
            max_bytes = max(max_bytes, 1)
        else:
            max_bytes = all_amount

        is_batch_set = batch is not None
        is_msg_limit_set = max_messages < all_amount
        is_bytes_limit_set = max_bytes < all_amount
        is_limit_set = is_msg_limit_set or is_bytes_limit_set
        is_slice_required = is_batch_set and is_limit_set

        if not is_slice_required:
            return batch

        sliced_messages = []
        bytes_taken = 0

        for batch_message in batch.messages:
            sliced_messages.append(batch_message)
            bytes_taken += len(batch_message.data)

            is_enough_messages = len(sliced_messages) >= max_messages
            is_enough_bytes = bytes_taken >= max_bytes
            is_stop_required = is_enough_messages or is_enough_bytes

            if is_stop_required:
                break

        sliced_batch = PublicBatch(
            messages=sliced_messages,
            _partition_session=batch._partition_session,
            _bytes_size=bytes_taken,
            _codec=batch._codec,
        )

        return sliced_batch

    def receive_batch(
        self,
        *,
        max_messages: typing.Union[int, None] = None,
        max_bytes: typing.Union[int, None] = None,
        timeout: Union[float, None] = None,
    ) -> Union[PublicBatch, None]:
        """
        Get one messages batch from reader
        It has no async_ version for prevent lost messages, use async_wait_message as signal for new batches available.

        if no new message in timeout seconds (default - infinite): raise TimeoutError()
        if timeout <= 0 - it will fast wait only one event loop cycle - without wait any i/o operations or pauses, get messages from internal buffer only.
        """
        self._check_closed()

        maybe_batch: Union[PublicBatch, None] = self._caller.safe_call_with_result(
            self._async_reader.receive_batch(),
            timeout,
        )

        return self._make_batch_slice(maybe_batch, max_messages, max_bytes)

    def commit(self, mess: typing.Union[datatypes.PublicMessage, datatypes.PublicBatch]):
        """
        Put commit message to internal buffer.

        For the method no way check the commit result
        (for example if lost connection - commits will not re-send and committed messages will receive again)
        """
        self._check_closed()

        self._caller.call_sync(lambda: self._async_reader.commit(mess))

    def commit_with_ack(
        self,
        mess: typing.Union[datatypes.PublicMessage, datatypes.PublicBatch],
        timeout: TimeoutType = None,
    ) -> Union[CommitResult, List[CommitResult]]:
        """
        write commit message to a buffer and wait ack from the server.

        if receive in timeout seconds (default - infinite): raise TimeoutError()
        """
        self._check_closed()

        return self._caller.unsafe_call_with_result(self._async_reader.commit_with_ack(mess), timeout)

    def async_commit_with_ack(
        self, mess: typing.Union[datatypes.PublicMessage, datatypes.PublicBatch]
    ) -> concurrent.futures.Future:
        """
        write commit message to a buffer and return Future for wait result.
        """
        self._check_closed()

        return self._caller.unsafe_call_with_future(self._async_reader.commit_with_ack(mess))

    def close(self, *, flush: bool = True, timeout: TimeoutType = None):
        if self._closed:
            return

        self._closed = True

        self._caller.safe_call_with_result(self._async_reader.close(flush), timeout)

    def _check_closed(self):
        if self._closed:
            raise TopicReaderClosedError()
