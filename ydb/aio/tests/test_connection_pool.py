import asyncio

from driver import Driver
from connection import Connection
import pytest
import ydb


@pytest.mark.asyncio
async def test_async_call(endpoint, database):
    driver_config = ydb.DriverConfig(
        endpoint, database, credentials=ydb.construct_credentials_from_environ(),
        root_certificates=ydb.load_ydb_root_certificate(),
    )

    driver = Driver(driver_config=driver_config)

    await driver.scheme_client.make_directory("/local/lol")


@pytest.mark.asyncio
async def test_disconnect_by_call(endpoint, database):
    driver_config = ydb.DriverConfig(
        endpoint, database, credentials=ydb.construct_credentials_from_environ(),
        root_certificates=ydb.load_ydb_root_certificate(),
    )

    driver = Driver(driver_config=driver_config)

    await driver.wait(timeout=10)

    import subprocess
    subprocess.run(["docker-compose", "restart"])

    try:
        await driver.scheme_client.make_directory("/local/lol")
    except Exception as e:
        pass
    await asyncio.sleep(5)
    assert len(driver._store.connections) == 0
