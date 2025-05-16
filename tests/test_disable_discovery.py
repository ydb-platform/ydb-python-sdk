import pytest
import unittest.mock
import ydb
import asyncio
from ydb import _apis


TEST_ERROR = "Test error"
TEST_QUERY = "SELECT 1 + 2 AS sum"

@pytest.fixture
def mock_connection():
    """Mock a YDB connection to avoid actual connections."""
    with unittest.mock.patch('ydb.connection.Connection.ready_factory') as mock_factory:
        # Setup the mock to return a connection-like object
        mock_connection = unittest.mock.MagicMock()
        # Use the endpoint fixture value via the function parameter
        mock_connection.endpoint = "localhost:2136"  # Will be overridden in tests
        mock_connection.node_id = "mock_node_id"
        mock_factory.return_value = mock_connection
        yield mock_factory


@pytest.fixture
def mock_aio_connection():
    """Mock a YDB async connection to avoid actual connections."""
    with unittest.mock.patch('ydb.aio.connection.Connection.__init__') as mock_init:
        # Setup the mock to return None (as __init__ does)
        mock_init.return_value = None

        # Mock connection_ready method
        with unittest.mock.patch('ydb.aio.connection.Connection.connection_ready') as mock_ready:
            # Create event loop if there isn't one currently
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            future = asyncio.Future()
            future.set_result(None)
            mock_ready.return_value = future
            yield mock_init


def create_mock_discovery_resolver(path):
    """Create a mock discovery resolver that raises exception if called."""
    def _mock_fixture():
        with unittest.mock.patch(path) as mock_resolve:
            # Configure mock to throw an exception if called
            mock_resolve.side_effect = Exception("Discovery should not be executed when discovery is disabled")
            yield mock_resolve
    return _mock_fixture


# Mock discovery resolvers to verify no discovery requests are made
mock_discovery_resolver = pytest.fixture(create_mock_discovery_resolver('ydb.resolver.DiscoveryEndpointsResolver.context_resolve'))
mock_aio_discovery_resolver = pytest.fixture(create_mock_discovery_resolver('ydb.aio.resolver.DiscoveryEndpointsResolver.resolve'))


# Basic unit tests for DriverConfig
def test_driver_config_has_disable_discovery_option(endpoint, database):
    """Test that DriverConfig has the disable_discovery option."""
    config = ydb.DriverConfig(
        endpoint=endpoint,
        database=database,
        disable_discovery=True
    )
    assert hasattr(config, "disable_discovery")
    assert config.disable_discovery is True


# Driver config fixtures
def create_driver_config(endpoint, database, disable_discovery):
    """Create a driver config with the given discovery setting."""
    return ydb.DriverConfig(
        endpoint=endpoint,
        database=database,
        disable_discovery=disable_discovery,
    )


@pytest.fixture
def driver_config_disabled_discovery(endpoint, database):
    """A driver config with discovery disabled"""
    return create_driver_config(endpoint, database, True)


@pytest.fixture
def driver_config_enabled_discovery(endpoint, database):
    """A driver config with discovery enabled (default)"""
    return create_driver_config(endpoint, database, False)


# Common test assertions
def assert_discovery_disabled(driver):
    """Assert that discovery is disabled in the driver."""
    assert "Discovery is disabled" in driver.discovery_debug_details()


def create_future_with_error():
    """Create a future with a test error."""
    future = asyncio.Future()
    future.set_exception(ydb.issues.Error(TEST_ERROR))
    return future


def create_completed_future():
    """Create a completed future."""
    future = asyncio.Future()
    future.set_result(None)
    return future


# Mock tests for synchronous driver
def test_sync_driver_discovery_disabled_mock(driver_config_disabled_discovery, mock_connection, mock_discovery_resolver):
    """Test that when disable_discovery=True, the discovery thread is not started and resolver is not called (mock)."""
    with unittest.mock.patch('ydb.pool.Discovery') as mock_discovery_class:
        driver = ydb.Driver(driver_config=driver_config_disabled_discovery)

        try:
            # Check that the discovery thread was not created
            mock_discovery_class.assert_not_called()

            # Check that discovery is disabled in debug details
            assert_discovery_disabled(driver)

            # Execute a dummy call to verify no discovery requests are made
            try:
                driver(ydb.issues.Error(TEST_ERROR), _apis.OperationService.Stub, "GetOperation")
            except ydb.issues.Error:
                pass  # Expected exception, we just want to ensure no discovery occurs

            # Verify the mock wasn't called
            assert not mock_discovery_resolver.called, "Discovery resolver should not be called when discovery is disabled"
        finally:
            # Clean up
            driver.stop()


def test_sync_driver_discovery_enabled_mock(driver_config_enabled_discovery, mock_connection):
    """Test that when disable_discovery=False, the discovery thread is started (mock)."""
    with unittest.mock.patch('ydb.pool.Discovery') as mock_discovery_class:
        mock_discovery_instance = unittest.mock.MagicMock()
        mock_discovery_class.return_value = mock_discovery_instance

        driver = ydb.Driver(driver_config=driver_config_enabled_discovery)

        try:
            # Check that the discovery thread was created and started
            mock_discovery_class.assert_called_once()
            assert mock_discovery_instance.start.called
        finally:
            # Clean up
            driver.stop()


