import os

import ydb
import asyncio


async def retry_operation(callee, retry_settings=None, *args, **kwargs):
    opt_generator = ydb.retry_operation_impl(callee, retry_settings, *args, **kwargs)
    for next_opt in opt_generator:
        if isinstance(next_opt, ydb.YdbRetryOperationSleepOpt):
            await asyncio.sleep(next_opt.timeout)
        else:
            return await next_opt.result


async def execute_query(pool):
    with pool.async_checkout() as session_holder:
        try:
            session = await asyncio.wait_for(asyncio.wrap_future(session_holder), timeout=5)
        except asyncio.TimeoutError:
            raise ydb.SessionPoolEmpty()

        return await asyncio.wrap_future(
            session.transaction().async_execute(
                'select 1 as cnt;',
                commit_tx=True,
                settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2)
            )
        )


async def main():
    driver_config = ydb.DriverConfig(
        endpoint=os.getenv('YDB_ENDPOINT'),
        database=os.getenv('YDB_DATABASE'),
        credentials=ydb.construct_credentials_from_environ(),
        root_certificates=ydb.load_ydb_root_certificate(),
    )

    with ydb.Driver(driver_config) as driver:
        try:
            await asyncio.wait_for(asyncio.wrap_future(driver.async_wait()), timeout=5)
        except asyncio.TimeoutError:
            # error connecting to ydb, print some internal details about connect
            print('ydb connect failed, %s', driver.discovery_debug_details())
            raise

        session_pool = ydb.SessionPool(driver)
        result = await retry_operation(execute_query, None, session_pool)
        assert result[0].rows[0].cnt == 1


asyncio.run(main())
