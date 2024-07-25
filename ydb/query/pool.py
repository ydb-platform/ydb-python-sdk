from typing import Callable

from . import base
from .session import (
    QuerySessionSync,
)
from ..retries import (
    RetrySettings,
    retry_operation_sync,
)


class QuerySessionPool:
    """QuerySessionPool is an object to simplify operations with sessions of Query Service."""

    def __init__(self, driver: base.SupportedDriverType):
        """
        :param driver: A driver instance
        """

        self._driver = driver

    def checkout(self):
        """Return a Session context manager, that opens session on enter and closes session on exit."""

        return SimpleQuerySessionCheckout(self)

    def retry_operation_sync(self, callee: Callable, retry_settings: RetrySettings = None, *args, **kwargs):
        """Special interface to execute a bunch of commands with session in a safe, retriable way.

        :param callee: A function, that works with session.
        :param retry_settings: RetrySettings object.

        :return: Result sets or exception in case of execution errors.
        """

        retry_settings = RetrySettings() if retry_settings is None else retry_settings

        def wrapped_callee():
            with self.checkout() as session:
                return callee(session, *args, **kwargs)

        return retry_operation_sync(wrapped_callee, retry_settings)

    def execute_with_retries(self, query: str, retry_settings: RetrySettings = None, *args, **kwargs):
        """Special interface to execute a one-shot queries in a safe, retriable way.

        :param query: A query, yql or sql text.
        :param retry_settings: RetrySettings object.

        :return: Result sets or exception in case of execution errors.
        """

        retry_settings = RetrySettings() if retry_settings is None else retry_settings
        with self.checkout() as session:

            def wrapped_callee():
                it = session.execute(query, empty_tx_control=True, *args, **kwargs)
                return [result_set for result_set in it]

            return retry_operation_sync(wrapped_callee, retry_settings)


class SimpleQuerySessionCheckout:
    def __init__(self, pool: QuerySessionPool):
        self._pool = pool
        self._session = QuerySessionSync(pool._driver)

    def __enter__(self):
        self._session.create()
        return self._session

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._session.delete()
