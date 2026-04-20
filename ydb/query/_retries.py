"""Retry wrappers that emit OpenTelemetry spans around the query-service retry loop.

``ydb.RunWithRetry`` is the umbrella INTERNAL span, and each attempt is wrapped in
a ``ydb.Try`` INTERNAL span with the ``ydb.retry.backoff_ms`` attribute capturing
the sleep that preceded it. When the retry fails, the offending exception is
recorded on the ``ydb.Try`` span; when it propagates out, it is also recorded on
the outer ``ydb.RunWithRetry`` span via the context-manager protocol.
"""
import asyncio
import time
from typing import Any, Callable, Optional

from ..opentelemetry.tracing import _registry
from ..retries import RetrySettings, YdbRetryOperationSleepOpt, retry_operation_impl


_RUN_WITH_RETRY = "ydb.RunWithRetry"
_TRY = "ydb.Try"
_BACKOFF_ATTR = "ydb.retry.backoff_ms"


def _start_try_span(backoff_ms: int):
    return _registry.create_span(_TRY, attributes={_BACKOFF_ATTR: backoff_ms}, kind="internal")


def retry_operation_sync(
    callee: Callable[..., Any],
    retry_settings: Optional[RetrySettings] = None,
    *args: Any,
    **kwargs: Any,
) -> Any:
    with _registry.create_span(_RUN_WITH_RETRY, kind="internal"):
        opt_generator = retry_operation_impl(callee, retry_settings, *args, **kwargs)
        try_span = _start_try_span(0)
        try:
            for next_opt in opt_generator:
                if isinstance(next_opt, YdbRetryOperationSleepOpt):
                    exc = getattr(next_opt, "exception", None)
                    if exc is not None:
                        try_span.set_error(exc)
                    try_span.end()
                    try_span = None
                    backoff_ms = int(next_opt.timeout * 1000)
                    try_span = _start_try_span(backoff_ms)
                    time.sleep(next_opt.timeout)
                else:
                    try_span.end()
                    try_span = None
                    return next_opt.result
        except BaseException as e:
            if try_span is not None:
                try_span.set_error(e)
                try_span.end()
                try_span = None
            raise
        if try_span is not None:
            try_span.end()
    return None


async def retry_operation_async(
    callee: Callable[..., Any],
    retry_settings: Optional[RetrySettings] = None,
    *args: Any,
    **kwargs: Any,
) -> Any:
    with _registry.create_span(_RUN_WITH_RETRY, kind="internal"):
        opt_generator = retry_operation_impl(callee, retry_settings, *args, **kwargs)
        try_span = _start_try_span(0)
        try:
            for next_opt in opt_generator:
                if isinstance(next_opt, YdbRetryOperationSleepOpt):
                    exc = getattr(next_opt, "exception", None)
                    if exc is not None:
                        try_span.set_error(exc)
                    try_span.end()
                    try_span = None
                    backoff_ms = int(next_opt.timeout * 1000)
                    try_span = _start_try_span(backoff_ms)
                    await asyncio.sleep(next_opt.timeout)
                else:
                    try:
                        result = await next_opt.result
                        try_span.end()
                        try_span = None
                        return result
                    except BaseException as e:  # pylint: disable=W0703
                        next_opt.set_exception(e)
        except BaseException as e:
            if try_span is not None:
                try_span.set_error(e)
                try_span.end()
                try_span = None
            raise
        if try_span is not None:
            try_span.end()
    return None
