import time
from typing import Callable

from . import base
from .session import (
    QuerySessionSync,
)
from .. import issues
from .._errors import check_retriable_error


class RetrySettings(object):
    def __init__(
        self,
        max_retries: int = 10,
        max_session_acquire_timeout: int = None,
        on_ydb_error_callback: Callable = None,
        idempotent: bool = False,
    ):
        self.max_retries = max_retries
        self.max_session_acquire_timeout = max_session_acquire_timeout
        self.on_ydb_error_callback = (lambda e: None) if on_ydb_error_callback is None else on_ydb_error_callback
        self.retry_not_found = True
        self.idempotent = idempotent
        self.retry_internal_error = True
        self.unknown_error_handler = lambda e: None


class YdbRetryOperationSleepOpt:
    def __init__(self, timeout):
        self.timeout = timeout

    def __eq__(self, other):
        return type(self) == type(other) and self.timeout == other.timeout

    def __repr__(self):
        return "YdbRetryOperationSleepOpt(%s)" % self.timeout


class YdbRetryOperationFinalResult:
    def __init__(self, result):
        self.result = result
        self.exc = None

    def __eq__(self, other):
        return type(self) == type(other) and self.result == other.result and self.exc == other.exc

    def __repr__(self):
        return "YdbRetryOperationFinalResult(%s, exc=%s)" % (self.result, self.exc)

    def set_exception(self, exc):
        self.exc = exc


def retry_operation_impl(callee: Callable, retry_settings: RetrySettings = None, *args, **kwargs):
    retry_settings = RetrySettings() if retry_settings is None else retry_settings
    status = None

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

            skip_yield_error_types = [
                issues.Aborted,
                issues.BadSession,
                issues.NotFound,
                issues.InternalError,
            ]

            yield_sleep = True
            for t in skip_yield_error_types:
                if isinstance(e, t):
                    yield_sleep = False

            if yield_sleep:
                yield YdbRetryOperationSleepOpt(retriable_info.sleep_timeout_seconds)

        except Exception as e:
            # you should provide your own handler you want
            retry_settings.unknown_error_handler(e)
            raise
    if status:
        raise status


class QuerySessionPool:
    def __init__(self, driver: base.SupportedDriverType):
        self._driver = driver

    def checkout(self):
        return SimpleQuerySessionCheckout(self)

    def retry_operation_sync(self, callee: Callable, retry_settings: RetrySettings = None, *args, **kwargs):
        retry_settings = RetrySettings() if retry_settings is None else retry_settings

        def wrapped_callee():
            with self.checkout() as session:
                return callee(session, *args, **kwargs)

        opt_generator = retry_operation_impl(wrapped_callee, retry_settings, *args, **kwargs)
        for next_opt in opt_generator:
            if isinstance(next_opt, YdbRetryOperationSleepOpt):
                time.sleep(next_opt.timeout)
            else:
                return next_opt.result

    def execute_with_retries(self, query: str, ddl: bool = False, retry_settings: RetrySettings = None, *args, **kwargs):
        retry_settings = RetrySettings() if retry_settings is None else retry_settings
        with self.checkout() as session:
            def wrapped_callee():
                it = session.execute(query, empty_tx_control=ddl)
                return [result_set for result_set in it]

            opt_generator = retry_operation_impl(wrapped_callee, retry_settings, *args, **kwargs)
            for next_opt in opt_generator:
                if isinstance(next_opt, YdbRetryOperationSleepOpt):
                    time.sleep(next_opt.timeout)
                else:
                    return next_opt.result


class SimpleQuerySessionCheckout:
    def __init__(self, pool: QuerySessionPool):
        self._pool = pool
        self._session = QuerySessionSync(pool._driver)

    def __enter__(self):
        self._session.create()
        return self._session

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._session.delete()
