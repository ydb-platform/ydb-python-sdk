import asyncio
import ydb
from ydb.aio.coordination import CoordinationClient


async def main():
    driver_config = ydb.DriverConfig(
        endpoint="grpc://localhost:2136",
        database="/local",
        # credentials=ydb.credentials_from_env_variables(),
        # root_certificates=ydb.load_ydb_root_certificate(),
    )
    try:
        driver = ydb.aio.Driver(driver_config)
        await driver.wait()
    except TimeoutError:
        raise RuntimeError("Connect failed to YDB")

    await asyncio.gather(
        some_workload(driver, "worker 1"),
        some_workload(driver, "worker 2"),
        # some_workload(driver, "worker 3"),
        # some_workload(driver, "worker 4"),
    )

    await driver.stop()


async def some_workload(driver, text):
    client = CoordinationClient(driver)
    await client.create_node("/local/node1")
    session = client.session("/local/node1")
    semaphore = session.lock("semaphore")
    for i in range(10):
        # print(f"{text} starting iteration {i}")
        await semaphore.acquire()
        for j in range(5):
            if j == 3:
                await session._reconnector._stream.close()
            print(f"{text} {j}")
            await asyncio.sleep(0.01)

        await semaphore.release()
        await asyncio.sleep(0.01)
        # print(f"{text} finished iteration {i}")

    await session.close()


if __name__ == "__main__":
    asyncio.run(main())
