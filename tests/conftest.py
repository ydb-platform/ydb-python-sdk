import os

import pytest
import ydb
import time
from ydb import issues


@pytest.fixture(scope="module")
def docker_compose_file(pytestconfig):
    return os.path.join(str(pytestconfig.rootdir), "docker-compose.yml")


def wait_container_ready(driver):
    driver.wait(timeout=30)

    with ydb.SessionPool(driver) as pool:

        started_at = time.time()
        while time.time() - started_at < 30:
            try:
                with pool.checkout() as session:
                    session.execute_scheme("create table `.sys_health/test_table` (A int32, primary key(A));")

                return True

            except ydb.Error:
                time.sleep(1)

    raise RuntimeError("Container is not ready after timeout.")


@pytest.fixture(scope="module")
def endpoint(pytestconfig, module_scoped_container_getter):
    with ydb.Driver(endpoint="localhost:2136", database="/local") as driver:
        wait_container_ready(driver)
    yield "localhost:2136"


@pytest.fixture(scope="session")
def secure_endpoint(pytestconfig, session_scoped_container_getter):
    ca_path = os.path.join(str(pytestconfig.rootdir), "ydb_certs/ca.pem")
    iterations = 0
    while not os.path.exists(ca_path) and iterations < 10:
        time.sleep(1)
        iterations += 1

    assert os.path.exists(ca_path)
    os.environ["YDB_SSL_ROOT_CERTIFICATES_FILE"] = ca_path
    with ydb.Driver(
        endpoint="grpcs://localhost:2135",
        database="/local",
        root_certificates=ydb.load_ydb_root_certificate(),
    ) as driver:
        wait_container_ready(driver)
    yield "localhost:2135"


@pytest.fixture(scope="module")
def database():
    return "/local"


@pytest.fixture()
async def aio_connection(endpoint, database):
    """A fixture to wait ydb start"""
    from ydb.aio.connection import Connection
    from ydb.driver import DriverConfig

    config = DriverConfig.default_from_endpoint_and_database(endpoint, database)
    connection = Connection(endpoint, config)
    await connection.connection_ready(ready_timeout=7)
    return connection


@pytest.fixture()
async def driver(endpoint, database, event_loop):
    driver_config = ydb.DriverConfig(
        endpoint,
        database,
    )

    driver = ydb.aio.Driver(driver_config=driver_config)
    await driver.wait(timeout=15)

    yield driver

    await driver.stop(timeout=10)


@pytest.fixture()
async def driver_sync(endpoint, database, event_loop):
    driver_config = ydb.DriverConfig(
        endpoint,
        database,
    )

    driver = ydb.Driver(driver_config=driver_config)
    driver.wait(timeout=15)

    yield driver

    driver.stop(timeout=10)


@pytest.fixture()
def table_name(driver_sync, database):
    table_name = "table"

    with ydb.SessionPool(driver_sync) as pool:

        def create_table(s):
            try:
                s.drop_table(database + "/" + table_name)
            except ydb.SchemeError:
                pass

            s.execute_scheme(
                """
CREATE TABLE %s (
id Int64 NOT NULL,
i64Val Int64,
PRIMARY KEY(id)
)
"""
                % table_name
            )

        pool.retry_operation_sync(create_table)
    return table_name


@pytest.fixture()
def table_path(database, table_name) -> str:
    return database + "/" + table_name


@pytest.fixture()
def topic_consumer():
    return "fixture-consumer"


@pytest.fixture()
@pytest.mark.asyncio()
async def topic_path(driver, topic_consumer, database) -> str:
    topic_path = database + "/test-topic"

    try:
        await driver.topic_client.drop_topic(topic_path)
    except issues.SchemeError:
        pass

    await driver.topic_client.create_topic(
        path=topic_path,
        consumers=[topic_consumer],
    )

    return topic_path


@pytest.fixture()
@pytest.mark.asyncio()
async def topic2_path(driver, topic_consumer, database) -> str:
    topic_path = database + "/test-topic2"

    try:
        await driver.topic_client.drop_topic(topic_path)
    except issues.SchemeError:
        pass

    await driver.topic_client.create_topic(
        path=topic_path,
        consumers=[topic_consumer],
    )

    return topic_path


@pytest.fixture()
@pytest.mark.asyncio()
async def topic_with_messages(driver, topic_consumer, database):
    topic_path = database + "/test-topic-with-messages"
    try:
        await driver.topic_client.drop_topic(topic_path)
    except issues.SchemeError:
        pass

    await driver.topic_client.create_topic(
        path=topic_path,
        consumers=[topic_consumer],
    )

    writer = driver.topic_client.writer(topic_path, producer_id="fixture-producer-id", codec=ydb.TopicCodec.RAW)
    await writer.write_with_ack(
        [
            ydb.TopicWriterMessage(data="123".encode()),
            ydb.TopicWriterMessage(data="456".encode()),
        ]
    )
    await writer.write_with_ack(
        [
            ydb.TopicWriterMessage(data="789".encode()),
            ydb.TopicWriterMessage(data="0".encode()),
        ]
    )
    await writer.close()
    return topic_path


@pytest.fixture()
@pytest.mark.asyncio()
async def topic_reader(driver, topic_consumer, topic_path) -> ydb.TopicReaderAsyncIO:
    reader = driver.topic_client.reader(topic=topic_path, consumer=topic_consumer)
    yield reader
    await reader.close()


@pytest.fixture()
def topic_reader_sync(driver_sync, topic_consumer, topic_path) -> ydb.TopicReader:
    reader = driver_sync.topic_client.reader(topic=topic_path, consumer=topic_consumer)
    yield reader
    reader.close()
