from __future__ import annotations

import abc
import asyncio
import logging
from typing import Any, Awaitable, Callable, Optional, Set, Union

from .._grpc.grpcwrapper.common_utils import GrpcWrapperAsyncIO, IGrpcWrapperAsyncIO, SupportedDriverType

logger = logging.getLogger(__name__)


class StreamConnection(abc.ABC):
    """The thin bidi-stream lifecycle shared by the topic reader and writer streams.

    It owns the gRPC wrapper, performs ``connect`` = open call + init handshake, runs the
    update-token loop, and is constructed SYNCHRONOUSLY (no network in ``__init__``). The
    latter is what makes the reconnector's single-stream / no-zombie guarantee structural:
    the connection object exists and owns its gRPC stream before the first cancellable
    network await, so the reconnector can always close it on cancel.

    Subclasses add their protocol-specific message handling and implement the hooks below.
    """

    def __init__(
        self,
        *,
        from_proto: Callable[[Any], Any],
        stub: Any,
        method: Any,
        update_token_interval: Optional[Union[int, float]] = None,
        get_token_function: Optional[Callable[[], Union[str, Awaitable[str]]]] = None,
    ):
        self._loop = asyncio.get_running_loop()
        self._stub = stub
        self._method = method
        # Built (not started) here so the connection owns its transport before connect()'s first
        # network await — that is what makes the no-zombie guarantee structural. The legacy
        # _start(stream, ...) injection path overrides this with an externally provided stream.
        self._stream: IGrpcWrapperAsyncIO = GrpcWrapperAsyncIO(from_proto)
        self._background_tasks: Set[asyncio.Task] = set()
        self._closed = False
        self._first_error: asyncio.Future = self._loop.create_future()
        self._update_token_interval = update_token_interval
        self._get_token_function = get_token_function
        self._update_token_event = asyncio.Event()

    async def connect(self, driver: SupportedDriverType) -> None:
        """Open the gRPC call and run the init handshake on the already-owned stream."""
        await self._stream.start(driver, self._stub, self._method)  # type: ignore[attr-defined]
        await self._init_and_spawn()

    # ------------------------------------------------------------------ death signal

    def _set_first_error(self, err: BaseException) -> None:
        """Record the first error that ended this connection; later errors are ignored."""
        if self._first_error.done():
            return
        self._first_error.set_result(err)
        self._on_first_error()

    def _get_first_error(self) -> Optional[BaseException]:
        return self._first_error.result() if self._first_error.done() else None

    async def wait_error(self) -> None:
        """Block until this connection fails, then raise that error (the reconnect signal)."""
        raise await self._first_error

    def _on_first_error(self) -> None:
        """Hook: wake local subscribers (e.g. the reader's wait_messages). Default: nothing."""

    # ------------------------------------------------------------------ shared update-token loop

    async def _update_token_loop(self) -> None:
        if self._update_token_interval is None:
            return  # nothing to refresh on a cadence; avoids a hot loop
        while True:
            await asyncio.sleep(self._update_token_interval)
            if self._get_token_function is None:
                return
            token = self._get_token_function()
            if not isinstance(token, str):
                token = await token  # async token providers are supported
            await self._update_token(token)

    async def _update_token(self, token: str) -> None:
        await self._update_token_event.wait()
        try:
            if self._stream is not None:
                self._stream.write(self._make_update_token_request(token))
        finally:
            self._update_token_event.clear()

    # ------------------------------------------------------------------ hooks

    @abc.abstractmethod
    async def _init_and_spawn(self, init_message: Any = None) -> None:
        """Send the init request on ``self._stream``, validate the response, and spawn the
        protocol's background workers. ``init_message`` is supplied by the legacy ``_start``
        injection path; when ``None`` (the ``connect`` path) the subclass derives it itself."""

    @abc.abstractmethod
    def _make_update_token_request(self, token: str) -> Any:
        """Wrap ``token`` in the protocol's FromClient(UpdateTokenRequest) message."""