# Helper for setting up async driver test mocks
def setup_async_driver_mocks():
    """Set up common mocks for async driver tests."""
    mocks = {}

    # Create mock for Discovery class
    discovery_patcher = unittest.mock.patch('ydb.aio.pool.Discovery')
    mocks['mock_discovery_class'] = discovery_patcher.start()

    # Mock the event loop
    loop_patcher = unittest.mock.patch('asyncio.get_event_loop')
    mock_loop = loop_patcher.start()
    mock_loop_instance = unittest.mock.MagicMock()
    mock_loop.return_value = mock_loop_instance
    mock_loop_instance.create_task.return_value = unittest.mock.MagicMock()
    mocks['mock_loop'] = mock_loop

    # Mock the connection pool stop method
    stop_patcher = unittest.mock.patch('ydb.aio.pool.ConnectionPool.stop')
    mock_stop = stop_patcher.start()
    mock_stop.return_value = create_completed_future()
    mocks['mock_stop'] = mock_stop

    # Add cleanup for all patchers
    mocks['patchers'] = [discovery_patcher, loop_patcher, stop_patcher]

    return mocks


def teardown_async_mocks(mocks):
    """Clean up all mock patchers."""
    for patcher in mocks['patchers']:
        patcher.stop()


# Mock tests for asynchronous driver
@pytest.mark.asyncio
async def test_aio_driver_discovery_disabled_mock(driver_config_disabled_discovery, mock_aio_connection, mock_aio_discovery_resolver):
    """Test that when disable_discovery=True, the discovery is not created and resolver is not called (mock)."""
    mocks = setup_async_driver_mocks()

    try:
        # Mock the pool's call method to prevent unhandled exceptions
        with unittest.mock.patch('ydb.aio.pool.ConnectionPool.__call__') as mock_call:
            mock_call.return_value = create_future_with_error()

            driver = ydb.aio.Driver(driver_config=driver_config_disabled_discovery)

            try:
                # Check that the discovery class was not instantiated
                mocks['mock_discovery_class'].assert_not_called()

                # Check that discovery is disabled in debug details
                assert_discovery_disabled(driver)

                # Execute a dummy call to verify no discovery requests are made
                try:
                    try:
                        await driver(ydb.issues.Error(TEST_ERROR), _apis.OperationService.Stub, "GetOperation")
                    except ydb.issues.Error:
                        pass  # Expected exception, we just want to ensure no discovery occurs
                except Exception as e:
                    if "discovery is disabled" in str(e).lower():
                        raise  # If the error is related to discovery being disabled, re-raise it
                    pass  # Other exceptions are expected as we're using mocks

                # Verify the mock wasn't called
                assert not mock_aio_discovery_resolver.called, "Discovery resolver should not be called when discovery is disabled"
            finally:
                # The stop method is already mocked, so we don't need to await it
                pass
    finally:
        teardown_async_mocks(mocks)


@pytest.mark.asyncio
async def test_aio_driver_discovery_enabled_mock(driver_config_enabled_discovery, mock_aio_connection):
    """Test that when disable_discovery=False, the discovery is created (mock)."""
    mocks = setup_async_driver_mocks()

    try:
        mock_discovery_instance = unittest.mock.MagicMock()
        mocks['mock_discovery_class'].return_value = mock_discovery_instance

        driver = ydb.aio.Driver(driver_config=driver_config_enabled_discovery)

        try:
            # Check that the discovery class was instantiated
            mocks['mock_discovery_class'].assert_called_once()
        finally:
            # The stop method is already mocked, so we don't need to await it
            pass
    finally:
        teardown_async_mocks(mocks)


# Common integration test logic
def perform_integration_test_checks(driver, is_async=False):
    """Common assertions for integration tests."""
    assert_discovery_disabled(driver)


# Integration tests with real YDB
def test_integration_disable_discovery(driver_config_disabled_discovery):
    """Integration test that tests the disable_discovery feature with a real YDB container."""
    # Create driver with discovery disabled
    driver = ydb.Driver(driver_config=driver_config_disabled_discovery)
    try:
        driver.wait(timeout=15)
        perform_integration_test_checks(driver)

        # Try to execute a simple query to ensure it works with discovery disabled
        with ydb.SessionPool(driver) as pool:
            def query_callback(session):
                result_sets = session.transaction().execute(TEST_QUERY, commit_tx=True)
                assert len(result_sets) == 1
                assert result_sets[0].rows[0].sum == 3

            pool.retry_operation_sync(query_callback)
    finally:
        driver.stop(timeout=10)


@pytest.mark.asyncio
async def test_integration_aio_disable_discovery(driver_config_disabled_discovery):
    """Integration test that tests the disable_discovery feature with a real YDB container (async)."""
    # Create driver with discovery disabled
    driver = ydb.aio.Driver(driver_config=driver_config_disabled_discovery)
    try:
        await driver.wait(timeout=15)
        perform_integration_test_checks(driver, is_async=True)

        # Try to execute a simple query to ensure it works with discovery disabled
        session_pool = ydb.aio.SessionPool(driver, size=10)

        async def query_callback(session):
            result_sets = await session.transaction().execute(TEST_QUERY, commit_tx=True)
            assert len(result_sets) == 1
            assert result_sets[0].rows[0].sum == 3

        try:
            await session_pool.retry_operation(query_callback)
        finally:
            await session_pool.stop()
    finally:
        await driver.stop(timeout=10)