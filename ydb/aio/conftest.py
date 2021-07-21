import os
import pytest

pytest_plugins = ["docker_compose"]


@pytest.fixture(scope="module")
def docker_compose_file(pytestconfig):
    return os.path.join(str(pytestconfig.rootdir), "docker-compose.yml")


@pytest.fixture(scope="session")
def endpoint(session_scoped_container_getter):
    service = session_scoped_container_getter.get("ydb").network_info[0]
    return service.hostname + ":" + service.host_port


@pytest.fixture(scope="module")
def database():
    return "local"


@pytest.fixture()
async def aio_connection(endpoint, database):
    """A fixture to wait ydb start"""
    from connection import Connection
    from kikimr.public.sdk.python.client.driver import DriverConfig
    config = DriverConfig.default_from_endpoint_and_database(endpoint, database)
    connection = Connection(endpoint, config)
    await connection.connection_ready(ready_timeout=7)
    return connection
