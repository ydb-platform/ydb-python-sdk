# -*- coding: utf-8 -*-
from unittest.mock import Mock, MagicMock, patch
from ydb import driver, pool, nearest_dc, connection


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


def test_detect_local_dc_overrides_server_location():
    """Test that detected location overrides server's self_location for preferred endpoints."""
    # Server reports dc1, but we detect dc2 as nearest
    endpoints = [
        MockEndpointInfo("dc1-host", 2135, "dc1"),
        MockEndpointInfo("dc2-host", 2135, "dc2"),
    ]
    mock_result = MockDiscoveryResult(self_location="dc1", endpoints=endpoints)

    mock_resolver = MagicMock()
    mock_resolver.context_resolve.return_value.__enter__.return_value = mock_result
    mock_resolver.context_resolve.return_value.__exit__.return_value = None

    preferred = []

    with patch.object(nearest_dc, "detect_local_dc", Mock(return_value="dc2")):
        with patch(
            "ydb.connection.Connection.ready_factory", lambda *args, **kw: MagicMock(endpoint=args[0], node_id=1)
        ):
            config = driver.DriverConfig(endpoint="grpc://test:2135", database="/local", detect_local_dc=True)
            discovery = pool.Discovery(store=pool.ConnectionsCache(), driver_config=config)
            discovery._resolver = mock_resolver

            original_add = discovery._cache.add
            discovery._cache.add = lambda conn, pref=False: (
                preferred.append(conn.endpoint) if pref else None,
                original_add(conn, pref),
            )[1]

            discovery.execute_discovery()

    assert any("dc2" in ep for ep in preferred), "dc2 should be preferred (detected)"
    assert not any("dc1" in ep for ep in preferred), "dc1 should not be preferred"


def test_detect_local_dc_failure_fallback():
    """Test that detection failure falls back to server's self_location."""
    endpoints = [
        MockEndpointInfo("dc1-host", 2135, "dc1"),
        MockEndpointInfo("dc2-host", 2135, "dc2"),
    ]
    mock_result = MockDiscoveryResult(self_location="dc1", endpoints=endpoints)

    mock_resolver = MagicMock()
    mock_resolver.context_resolve.return_value.__enter__.return_value = mock_result
    mock_resolver.context_resolve.return_value.__exit__.return_value = None

    preferred = []

    with patch.object(nearest_dc, "detect_local_dc", Mock(return_value=None)):
        with patch(
            "ydb.connection.Connection.ready_factory", lambda *args, **kw: MagicMock(endpoint=args[0], node_id=1)
        ):
            config = driver.DriverConfig(endpoint="grpc://test:2135", database="/local", detect_local_dc=True)
            discovery = pool.Discovery(store=pool.ConnectionsCache(), driver_config=config)
            discovery._resolver = mock_resolver

            original_add = discovery._cache.add
            discovery._cache.add = lambda conn, pref=False: (
                preferred.append(conn.endpoint) if pref else None,
                original_add(conn, pref),
            )[1]

            discovery.execute_discovery()

    assert any("dc1" in ep for ep in preferred), "dc1 should be preferred (server fallback)"
