# -*- coding: utf-8 -*-
import tornado.concurrent
import tornado.ioloop
import tornado.gen
from tornado.concurrent import TracebackFuture
from kikimr.public.sdk.python.client.table import RetrySettings, calc_backoff_timeout, SessionPoolEmpty
from kikimr.public.sdk.python.client import issues
import six.moves


def as_tornado_future(foreign_future, timeout=None):
    """
    Return tornado.concurrent.Future wrapped python concurrent.future (foreign_future).
    Cancel execution original future after given timeout
    """
    result_future = tornado.concurrent.Future()
    timeout_timer = None
    if timeout:

        def on_timeout():
            timeout_timer.clear()
            foreign_future.cancel()

        timeout_timer.append(
            tornado.ioloop.IOLoop.current().call_later(
                timeout, on_timeout
            )
        )

    def copy_to_result_future(foreign_future):
        if timeout_timer is not None:
            tornado.ioloop.IOLoop.current().remove_timeout(
                timeout_timer.pop(
                    0
                )
            )

        if result_future.done():
            return

        if (
                isinstance(foreign_future, TracebackFuture)
                and isinstance(result_future, TracebackFuture)
                and result_future.exc_info() is not None
        ):
            result_future.set_exc_info(foreign_future.exc_info())
        elif foreign_future.cancelled():
            result_future.set_exception(tornado.gen.TimeoutError())
        elif foreign_future.exception() is not None:
            result_future.set_exception(foreign_future.exception())
        else:
            result_future.set_result(foreign_future.result())

    tornado.ioloop.IOLoop.current().add_future(foreign_future, copy_to_result_future)
    return result_future


async def retry_operation(callee, retry_settings=None, *args, **kwargs):

    retry_settings = RetrySettings() if retry_settings is None else retry_settings
    status = None

    for attempt in six.moves.range(retry_settings.max_retries + 1):
        try:
            return await callee(*args, **kwargs)
        except (
                issues.Unavailable, issues.Aborted, issues.BadSession,
                issues.NotFound, issues.InternalError) as e:
            status = e
            retry_settings.on_ydb_error_callback(e)

            if isinstance(e, issues.NotFound) and not retry_settings.retry_not_found:
                raise e

            if isinstance(e, issues.InternalError) and not retry_settings.retry_internal_error:
                raise e

        except (issues.Overloaded, SessionPoolEmpty, issues.ConnectionError) as e:
            status = e
            retry_settings.on_ydb_error_callback(e)
            await tornado.gen.sleep(
                calc_backoff_timeout(
                    retry_settings,
                    attempt
                )
            )

        except issues.Error as e:
            retry_settings.on_ydb_error_callback(e)
            raise

        except Exception as e:
            # you should provide your own handler you want
            retry_settings.unknown_error_handler(e)

    raise status
