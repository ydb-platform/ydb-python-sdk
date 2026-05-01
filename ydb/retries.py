import asyncio
import functools
import inspect
import random
import time
from typing import Any, Awaitable, Callable, Generator, Optional, Union

from . import issues
from ._errors import check_retriable_error
from .opentelemetry.tracing import _registry as _tracing_registry


_RUN_WITH_RETRY_SPAN = "ydb.RunWithRetry"
_TRY_SPAN = "ydb.Try"
_BACKOFF_ATTR = "ydb.retry.backoff_ms"


def _start_run_with_retry_span():
    return _tracing_registry.create_span(_RUN_WITH_RETRY_SPAN, kind="internal")


def _start_try_span(backoff_ms: Optional[int]):
    # ``backoff_ms is None`` for the first attempt — the attribute is omitted because
    # there was no preceding sleep at all. For every subsequent attempt the attribute
    # is set, including ``0`` on the skip-yield retry path (Aborted/BadSession/...).
    attrs = {_BACKOFF_ATTR: backoff_ms} if backoff_ms is not None else None
    return _tracing_registry.create_span(_TRY_SPAN, attributes=attrs, kind="internal")


class BackoffSettings:
    def __init__(
        self,
        ceiling: int = 6,
        slot_duration: float = 0.001,
        uncertain_ratio: float = 0.5,
    ) -> None:
        self.ceiling = ceiling
        self.slot_duration = slot_duration
        self.uncertain_ratio = uncertain_ratio

    def calc_backoff_ms(self, retry_number: int) -> int:
        slots_count = 1 << min(retry_number, self.ceiling)
        max_duration_ms = slots_count * self.slot_duration * 1000.0
        # duration_ms = random.random() * max_duration_ms * uncertain_ratio + max_duration_ms * (1 - uncertain_ratio)
        duration_ms = max_duration_ms * (random.random() * self.uncertain_ratio + 1.0 - self.uncertain_ratio)
        return int(duration_ms)

    def calc_timeout(self, retry_number: int) -> float:
        """Backward-compatible alias returning seconds."""
        return self.calc_backoff_ms(retry_number) / 1000.0


class RetrySettings:
    def __init__(
        self,
        max_retries: int = 10,
        max_session_acquire_timeout: Optional[float] = None,
        on_ydb_error_callback: Optional[Callable[[issues.Error], None]] = None,
        backoff_ceiling: int = 6,
        backoff_slot_duration: float = 1,
        get_session_client_timeout: float = 5,
        fast_backoff_settings: Optional[BackoffSettings] = None,
        slow_backoff_settings: Optional[BackoffSettings] = None,
        idempotent: bool = False,
        retry_cancelled: bool = False,
    ) -> None:
        self.max_retries = max_retries
        self.max_session_acquire_timeout = max_session_acquire_timeout
        self.on_ydb_error_callback: Callable[[issues.Error], None] = (
            (lambda e: None) if on_ydb_error_callback is None else on_ydb_error_callback
        )
        self.fast_backoff = BackoffSettings(10, 0.005) if fast_backoff_settings is None else fast_backoff_settings
        self.slow_backoff = (
            BackoffSettings(backoff_ceiling, backoff_slot_duration)
            if slow_backoff_settings is None
            else slow_backoff_settings
        )
        self.retry_not_found = True
        self.idempotent = idempotent
        self.retry_internal_error = True
        self.retry_cancelled = retry_cancelled
        self.unknown_error_handler: Callable[[Exception], None] = lambda e: None
        self.get_session_client_timeout: float = get_session_client_timeout
        if max_session_acquire_timeout is not None:
            self.get_session_client_timeout = min(max_session_acquire_timeout, self.get_session_client_timeout)

    def with_fast_backoff(self, backoff_settings: BackoffSettings) -> "RetrySettings":
        self.fast_backoff = backoff_settings
        return self

    def with_slow_backoff(self, backoff_settings: BackoffSettings) -> "RetrySettings":
        self.slow_backoff = backoff_settings
        return self


