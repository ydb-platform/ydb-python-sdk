from __future__ import annotations

import abc
import asyncio
import logging
from typing import Generic, Optional, Set, TypeVar

from .. import issues
from .._errors import check_retriable_error, ErrorRetryInfo
from .._utilities import AtomicCounter
from ..retries import RetrySettings

logger = logging.getLogger(__name__)

ConnT = TypeVar("ConnT")


class StreamReconnector(abc.ABC, Generic[ConnT]):
    """Connection lifecycle shared by the topic reader and writer.

    It owns exactly one background task — the reconnect loop — plus the fatal signal
    and the state-change event consumers wait on. Everything about *when* to reconnect
    (connect, run-until-error, classify, backoff, reconnect, teardown ordering) lives
    here once; subclasses plug in the per-protocol parts through the hooks below.

    Subclasses must set up their own attributes BEFORE calling ``super().__init__()``,
    because that call schedules the connection loop, which immediately uses ``_new_connection``
    and ``_handshake``.
    """

    _static_counter = AtomicCounter()

    def __init__(
        self,
        *,
        retry_settings: RetrySettings,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        self._id = StreamReconnector._static_counter.inc_and_get()
        self._retry_settings = retry_settings
        self._loop = loop if loop is not None else asyncio.get_running_loop()
        self._closed = False
        self._conn: Optional[ConnT] = None
        self._state_changed = asyncio.Event()
        self._fatal: asyncio.Future = self._loop.create_future()
        self._background_tasks: Set[asyncio.Task] = set()
        self._background_tasks.add(asyncio.create_task(self._connection_loop()))
        logger.debug("%s init id=%s", type(self).__name__, self._id)

    # ------------------------------------------------------------------ helpers for subclasses

    @property
    def connection(self) -> Optional[ConnT]:
        return self._conn

    def _signal_fatal(self, err: BaseException) -> None:
        """Record the terminal error (first one wins), run teardown, wake every waiter."""
        if self._fatal.done():
            self._state_changed.set()
            return
        self._fatal.set_result(err)
        self._on_fatal(err)
        self._state_changed.set()

    def _fatal_error(self) -> Optional[BaseException]:
        return self._fatal.result() if self._fatal.done() else None

    async def _wait_state_change(self) -> None:
        await self._state_changed.wait()
        self._state_changed.clear()

    # ------------------------------------------------------------------ the one reconnect loop

    async def _connection_loop(self) -> None:
        attempt = 0
        while True:
            if self._closed:
                return
            conn = None
            try:
                logger.debug("%s %s connect attempt %s", type(self).__name__, self._id, attempt)
                # Construct synchronously and take ownership BEFORE the first cancellable network
                # await, so a cancel during the handshake still reaches close() in the finally —
                # this is what makes "one stream, no zombie" structural rather than a contract.
                conn = self._new_connection()
                await self._handshake(conn)
                # Publish only after a successful handshake so consumers never observe a
                # half-initialized connection. Teardown still uses the local `conn` in the
                # finally, so an interrupted handshake is closed regardless (no zombie).
                self._conn = conn
                attempt = 0  # reset only on a successful connect — backoff grows across failures
                await self._on_connected(conn)
                self._state_changed.set()
                await self._run(conn)
            except BaseException as err:
                if isinstance(err, asyncio.CancelledError):
                    if self._closed:
                        raise  # let close() tear the loop down
                    # a cancelled gRPC call surfaces as CancelledError; treat it as a lost
                    # connection and reconnect instead of dying
                    err = issues.ConnectionLost("gRPC stream cancelled")
                logger.debug("%s %s loop error: %s", type(self).__name__, self._id, err)
                retry_info = self._classify_error(err, attempt)
                if not retry_info.is_retriable:
                    self._signal_fatal(err)
                    return
                await asyncio.sleep(retry_info.sleep_timeout_seconds or 0)
                attempt += 1
            finally:
                if conn is not None:
                    # noinspection PyBroadException
                    try:
                        await self._close_connection(conn, flush=False)
                    except asyncio.CancelledError:
                        # propagate cancellation (e.g. from close()) so the loop stops instead
                        # of swallowing it and reconnecting into a zombie connection
                        raise
                    except Exception:
                        pass  # suppress any error while closing the dead connection

    async def close(self, flush: bool) -> None:
        if self._closed:
            return
        logger.debug("%s %s close", type(self).__name__, self._id)
        # Mark closed first so the loop won't bring up a new connection, then close the live
        # one with the requested flush BEFORE cancelling the loop — cancelling first would let
        # the finally close it with flush=False and skip the flush.
        self._closed = True
        if self._conn is not None:
            await self._close_connection(self._conn, flush)
        # Wake any pending waiter so it doesn't hang if the loop was mid-reconnect.
        self._signal_fatal(self._terminal_error())
        for task in self._background_tasks:
            task.cancel()
        await asyncio.wait(self._background_tasks)

    # ------------------------------------------------------------------ hooks

    @abc.abstractmethod
    def _new_connection(self) -> ConnT:
        """Construct the connection object SYNCHRONOUSLY (no network). It must already own its
        transport, so close() is safe even if the handshake is later cancelled."""

    @abc.abstractmethod
    async def _handshake(self, conn: ConnT) -> None:
        """Open the call and run the init handshake on an already-constructed connection."""

    async def _on_connected(self, conn: ConnT) -> None:
        """Run right after a connection is established — restore state, capture init info,
        re-send buffered work. Default: nothing."""

    @abc.abstractmethod
    async def _run(self, conn: ConnT) -> None:
        """Block until this connection ends (it errors or is torn down)."""

    @abc.abstractmethod
    async def _close_connection(self, conn: ConnT, flush: bool) -> None:
        """Tear down a connection, optionally flushing its own per-stream state."""

    @abc.abstractmethod
    def _terminal_error(self) -> BaseException:
        """Error used to wake waiters once close() is called."""

    def _on_fatal(self, err: BaseException) -> None:
        """Synchronous teardown run once, when the reconnector terminates (e.g. fail pending
        writes). Default: nothing."""

    def _classify_error(self, err: BaseException, attempt: int) -> ErrorRetryInfo:
        """Decide whether ``err`` is retriable and how long to back off. Override to add
        protocol-specific rules (e.g. the writer disables retries inside a transaction)."""
        return check_retriable_error(err, self._retry_settings, attempt)
