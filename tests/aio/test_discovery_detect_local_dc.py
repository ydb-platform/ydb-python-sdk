# -*- coding: utf-8 -*-
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from ydb import driver, connection
from ydb import _apis, resolver
from ydb.aio import pool, _utilities


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

    with patch.object(_utilities, "detect_local_dc", AsyncMock(return_value="dc2")):
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

    with patch.object(_utilities, "detect_local_dc", AsyncMock(return_value=None)):
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


@pytest.mark.asyncio
async def test_detect_local_dc_skipped_when_use_all_nodes_true():
    """Test that detect_local_dc is NOT called when use_all_nodes=True."""
    endpoints = [
        MockEndpointInfo("dc1-host", 2135, "dc1"),
        MockEndpointInfo("dc2-host", 2135, "dc2"),
    ]
    mock_result = MockDiscoveryResult(self_location="dc1", endpoints=endpoints)

    mock_resolver = MagicMock()
    mock_resolver.resolve = AsyncMock(return_value=mock_result)

    def mock_init(self, endpoint, driver_config, endpoint_options=None):
        self.endpoint = endpoint
        self.node_id = 1

    with patch.object(_utilities, "detect_local_dc", AsyncMock(return_value="dc2")) as detect_mock:
        with patch("ydb.aio.connection.Connection.__init__", mock_init):
            with patch("ydb.aio.connection.Connection.connection_ready", AsyncMock()):
                with patch("ydb.aio.connection.Connection.close", AsyncMock()):
                    with patch("ydb.aio.connection.Connection.add_cleanup_callback", lambda *a: None):
                        config = driver.DriverConfig(
                            endpoint="grpc://test:2135", database="/local", detect_local_dc=True, use_all_nodes=True
                        )
                        discovery = pool.Discovery(
                            store=pool.ConnectionsCache(config.use_all_nodes), driver_config=config
                        )
                        discovery._resolver = mock_resolver
                        await discovery.execute_discovery()

    assert detect_mock.call_count == 0, "detect_local_dc should NOT be called when use_all_nodes=True"


class PrimaryConnection:
    failed = set()
    created = []

    def __init__(self, endpoint, driver_config, endpoint_options=None):
        self.endpoint = endpoint
        self.node_id = endpoint_options.node_id
        self.callbacks = []
        self.closed = False
        self.created.append(self)

    async def connection_ready(self, ready_timeout):
        if self.endpoint in self.failed:
            raise TimeoutError()

    def add_cleanup_callback(self, callback):
        self.callbacks.append(callback)

    async def close(self, grace=30):
        self.closed = True
        for callback in self.callbacks:
            callback(self)


def primary_result(states, nodes=((1, "A"), (2, "B"))):
    message = _apis.ydb_discovery.ListEndpointsResult(self_location="local")
    for node_id, pile in nodes:
        message.endpoints.add(
            address=f"node{node_id}",
            port=2135,
            node_id=node_id,
            location="local" if pile == "A" else "remote",
            bridge_pile_name=pile,
        )
    for name, state in states.items():
        message.pile_states.add(pile_name=name, state=state)
    response = _apis.ydb_discovery.ListEndpointsResponse()
    response.operation.ready = True
    response.operation.status = 400000
    response.operation.result.Pack(message)
    return resolver.DiscoveryResult.from_response(None, response, use_all_nodes=True)


def primary_discovery(monkeypatch, result, enabled=True, use_all_nodes=True, failed=()):
    PrimaryConnection.failed, PrimaryConnection.created = set(failed), []
    monkeypatch.setattr(pool, "Connection", PrimaryConnection)
    config = driver.DriverConfig("grpc://test:2135", "/local", use_all_nodes=use_all_nodes, prefer_primary_pile=enabled)
    discovery = pool.Discovery(pool.ConnectionsCache(use_all_nodes), config)
    discovery._resolver.resolve = AsyncMock(return_value=result)
    return discovery


@pytest.mark.asyncio
async def test_primary_role_change_and_affinity(monkeypatch):
    discovery = primary_discovery(monkeypatch, primary_result({"A": 1, "B": 3}))
    assert await discovery.execute_discovery()
    assert {(await discovery._cache.get()).node_id for _ in range(10)} == {1}
    assert (await discovery._cache.get(connection.EndpointKey("node2:2135", 2))).node_id == 2
    discovery._resolver.resolve.return_value = primary_result({"A": 3, "B": 1})
    assert await discovery.execute_discovery()
    assert {(await discovery._cache.get()).node_id for _ in range(10)} == {2}
    assert len(PrimaryConnection.created) == 2
    assert not any(conn.closed for conn in PrimaryConnection.created)
    assert (await discovery._cache.get(connection.EndpointKey("node1:2135", 1))).node_id == 1
    await (await discovery._cache.get()).close()
    assert (await discovery._cache.get()).node_id == 1


