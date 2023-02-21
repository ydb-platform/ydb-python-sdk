from __future__ import annotations

import asyncio
import os
from concurrent.futures import Future, ThreadPoolExecutor
import threading
from typing import Union, List, Optional, Coroutine

from . import topic_writer
from .._grpc.grpcwrapper.common_utils import SupportedDriverType
from .topic_writer import (
    PublicWriterSettings,
    TopicWriterError,
    PublicWriterInitInfo,
    PublicMessage,
    PublicWriteResult,
)

from .topic_writer_asyncio import WriterAsyncIO

_shared_event_loop_lock = threading.Lock()
_shared_event_loop = None  # type: Optional[asyncio.AbstractEventLoop]


def _get_shared_event_loop() -> asyncio.AbstractEventLoop:
    global _shared_event_loop

    if _shared_event_loop is not None:
        return _shared_event_loop

    with _shared_event_loop_lock:
        if _shared_event_loop is not None:
            return _shared_event_loop

        event_loop_set_done = Future()

        def start_event_loop():
            global _shared_event_loop

            max_workers = min(32, (os.cpu_count() or 1) + 4)
            max_workers = max(max_workers, 10)
            executor = ThreadPoolExecutor(max_workers=max_workers)

            _shared_event_loop = asyncio.new_event_loop()
            _shared_event_loop.set_default_executor(executor)
            event_loop_set_done.set_result(None)
            asyncio.set_event_loop(_shared_event_loop)
            _shared_event_loop.run_forever()

        t = threading.Thread(
            target=start_event_loop,
            name="Common ydb topic writer event loop",
            daemon=True,
        )
        t.start()

        event_loop_set_done.result()
        return _shared_event_loop


class PublicWriterSync:
    _loop: asyncio.AbstractEventLoop
    _async_writer: WriterAsyncIO
    _closed: bool

    def __init__(
        self,
        driver: SupportedDriverType,
        settings: PublicWriterSettings,
        *,
        eventloop: asyncio.AbstractEventLoop = None,
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

    def __enter__(self) -> PublicWriterSync:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _call(self, coro, *args, **kwargs):
        if self._closed:
            raise TopicWriterError("writer is closed")

        return asyncio.run_coroutine_threadsafe(coro, self._loop)

    def _call_sync(self, coro: Coroutine, timeout, *args, **kwargs):
        f = self._call(coro, *args, **kwargs)
        try:
            return f.result()
        except TimeoutError:
            f.cancel()
            raise

    def close(self):
        if self._closed:
            return
        self._closed = True
        asyncio.run_coroutine_threadsafe(
            self._async_writer.close(), self._loop
        ).result()

    def async_flush(self) -> Future:
        if self._closed:
            raise TopicWriterError("writer is closed")
        return self._call(self._async_writer.flush())

    def flush(self, timeout=None):
        self._call_sync(self._async_writer.flush(), timeout)

    def async_wait_init(self) -> Future[PublicWriterInitInfo]:
        return self._call(self._async_writer.wait_init())

    def wait_init(
        self, timeout: Union[int, float, None] = None
    ) -> PublicWriterInitInfo:
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
        messages: Union[topic_writer.MessageType, List[topic_writer.MessageType]],
        *args: Optional[topic_writer.MessageType],
    ) -> Future[Union[PublicWriteResult, List[PublicWriteResult]]]:
        return self._call(self._async_writer.write_with_ack(messages, *args))

    def write_with_ack(
        self,
        messages: Union[topic_writer.MessageType, List[topic_writer.MessageType]],
        *args: Optional[topic_writer.MessageType],
        timeout: Union[float, None] = None,
    ) -> Union[PublicWriteResult, List[PublicWriteResult]]:
        return self._call_sync(
            self._async_writer.write_with_ack(messages, *args), timeout=timeout
        )
