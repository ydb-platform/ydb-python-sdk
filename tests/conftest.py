import os
import subprocess

import docker
import pytest
from pytest_docker.plugin import DockerComposeExecutor, Services, containers_scope
import ydb
from ydb import issues

YDB_ENDPOINT_PORT = 2136
YDB_SECURE_ENDPOINT_PORT = 2135


def _docker_client():
    """Build a Docker SDK client that works with non-default sockets.

    `docker.from_env()` only honors `DOCKER_HOST` and a couple of fixed
    paths, so it fails on Colima / OrbStack / Docker Desktop on macOS where
    the socket lives elsewhere. Fall back to whatever the CLI's active
    context says — that's a one-shot subprocess call before any driver is
    running, so the gRPC fork race we worry about elsewhere doesn't apply.
    """
    try:
        return docker.from_env()
    except docker.errors.DockerException:
        pass
    try:
        host = (
            subprocess.check_output(
                ["docker", "context", "inspect", "--format", "{{.Endpoints.docker.Host}}"],
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise RuntimeError(
            "Could not locate the Docker daemon socket. " "Set DOCKER_HOST or make sure `docker context` is configured."
        ) from exc
    return docker.DockerClient(base_url=host)


def pytest_addoption(parser):
    """Add custom command line options for pytest-docker compatibility."""
    parser.addoption(
        "--docker-compose-file",
        action="store",
        default="docker-compose.yml",
        help="Path to docker-compose file (relative to project root)",
    )


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    """Path to docker-compose.yml for pytest-docker."""
    compose_file = pytestconfig.getoption("--docker-compose-file")
    return os.path.join(str(pytestconfig.rootdir), compose_file)


@pytest.fixture(scope="session")
def docker_cleanup():
    """Remove volumes after tests (equivalent to --docker-compose-remove-volumes)."""
    return ["down -v --remove-orphans"]


def _cleanup_docker_project(project_name):
    docker_client = _docker_client()
    project_filter = {"label": f"com.docker.compose.project={project_name}"}

    for container in docker_client.containers.list(all=True, filters=project_filter):
        container.remove(force=True, v=True)

    for network in docker_client.networks.list(filters=project_filter):
        network.remove()

    for volume in docker_client.volumes.list(filters=project_filter):
        volume.remove(force=True)


@pytest.fixture(scope=containers_scope)
def docker_services(
    docker_compose_command,
    docker_compose_file,
    docker_compose_project_name,
    docker_setup,
    docker_cleanup,
):
    """Start compose services and clean them up without forking during teardown."""
    docker_compose = DockerComposeExecutor(
        docker_compose_command,
        docker_compose_file,
        docker_compose_project_name,
    )

    if docker_setup:
        if isinstance(docker_setup, str):
            docker_setup = [docker_setup]
        for command in docker_setup:
            docker_compose.execute(command)

    try:
        yield Services(docker_compose)
    finally:
        if docker_cleanup:
            _cleanup_docker_project(docker_compose_project_name)


class DockerProject:
    """Compatibility wrapper for pytest-docker-compose docker_project fixture.

    The `stop()` method talks to the Docker daemon via the SDK (unix socket)
    instead of forking a `docker compose kill` subprocess. Forking from a
    python process that has active gRPC threads crashes the child with
    SIGABRT on Python 3.9 (long-standing gRPC fork-handler issue), and
    `stop()` is the worst offender because the driver is in the middle of
    busy traffic when it's called.

    `start()` still uses `docker compose up -d --force-recreate` because
    recreating a YDB container after SIGKILL needs the full compose config
    (in-memory PDisks lose state, plain `container.start()` can't recover
    them). By the time `start()` runs, the driver's connections are already
    broken and its background threads are sleeping in retry backoff, so
    forking a subprocess is safe.
    """

    def __init__(self, project_name, docker_compose, docker_services, endpoint):
        self._project_name = project_name
        self._docker_compose = docker_compose
        self._docker_services = docker_services
        self._endpoint = endpoint
        self._docker = _docker_client()
        self._stopped = False

    def _ydb_container(self):
        containers = self._docker.containers.list(
            all=True,
            filters={
                "label": [
                    f"com.docker.compose.project={self._project_name}",
                    "com.docker.compose.service=ydb",
                ]
            },
        )
        if not containers:
            raise RuntimeError(f"YDB container for compose project '{self._project_name}' not found")
        return containers[0]

    def stop(self):
        """Instantly kill the YDB container (simulates network failure)."""
        self._stopped = True
        self._ydb_container().kill()

    def start(self):
        """Restart containers and wait until YDB is responsive."""
        if self._stopped:
            self._docker_compose.execute("up -d --force-recreate")
            self._stopped = False
        else:
            self._docker_compose.execute("start")

        self._docker_services.wait_until_responsive(
            timeout=120.0,
            pause=2.0,
            check=lambda: is_ydb_responsive(self._endpoint),
        )


@pytest.fixture(scope="module")
def docker_project(docker_compose_project_name, docker_services, endpoint):
    """Compatibility fixture providing stop/start methods like pytest-docker-compose."""
    return DockerProject(docker_compose_project_name, docker_services._docker_compose, docker_services, endpoint)


def is_ydb_responsive(endpoint):
    """Check if YDB is ready to accept connections."""
    try:
        with ydb.Driver(endpoint=endpoint, database="/local") as driver:
            driver.wait(timeout=5)
            with ydb.SessionPool(driver) as pool:
                with pool.checkout() as session:
                    session.execute_scheme("create table `.sys_health/test_table` (A int32, primary key(A));")
            return True
    except Exception:
        return False


def is_ydb_secure_responsive(endpoint, root_certificates):
    """Check if YDB TLS endpoint is ready to accept connections."""
    try:
        with ydb.Driver(
            endpoint=f"grpcs://{endpoint}",
            database="/local",
            root_certificates=root_certificates,
        ) as driver:
            driver.wait(timeout=5)
            with ydb.SessionPool(driver) as pool:
                with pool.checkout() as session:
                    session.execute_scheme("create table `.sys_health/test_table_tls` (A int32, primary key(A));")
            return True
    except Exception:
        return False


@pytest.fixture(scope="module")
def endpoint(request):
    """Wait for YDB to be responsive and return endpoint."""
    # Resolve docker_services lazily so the fixture is only requested when a
    # test actually needs the container. The compose file publishes a fixed
    # host port, so avoid `port_for()` — it shells out to `docker compose
    # port`, which is exactly the late subprocess path that can trip the
    # Python 3.9 gRPC fork race.
    docker_services = request.getfixturevalue("docker_services")
    endpoint_url = f"localhost:{YDB_ENDPOINT_PORT}"
    docker_services.wait_until_responsive(
        timeout=60.0,
        pause=1.0,
        check=lambda: is_ydb_responsive(endpoint_url),
    )
    yield endpoint_url


@pytest.fixture(scope="session")
def secure_endpoint(pytestconfig, docker_services):
    """Wait for YDB TLS endpoint to be responsive."""
    ca_path = os.path.join(str(pytestconfig.rootdir), "ydb_certs/ca.pem")

    # Wait for certificate file to be generated by container
    def wait_for_certificate():
        return os.path.exists(ca_path)

    docker_services.wait_until_responsive(
        timeout=30.0,
        pause=1.0,
        check=wait_for_certificate,
    )

    assert os.path.exists(ca_path), f"Certificate not found at {ca_path}"
    os.environ["YDB_SSL_ROOT_CERTIFICATES_FILE"] = ca_path
    root_certificates = ydb.load_ydb_root_certificate()

    endpoint_url = f"localhost:{YDB_SECURE_ENDPOINT_PORT}"

    docker_services.wait_until_responsive(
        timeout=60.0,
        pause=1.0,
        check=lambda: is_ydb_secure_responsive(endpoint_url, root_certificates),
    )

    yield endpoint_url


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


@pytest.fixture
def column_table_name(driver_sync, database):
    table_name = "column_table"

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
PARTITION BY HASH(id)
WITH (
    STORE = COLUMN
)
"""
                % table_name
            )

        pool.retry_operation_sync(create_table)
    return table_name


@pytest.fixture()
def column_table_path(database, column_table_name) -> str:
    return database + "/" + column_table_name


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
async def topic_with_two_partitions_path(driver, topic_consumer, database) -> str:
    topic_path = database + "/test-topic-two-partitions"

    try:
        await driver.topic_client.drop_topic(topic_path)
    except issues.SchemeError:
        pass

    await driver.topic_client.create_topic(
        path=topic_path,
        consumers=[topic_consumer],
        min_active_partitions=2,
        partition_count_limit=2,
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
async def topic_with_messages_with_metadata(driver, topic_consumer, database):
    topic_path = database + "/test-topic-with-messages-with-metadata"
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
            ydb.TopicWriterMessage(data="123".encode(), metadata_items={"key": "value"}),
            ydb.TopicWriterMessage(data="456".encode(), metadata_items={"key": b"value"}),
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