@pytest.mark.asyncio
async def test_primary_off_and_ordinary_cluster_locality(monkeypatch):
    discovery = primary_discovery(monkeypatch, primary_result({"A": 1, "B": 3}), enabled=False)
    assert await discovery.execute_discovery()
    assert {(await discovery._cache.get()).node_id for _ in range(10)} == {1, 2}
    discovery = primary_discovery(monkeypatch, primary_result({}), use_all_nodes=False)
    assert await discovery.execute_discovery()
    assert {(await discovery._cache.get()).node_id for _ in range(10)} == {1}
    discovery._resolver.resolve.return_value = primary_result({"A": 3, "B": 1})
    assert await discovery.execute_discovery()
    assert (await discovery._cache.get()).node_id == 2
    discovery._resolver.resolve.return_value = primary_result({})
    assert await discovery.execute_discovery()
    assert (await discovery._cache.get()).node_id == 1


@pytest.mark.asyncio
async def test_primary_promoted_and_unknown_states(monkeypatch):
    discovery = primary_discovery(
        monkeypatch,
        primary_result({"A": 1, "B": 2, "C": 3, "D": 99}, ((1, "A"), (2, "B"), (3, "C"), (4, "D"), (5, "missing"))),
    )
    assert await discovery.execute_discovery()
    assert {(await discovery._cache.get()).node_id for _ in range(10)} == {1, 2}
    await (await discovery._cache.get(connection.EndpointKey("node1:2135", 1))).close()
    await (await discovery._cache.get(connection.EndpointKey("node2:2135", 2))).close()
    assert (await discovery._cache.get()).node_id == 3
    await (await discovery._cache.get()).close()
    assert {(await discovery._cache.get()).node_id for _ in range(10)} == {4, 5}


@pytest.mark.asyncio
async def test_primary_full_cache_admission_and_failed_connection(monkeypatch):
    old = tuple((i, "A") for i in range(1, 10))
    discovery = primary_discovery(monkeypatch, primary_result({"A": 1}, old))
    assert await discovery.execute_discovery() and discovery._cache.size == 9
    discovery._resolver.resolve.return_value = primary_result({"A": 3, "B": 1}, old + ((10, "B"),))
    PrimaryConnection.failed = {"node10:2135"}
    assert await discovery.execute_discovery()
    assert discovery._cache.size == 9
    assert not any(conn.closed for conn in PrimaryConnection.created if conn.node_id != 10)
    PrimaryConnection.failed.clear()
    assert await discovery.execute_discovery()
    assert (await discovery._cache.get()).node_id == 10
    assert discovery._cache.size == 9
    created_count = len(PrimaryConnection.created)
    assert await discovery.execute_discovery()
    assert len(PrimaryConnection.created) == created_count


@pytest.mark.asyncio
async def test_primary_cache_preserves_synchronized_fallback(monkeypatch):
    nodes = tuple((i, "A") for i in range(1, 11)) + ((11, "B"),)
    discovery = primary_discovery(monkeypatch, primary_result({"A": 1, "B": 3}, nodes))
    assert await discovery.execute_discovery() and discovery._cache.size == 9
    assert discovery._cache.already_exists("node11:2135")
    for conn in discovery._cache.values():
        if conn.node_id != 11:
            await conn.close()
    assert (await discovery._cache.get()).node_id == 11


@pytest.mark.asyncio
async def test_primary_alias_retirement_keeps_node_affinity():
    cache = pool.ConnectionsCache()
    options = connection.EndpointOptions(node_id=1)
    old = PrimaryConnection("old:2135", None, options)
    new = PrimaryConnection("new:2135", None, options)
    cache.add(old)
    cache.add(new)
    await old.close()
    assert await cache.get(connection.EndpointKey(None, 1)) is new


@pytest.mark.asyncio
async def test_primary_driver_keyword_and_config_override(monkeypatch):
    from ydb import topic
    from ydb.aio import driver as aio_driver, table, scheme, coordination

    seen = []
    monkeypatch.setattr(pool.ConnectionPool, "__init__", lambda self, config: seen.append(config))
    for module, name in (
        (topic, "TopicClientAsyncIO"),
        (table, "TableClient"),
        (scheme, "SchemeClient"),
        (coordination, "CoordinationClient"),
    ):
        monkeypatch.setattr(module, name, MagicMock())
    aio_driver.Driver(endpoint="grpc://test:2135", database="/local", prefer_primary_pile=True)
    assert seen[-1].prefer_primary_pile
    config = aio_driver.DriverConfig("grpc://test:2135", "/local", prefer_primary_pile=True)
    aio_driver.Driver(config)
    assert seen[-1].prefer_primary_pile
    aio_driver.Driver(config, prefer_primary_pile=False)
    assert not seen[-1].prefer_primary_pile


@pytest.mark.asyncio
async def test_primary_discovery_cancellation_closes_candidate(monkeypatch):
    import asyncio

    discovery = primary_discovery(monkeypatch, primary_result({"A": 1, "B": 3}))
    monkeypatch.setattr(PrimaryConnection, "connection_ready", AsyncMock(side_effect=asyncio.CancelledError))
    with pytest.raises(asyncio.CancelledError):
        await discovery.execute_discovery()
    assert len(PrimaryConnection.created) == 1
    assert PrimaryConnection.created[0].closed
