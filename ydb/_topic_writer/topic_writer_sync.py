from __future__ import annotations

import asyncio
from concurrent.futures import Future
from typing import Union, List, Optional, Coroutine

from .._grpc.grpcwrapper.common_utils import SupportedDriverType
from .topic_writer import (
    PublicWriterSettings,
    TopicWriterError,
    PublicWriterInitInfo,
    PublicMessage,
    PublicWriteResult,
    MessageType,
)

from .topic_writer_asyncio import WriterAsyncIO
from .._topic_common.common import _get_shared_event_loop, TimeoutType


class WriterSync:
    _loop: asyncio.AbstractEventLoop
    _async_writer: WriterAsyncIO
    _closed: bool

    def __init__(
        self,
        driver: SupportedDriverType,
        settings: PublicWriterSettings,
        *,
        eventloop: Optional[asyncio.AbstractEventLoop] = None,
    ):

        self._closed = False

        if eventloop:
            self._loop = eventloop
        else:
            self._loop = _get_shared_event_loop()

        async def create_async_writer():
            return WriterAsyncIO(driver, settings)

        self._async_writer = asyncio.run_coroutine_threadsafe(
            create_async_writer(), self._loop
        ).result()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _call(self, coro):
        if self._closed:
            raise TopicWriterError("writer is closed")

        return asyncio.run_coroutine_threadsafe(coro, self._loop)

    def _call_sync(self, coro: Coroutine, timeout):
        f = self._call(coro)
        try:
            return f.result(timeout)
        except TimeoutError:
            f.cancel()
            raise

    def close(self, flush: bool = True):
        if self._closed:
            return

        self._closed = True

        # for no call self._call_sync on closed object
        asyncio.run_coroutine_threadsafe(
            self._async_writer.close(flush=flush), self._loop
        ).result()

    def async_flush(self) -> Future:
        if self._closed:
            raise TopicWriterError("writer is closed")
        return self._call(self._async_writer.flush())

    def flush(self, timeout=None):
        self._call_sync(self._async_writer.flush(), timeout)

    def async_wait_init(self) -> Future[PublicWriterInitInfo]:
        return self._call(self._async_writer.wait_init())

    def wait_init(self, timeout: Optional[TimeoutType] = None) -> PublicWriterInitInfo:
        return self._call_sync(self._async_writer.wait_init(), timeout)

    def write(
        self,
        message: Union[PublicMessage, List[PublicMessage]],
        *args: Optional[PublicMessage],
        timeout: Union[float, None] = None,
    ):
        self._call_sync(self._async_writer.write(message, *args), timeout=timeout)

    def async_write_with_ack(
        self,
        messages: Union[MessageType, List[MessageType]],
        *args: Optional[MessageType],
    ) -> Future[Union[PublicWriteResult, List[PublicWriteResult]]]:
        return self._call(self._async_writer.write_with_ack(messages, *args))

    def write_with_ack(
        self,
        messages: Union[MessageType, List[MessageType]],
        *args: Optional[MessageType],
        timeout: Union[float, None] = None,
    ) -> Union[PublicWriteResult, List[PublicWriteResult]]:
        return self._call_sync(
            self._async_writer.write_with_ack(messages, *args), timeout=timeout
        )
