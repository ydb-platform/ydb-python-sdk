import asyncio
import os
import pytest
import ydb

pytest_plugins = ["docker_compose"]


@pytest.fixture(scope="module")
def docker_compose_file(pytestconfig):
    return os.path.join(str(pytestconfig.rootdir), "docker-compose.yml")


@pytest.fixture(scope="module")
def endpoint(module_scoped_container_getter):
    service = module_scoped_container_getter.get("ydb").network_info[0]
    return service.hostname + ":" + service.host_port


@pytest.fixture(scope="module")
def database():
    return "local"


@pytest.fixture()
async def aio_connection(endpoint, database):
    """A fixture to wait ydb start"""
    from ydb.aio.connection import Connection
    from kikimr.public.sdk.python.client.driver import DriverConfig
    config = DriverConfig.default_from_endpoint_and_database(endpoint, database)
    connection = Connection(endpoint, config)
    await connection.connection_ready(ready_timeout=7)
    return connection


@pytest.fixture()
async def driver(endpoint, database, request):
    driver_config = ydb.DriverConfig(
        endpoint, database, credentials=ydb.construct_credentials_from_environ(),
        root_certificates=ydb.load_ydb_root_certificate(),
    )

    driver = ydb.aio.Driver(driver_config=driver_config)
    await driver.wait(timeout=15)

    def teardown():
        asyncio.get_event_loop().run_until_complete(driver.stop())

    request.addfinalizer(teardown)

    return driver

