# -*- coding: utf-8 -*-
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from ydb import driver, connection
from ydb.aio import pool, nearest_dc


class MockEndpointInfo:
    def __init__(self, address, port, location):
        self.address = address
        self.port = port
        self.endpoint = f"{address}:{port}"
        self.location = location
        self.ssl = False
        self.node_id = 1

    def endpoints_with_options(self):
        yield (self.endpoint, connection.EndpointOptions(ssl_target_name_override=None, node_id=self.node_id))


class MockDiscoveryResult:
    def __init__(self, self_location, endpoints):
        self.self_location = self_location
        self.endpoints = endpoints


@pytest.mark.asyncio
async def test_detect_local_dc_overrides_server_location():
    """Test that detected location overrides server's self_location for preferred endpoints."""
    # Server reports dc1, but we detect dc2 as nearest
    endpoints = [
        MockEndpointInfo("dc1-host", 2135, "dc1"),
        MockEndpointInfo("dc2-host", 2135, "dc2"),
    ]
    mock_result = MockDiscoveryResult(self_location="dc1", endpoints=endpoints)

    mock_resolver = MagicMock()
    mock_resolver.resolve = AsyncMock(return_value=mock_result)

    preferred = []

    def mock_init(self, endpoint, driver_config, endpoint_options=None):
        self.endpoint = endpoint
        self.node_id = 1

    with patch.object(nearest_dc, "detect_local_dc", AsyncMock(return_value="dc2")):
        with patch("ydb.aio.connection.Connection.__init__", mock_init):
            with patch("ydb.aio.connection.Connection.connection_ready", AsyncMock()):
                with patch("ydb.aio.connection.Connection.close", AsyncMock()):
                    with patch("ydb.aio.connection.Connection.add_cleanup_callback", lambda *a: None):
                        config = driver.DriverConfig(
                            endpoint="grpc://test:2135", database="/local", detect_local_dc=True, use_all_nodes=False
                        )
                        discovery = pool.Discovery(
                            store=pool.ConnectionsCache(config.use_all_nodes), driver_config=config
                        )
                        discovery._resolver = mock_resolver

                        original_add = discovery._cache.add
                        discovery._cache.add = lambda conn, pref=False: (
                            preferred.append(conn.endpoint) if pref else None,
                            original_add(conn, pref),
                        )[1]

                        await discovery.execute_discovery()

    assert any("dc2" in ep for ep in preferred), "dc2 should be preferred (detected)"
    assert not any("dc1" in ep for ep in preferred), "dc1 should not be preferred"


@pytest.mark.asyncio
async def test_detect_local_dc_failure_fallback():
    """Test that detection failure falls back to server's self_location."""
    endpoints = [
        MockEndpointInfo("dc1-host", 2135, "dc1"),
        MockEndpointInfo("dc2-host", 2135, "dc2"),
    ]
    mock_result = MockDiscoveryResult(self_location="dc1", endpoints=endpoints)

    mock_resolver = MagicMock()
    mock_resolver.resolve = AsyncMock(return_value=mock_result)

    preferred = []

    def mock_init(self, endpoint, driver_config, endpoint_options=None):
        self.endpoint = endpoint
        self.node_id = 1

    with patch.object(nearest_dc, "detect_local_dc", AsyncMock(return_value=None)):
        with patch("ydb.aio.connection.Connection.__init__", mock_init):
            with patch("ydb.aio.connection.Connection.connection_ready", AsyncMock()):
                with patch("ydb.aio.connection.Connection.close", AsyncMock()):
                    with patch("ydb.aio.connection.Connection.add_cleanup_callback", lambda *a: None):
                        config = driver.DriverConfig(
                            endpoint="grpc://test:2135", database="/local", detect_local_dc=True, use_all_nodes=False
                        )
                        discovery = pool.Discovery(
                            store=pool.ConnectionsCache(config.use_all_nodes), driver_config=config
                        )
                        discovery._resolver = mock_resolver

                        original_add = discovery._cache.add
                        discovery._cache.add = lambda conn, pref=False: (
                            preferred.append(conn.endpoint) if pref else None,
                            original_add(conn, pref),
                        )[1]

                        await discovery.execute_discovery()

    assert any("dc1" in ep for ep in preferred), "dc1 should be preferred (server fallback)"
