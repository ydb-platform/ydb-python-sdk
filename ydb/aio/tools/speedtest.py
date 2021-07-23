from ydb.aio.driver import Driver as AioDriver
from ydb import Driver as SyncDriver
import ydb

import sys
import asyncio
import time
from concurrent.futures import TimeoutError, ThreadPoolExecutor
from statistics import mean

import argparse


async def make_async_call(driver: AioDriver):
    return await driver.scheme_client.describe_path(path=database)


async def coroutine(driver, limit, it):
    let = 0
    errs = []
    count = 0
    await driver.wait()
    for i in range(limit):
        try:
            start = time.time()
            await asyncio.wait_for(make_async_call(driver), timeout=60)
            if count > 0:
                let = (let * (max(count - 1, 0)) + (time.time() - start)) / count
            count += 1
        except ydb.Error as e:
            errs.append(e)
        except TimeoutError as e:
            errs.append(e)
    print("latency:", let, "errors:", errs, "requests completed:", count)
    return let


def thread(driver, limit, it):

    let = 0
    errs = []

    count = 0
    for i in range(limit):
        try:
            start = time.time()
            driver.wait()
            driver.scheme_client.describe_path(path=database)
            if count > 0:
                let = (let * (max(count - 1, 0)) + (time.time() - start)) / count
            count += 1
        except ydb.Error as e:
            errs.append(e)
        except Exception as e:
            errs.append(e)
    print("latency:", let, "errors:", errs, "requests completed:", count)
    return let


async def async_main(driver, limit, num):
    coroutines = [
        coroutine(driver, limit, i)
        for i in range(num)
    ]
    return mean(await asyncio.gather(*coroutines))


def sync_main(driver, limit, num):
    tasks = []
    with ThreadPoolExecutor(max_workers=num) as e:
        for i in range(num):
            tasks.append(e.submit(thread, driver, limit, i))

    return mean(x.result() for x in tasks)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Test python ydb sdk")
    parser.add_argument("-e", "--endpoint", default="0.0.0.0:2135", help="Ydb endpoint")
    parser.add_argument("-d", "--database", default="local", help="Ydb database")
    parser.add_argument("-t", "--test_type", choices=("sync", "async"), help="Run sync or async sdk")
    parser.add_argument("-l", "--limit", type=int, help="Limit of request on one worker")
    parser.add_argument("-w", "--workers", type=int, help="Number of workers")

    args = parser.parse_args()
    database = args.database
    endpoint = args.endpoint
    limit = args.limit
    test_type = args.test_type
    num = args.workers

    print("""
    endpoint: %s,
    database: %s,
    limit: %s,
    workers number: %s
    """ % (endpoint, database, limit, num))
    limit = int(limit)
    num = int(num)

    config = ydb.DriverConfig(
        endpoint, database, credentials=ydb.construct_credentials_from_environ(),
        root_certificates=ydb.load_ydb_root_certificate(),
    )

    print("running %s test" % test_type)
    let = 0
    start = time.time()
    connections = []
    if test_type == "async":
        async_driver = AioDriver(config)
        loop = asyncio.get_event_loop()
        let = loop.run_until_complete(async_main(async_driver, limit, num))
        connections.extend(async_driver._store.connections)

    if test_type == "sync":
        start = time.time()
        sync_driver = SyncDriver(config)
        sync_driver.wait(5)
        let = sync_main(sync_driver, limit, num)
        connections.extend(sync_driver._store.connections)

    print("Full test complete at " + str(time.time() - start))
    print("Mean latency: %s" % str(let))
    print("Found connections: ", connections)