class YdbRetryOperationSleepOpt:
    """Yielded by :func:`retry_operation_impl` between attempts.

    ``timeout`` is the wait in seconds (``time.sleep`` / ``asyncio.sleep``); for the
    "skip yield" YDB error path (``Aborted``/``BadSession``/``NotFound``/``InternalError``)
    it is ``0.0`` and ``exception`` is set so consumers still emit one artefact per
    attempt (e.g. a ``ydb.Try`` span). ``backoff_ms`` exposes the same value as integer
    milliseconds for OpenTelemetry attributes.
    """

    def __init__(self, timeout: float, exception: Optional[BaseException] = None) -> None:
        self.timeout = timeout
        self.exception = exception

    @property
    def backoff_ms(self) -> int:
        return int(self.timeout * 1000)

    def __eq__(self, other: object) -> bool:
        return (
            type(self) is type(other) and isinstance(other, YdbRetryOperationSleepOpt) and self.timeout == other.timeout
        )

    def __repr__(self) -> str:
        return "YdbRetryOperationSleepOpt(%s)" % self.timeout


class YdbRetryOperationFinalResult:
    def __init__(self, result: Any) -> None:
        self.result = result
        self.exc: Optional[BaseException] = None

    def __eq__(self, other: object) -> bool:
        return (
            type(self) is type(other)
            and isinstance(other, YdbRetryOperationFinalResult)
            and self.result == other.result
            and self.exc == other.exc
        )

    def __repr__(self) -> str:
        return "YdbRetryOperationFinalResult(%s, exc=%s)" % (self.result, self.exc)

    def set_exception(self, exc: BaseException) -> None:
        self.exc = exc


def retry_operation_impl(
    callee: Callable[..., Any],
    retry_settings: Optional[RetrySettings] = None,
    *args: Any,
    **kwargs: Any,
) -> Generator[Union[YdbRetryOperationSleepOpt, YdbRetryOperationFinalResult], None, None]:
    """Pure retry-policy generator.

    Yields ``YdbRetryOperationFinalResult`` (callee's return value, or coroutine for an
    async callee) and, between attempts, ``YdbRetryOperationSleepOpt`` carrying the wait
    time in seconds plus the original exception. OpenTelemetry spans are created by the
    callers (``retry_operation_sync`` / ``retry_operation_async``), not here, so the
    generator stays unaware of tracing.
    """
    retry_settings = RetrySettings() if retry_settings is None else retry_settings
    status: Optional[issues.Error] = None

    for attempt in range(retry_settings.max_retries + 1):
        try:
            result = YdbRetryOperationFinalResult(callee(*args, **kwargs))
            yield result

            if result.exc is not None:
                raise result.exc

        except issues.Error as e:
            status = e
            retry_settings.on_ydb_error_callback(e)

            retriable_info = check_retriable_error(e, retry_settings, attempt)
            if not retriable_info.is_retriable:
                raise

            skip_yield_error_types = (
                issues.Aborted,
                issues.BadSession,
                issues.NotFound,
                issues.InternalError,
            )

            if isinstance(e, skip_yield_error_types):
                # Fast retry path: no inter-attempt sleep, but we still yield a marker
                # SleepOpt(0.0) so consumers (e.g. the sync wrapper) advance per-attempt
                # bookkeeping such as ``ydb.Try`` spans.
                yield YdbRetryOperationSleepOpt(0.0, exception=e)
            else:
                sleep_seconds = retriable_info.sleep_timeout_seconds or 0.0
                yield YdbRetryOperationSleepOpt(sleep_seconds, exception=e)

        except Exception as e:
            retry_settings.unknown_error_handler(e)
            raise

    if status is not None:
        raise status


