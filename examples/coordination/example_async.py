import asyncio

import ydb

NODE_PATH = "/local/node_name1"
SEMAPHORE_NAME = "semaphore"


async def linear_workload(client, text):
    session = client.session(NODE_PATH)
    semaphore = session.semaphore(SEMAPHORE_NAME)
    for i in range(3):
        await semaphore.acquire()
        for j in range(3):
            print(f"{text} iteration {i}-{j}")
            await asyncio.sleep(0.1)
        await semaphore.release()
        await asyncio.sleep(0.05)
    await session.close()


async def context_manager_workload(client, text):
    async with client.session(NODE_PATH) as session:
        for i in range(3):
            async with session.semaphore(SEMAPHORE_NAME):
                for j in range(3):
                    print(f"{text} iteration {i}-{j}")
                    await asyncio.sleep(0.1)
            await asyncio.sleep(0.05)


async def run(endpoint, database):
    async with ydb.aio.Driver(
        endpoint=endpoint,
        database=database,
        credentials=ydb.credentials_from_env_variables(),
        root_certificates=ydb.load_ydb_root_certificate(),
    ) as driver:
        await driver.wait(timeout=5, fail_fast=True)

        await driver.coordination_client.create_node(NODE_PATH)

        await asyncio.gather(
            linear_workload(driver.coordination_client, "worker 1"),
            linear_workload(driver.coordination_client, "worker 2"),
            context_manager_workload(driver.coordination_client, "worker 3"),
            context_manager_workload(driver.coordination_client, "worker 4"),
        )