def retry_operation_sync(
    callee: Callable[..., Any],
    retry_settings: Optional[RetrySettings] = None,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """Drive :func:`retry_operation_impl` synchronously with OpenTelemetry spans.

    ``ydb.RunWithRetry`` is the outer ``INTERNAL`` span; each attempt runs inside a
    ``ydb.Try`` whose ``ydb.retry.backoff_ms`` is the wait that preceded it. The first
    ``ydb.Try`` has no such wait so the attribute is omitted; subsequent attempts
    always carry it (``0`` on the skip-yield retry path). RPC spans
    (``ydb.ExecuteQuery``/``ydb.Commit``/``ydb.Rollback``) nest under the active
    ``ydb.Try`` because the sync callee runs while ``TracingSpan.__enter__`` has the
    OTel context attached.
    """
    backoff_ms: Optional[int] = None

    if inspect.iscoroutinefunction(callee):
        # Async callee with a sync driver: keep current legacy behaviour — the impl just
        # creates the coroutine, the caller is responsible for awaiting it. No ``ydb.Try``
        # is opened around the bare coroutine creation; tracing for that case lives in
        # ``retry_operation_async``.
        traced_callee: Callable[..., Any] = callee
    else:

        @functools.wraps(callee)
        def traced_callee(*a: Any, **kw: Any) -> Any:
            with _start_try_span(backoff_ms):
                return callee(*a, **kw)

    with _start_run_with_retry_span():
        for next_opt in retry_operation_impl(traced_callee, retry_settings, *args, **kwargs):
            if isinstance(next_opt, YdbRetryOperationSleepOpt):
                backoff_ms = next_opt.backoff_ms
                if next_opt.timeout > 0:
                    time.sleep(next_opt.timeout)
            else:
                return next_opt.result
    return None


async def retry_operation_async(  # pylint: disable=W1113
    callee: Callable[..., Any],
    retry_settings: Optional[RetrySettings] = None,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """Drive :func:`retry_operation_impl` asynchronously with OpenTelemetry spans.

    Mirrors :func:`retry_operation_sync`. The inter-attempt ``await asyncio.sleep`` runs
    *outside* ``ydb.Try`` so an `asyncio.CancelledError` during the wait is recorded on
    ``ydb.RunWithRetry`` (the outer span), not on a misleading per-attempt span.
    """
    backoff_ms: Optional[int] = None
    with _start_run_with_retry_span():
        for next_opt in retry_operation_impl(callee, retry_settings, *args, **kwargs):
            if isinstance(next_opt, YdbRetryOperationSleepOpt):
                backoff_ms = next_opt.backoff_ms
                if next_opt.timeout > 0:
                    await asyncio.sleep(next_opt.timeout)
            else:
                with _start_try_span(backoff_ms) as try_span:
                    awaitable: Awaitable[Any] = next_opt.result
                    try:
                        return await awaitable
                    except BaseException as e:  # noqa: BLE001
                        # Exception is swallowed by ``next_opt.set_exception`` so the
                        # impl re-raises it on the next ``next()`` call; the ``with``
                        # would not see it via ``__exit__``, so mark ``ydb.Try`` failed
                        # explicitly.
                        try_span.set_error(e)
                        next_opt.set_exception(e)
    return None


def ydb_retry(
    max_retries: int = 10,
    max_session_acquire_timeout: Optional[float] = None,
    on_ydb_error_callback: Optional[Callable[[issues.Error], None]] = None,
    backoff_ceiling: int = 6,
    backoff_slot_duration: float = 1,
    get_session_client_timeout: float = 5,
    fast_backoff_settings: Optional[BackoffSettings] = None,
    slow_backoff_settings: Optional[BackoffSettings] = None,
    idempotent: bool = False,
    retry_cancelled: bool = False,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator for automatic function retry in case of YDB errors.

    Supports both synchronous and asynchronous functions.

    :param max_retries: Maximum number of retries (default: 10)
    :param max_session_acquire_timeout: Maximum session acquisition timeout (default: None)
    :param on_ydb_error_callback: Callback for handling YDB errors (default: None)
    :param backoff_ceiling: Ceiling for backoff algorithm (default: 6)
    :param backoff_slot_duration: Slot duration for backoff (default: 1)
    :param get_session_client_timeout: Session client timeout (default: 5)
    :param fast_backoff_settings: Fast backoff settings (default: None)
    :param slow_backoff_settings: Slow backoff settings (default: None)
    :param idempotent: Whether the operation is idempotent (default: False)
    :param retry_cancelled: Whether to retry cancelled operations (default: False)
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        retry_settings = RetrySettings(
            max_retries=max_retries,
            max_session_acquire_timeout=max_session_acquire_timeout,
            on_ydb_error_callback=on_ydb_error_callback,
            backoff_ceiling=backoff_ceiling,
            backoff_slot_duration=backoff_slot_duration,
            get_session_client_timeout=get_session_client_timeout,
            fast_backoff_settings=fast_backoff_settings,
            slow_backoff_settings=slow_backoff_settings,
            idempotent=idempotent,
            retry_cancelled=retry_cancelled,
        )

        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                return await retry_operation_async(func, retry_settings, *args, **kwargs)

            return async_wrapper

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            return retry_operation_sync(func, retry_settings, *args, **kwargs)

        return sync_wrapper

    return decorator
