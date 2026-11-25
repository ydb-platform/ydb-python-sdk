# -*- coding: utf-8 -*-
from unittest.mock import AsyncMock, Mock, MagicMock, patch

import pytest
from ydb import driver, pool, _utilities, connection, issues
from ydb import _apis, resolver
from ydb.aio import resolver as aio_resolver


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

    with patch.object(_utilities, "detect_local_dc", Mock(return_value="dc2")):
        with patch(
            "ydb.connection.Connection.ready_factory", lambda *args, **kw: MagicMock(endpoint=args[0], node_id=1)
        ):
            config = driver.DriverConfig(
                endpoint="grpc://test:2135", database="/local", detect_local_dc=True, use_all_nodes=False
            )
            discovery = pool.Discovery(store=pool.ConnectionsCache(config.use_all_nodes), driver_config=config)
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

    with patch.object(_utilities, "detect_local_dc", Mock(return_value=None)):
        with patch(
            "ydb.connection.Connection.ready_factory", lambda *args, **kw: MagicMock(endpoint=args[0], node_id=1)
        ):
            config = driver.DriverConfig(
                endpoint="grpc://test:2135", database="/local", detect_local_dc=True, use_all_nodes=False
            )
            discovery = pool.Discovery(store=pool.ConnectionsCache(config.use_all_nodes), driver_config=config)
            discovery._resolver = mock_resolver

            original_add = discovery._cache.add
            discovery._cache.add = lambda conn, pref=False: (
                preferred.append(conn.endpoint) if pref else None,
                original_add(conn, pref),
            )[1]

            discovery.execute_discovery()

    assert any("dc1" in ep for ep in preferred), "dc1 should be preferred (server fallback)"


def test_detect_local_dc_skipped_when_use_all_nodes_true():
    """Test that detect_local_dc is NOT called when use_all_nodes=True."""
    endpoints = [
        MockEndpointInfo("dc1-host", 2135, "dc1"),
        MockEndpointInfo("dc2-host", 2135, "dc2"),
    ]
    mock_result = MockDiscoveryResult(self_location="dc1", endpoints=endpoints)

    mock_resolver = MagicMock()
    mock_resolver.context_resolve.return_value.__enter__.return_value = mock_result
    mock_resolver.context_resolve.return_value.__exit__.return_value = None

    with patch.object(_utilities, "detect_local_dc", Mock(return_value="dc2")) as detect_mock:
        with patch(
            "ydb.connection.Connection.ready_factory", lambda *args, **kw: MagicMock(endpoint=args[0], node_id=1)
        ):
            config = driver.DriverConfig(
                endpoint="grpc://test:2135", database="/local", detect_local_dc=True, use_all_nodes=True
            )
            discovery = pool.Discovery(store=pool.ConnectionsCache(config.use_all_nodes), driver_config=config)
            discovery._resolver = mock_resolver
            discovery.execute_discovery()

        assert detect_mock.call_count == 0, "detect_local_dc should NOT be called when use_all_nodes=True"


class PrimaryConnection:
    def __init__(self, endpoint, node_id):
        self.endpoint, self.node_id = endpoint, node_id
        self.closed = False
        self.callbacks = []

    def add_cleanup_callback(self, callback):
        self.callbacks.append(callback)

    def close(self):
        self.closed = True
        for callback in self.callbacks:
            callback(self)


def primary_response(states, nodes):
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
    return response


def primary_result(states, nodes=((1, "A"), (2, "B"))):
    response = primary_response(states, nodes)
    return resolver.DiscoveryResult.from_response(None, response, use_all_nodes=True)


async def resolve_node_order(monkeypatch, config, response, is_async):
    module = aio_resolver if is_async else resolver
    discovery = module.DiscoveryEndpointsResolver(config)
    monkeypatch.setattr(resolver.random, "shuffle", lambda endpoints: endpoints.sort(key=lambda info: info.node_id))

    def list_endpoints(request, stub, method, wrap_result, *, settings, wrap_args=()):
        return wrap_result(None, response, *wrap_args)

    if is_async:
        bootstrap = AsyncMock(side_effect=list_endpoints)
        monkeypatch.setattr(aio_resolver.conn_impl, "Connection", Mock(return_value=bootstrap))
        result = await discovery.resolve()
    else:
        bootstrap = Mock(side_effect=list_endpoints)
        monkeypatch.setattr(connection.Connection, "ready_factory", Mock(return_value=bootstrap))
        result = discovery.resolve()

    return [info.node_id for info in result.endpoints]


@pytest.mark.asyncio
@pytest.mark.parametrize("use_all_nodes", [False, True])
@pytest.mark.parametrize("is_async", [False, True])
async def test_bridge_discovery_orders_connections_by_pile(monkeypatch, use_all_nodes, is_async):
    response = primary_response(
        {"A": 3, "B": 3, "C": 2, "D": 1}, ((1, "unknown"), (2, "B"), (3, "A"), (4, "C"), (5, "D"))
    )
    config = driver.DriverConfig("grpc://test:2135", "/local", use_all_nodes=use_all_nodes, prefer_primary_pile=True)
    assert await resolve_node_order(monkeypatch, config, response, is_async) == [4, 5, 2, 3, 1]


@pytest.mark.asyncio
@pytest.mark.parametrize("is_async", [False, True])
@pytest.mark.parametrize("states,prefer_primary_pile", [({}, True), ({"A": 3, "B": 1}, False)])
@pytest.mark.parametrize("use_all_nodes,expected", [(True, [1, 2]), (False, [2, 1])])
async def test_discovery_keeps_ordinary_order_without_bridge_policy(
    monkeypatch, states, prefer_primary_pile, use_all_nodes, expected, is_async
):
    response = primary_response(states, ((1, "B"), (2, "A")))
    config = driver.DriverConfig(
        "grpc://test:2135", "/local", use_all_nodes=use_all_nodes, prefer_primary_pile=prefer_primary_pile
    )
    assert await resolve_node_order(monkeypatch, config, response, is_async) == expected


def primary_discovery(monkeypatch, result, enabled=True, use_all_nodes=True, failed=()):
    created = []

    def ready(endpoint, config, timeout, endpoint_options):
        if endpoint in failed:
            return None
        conn = PrimaryConnection(endpoint, endpoint_options.node_id)
        created.append(conn)
        return conn

    monkeypatch.setattr(connection.Connection, "ready_factory", ready)
    config = driver.DriverConfig("grpc://test:2135", "/local", use_all_nodes=use_all_nodes, prefer_primary_pile=enabled)
    discovery = pool.Discovery(pool.ConnectionsCache(use_all_nodes), config)
    discovery._resolver = MagicMock()
    discovery._resolver.context_resolve.return_value.__enter__.return_value = result
    return discovery, created


def test_primary_role_change_updates_existing_connections_and_affinity(monkeypatch):
    discovery, created = primary_discovery(monkeypatch, primary_result({"A": 1, "B": 3}))
    assert discovery.execute_discovery()
    assert {discovery._cache.get().node_id for _ in range(10)} == {1}
    assert discovery._cache.get(connection.EndpointKey("node2:2135", 2)).node_id == 2
    discovery._resolver.context_resolve.return_value.__enter__.return_value = primary_result({"A": 3, "B": 1})
    assert discovery.execute_discovery()
    assert {discovery._cache.get().node_id for _ in range(10)} == {2}
    assert len(created) == 2 and not any(conn.closed for conn in created)
    assert discovery._cache.get(connection.EndpointKey("node1:2135", 1)).node_id == 1
    discovery._cache.get().close()
    assert discovery._cache.get().node_id == 1


def test_primary_option_is_off_by_default_and_ordinary_clusters_keep_locality(monkeypatch):
    assert not driver.DriverConfig("grpc://test:2135").prefer_primary_pile
    discovery, _ = primary_discovery(monkeypatch, primary_result({"A": 1, "B": 3}), enabled=False)
    assert discovery.execute_discovery()
    assert {discovery._cache.get().node_id for _ in range(10)} == {1, 2}
    discovery, created = primary_discovery(monkeypatch, primary_result({}), use_all_nodes=False)
    assert discovery.execute_discovery()
    assert {discovery._cache.get().node_id for _ in range(10)} == {1}
    discovery._resolver.context_resolve.return_value.__enter__.return_value = primary_result({"A": 3, "B": 1})
    assert discovery.execute_discovery()
    assert discovery._cache.get().node_id == 2
    discovery._resolver.context_resolve.return_value.__enter__.return_value = primary_result({})
    assert discovery.execute_discovery()
    assert discovery._cache.get().node_id == 1
    assert len(created) == 2


@pytest.mark.parametrize("use_all_nodes,detect_local_dc", [(True, True), (False, False), (False, True)])
def test_empty_pile_states_restore_configured_balancing(monkeypatch, use_all_nodes, detect_local_dc):
    discovery, created = primary_discovery(monkeypatch, primary_result({"A": 1, "B": 3}), use_all_nodes=use_all_nodes)
    discovery._driver_config.detect_local_dc = detect_local_dc
    detector = Mock(return_value="remote")
    monkeypatch.setattr(_utilities, "detect_local_dc", detector)
    assert discovery.execute_discovery()
    assert {discovery._cache.get().node_id for _ in range(2)} == {1}
    detector.assert_not_called()

    ordinary = primary_result({})
    ordinary.self_location = "local" if detect_local_dc else "remote"
    discovery._resolver.context_resolve.return_value.__enter__.return_value = ordinary
    assert discovery.execute_discovery()
    assert {discovery._cache.get().node_id for _ in range(2)} == ({1, 2} if use_all_nodes else {2})
    assert len(created) == 2 and not any(conn.closed for conn in created)


def test_primary_promoted_synchronized_and_unknown_fallback(monkeypatch):
    result = primary_result({"A": 1, "B": 2, "C": 3, "D": 99}, ((1, "A"), (2, "B"), (3, "C"), (4, "D"), (5, "missing")))
    discovery, _ = primary_discovery(monkeypatch, result)
    assert discovery.execute_discovery()
    choices = [discovery._cache.get().node_id for _ in range(4)]
    assert set(choices[:2]) == {1, 2}
    assert choices[2:] == choices[:2]
    discovery._cache.get(connection.EndpointKey("node1:2135", 1)).close()
    discovery._cache.get(connection.EndpointKey("node2:2135", 2)).close()
    assert discovery._cache.get().node_id == 3
    discovery._cache.get().close()
    assert {discovery._cache.get().node_id for _ in range(10)} == {4, 5}


def test_discovery_retires_withdrawn_endpoints(monkeypatch):
    discovery, created = primary_discovery(monkeypatch, primary_result({"A": 1, "B": 3}), use_all_nodes=False)
    assert discovery.execute_discovery()
    primary = discovery._cache.get()
    resolve = discovery._resolver.context_resolve.return_value.__enter__
    resolve.return_value = primary_result({}, nodes=((2, "B"),))
    assert discovery.execute_discovery()
    assert primary.closed
    assert discovery._cache.get().node_id == 2

    resolve.return_value = primary_result({}, nodes=())
    assert not discovery.execute_discovery()
    assert all(conn.closed for conn in created)
    with pytest.raises(issues.ConnectionLost):
        discovery._cache.get()


def test_discovery_closes_candidate_if_slot_was_taken(monkeypatch):
    result = primary_result({"A": 1, "B": 2})
    discovery, created = primary_discovery(monkeypatch, result)
    discovery._max_size = 1
    other = result.endpoints[1]
    admitted = PrimaryConnection(other.endpoint, other.node_id)
    ready = connection.Connection.ready_factory

    def finish_connecting(endpoint, config, timeout, endpoint_options):
        discovery._cache.add(admitted)
        return ready(endpoint, config, timeout, endpoint_options)

    monkeypatch.setattr(connection.Connection, "ready_factory", finish_connecting)
    assert discovery.execute_discovery()
    assert len(created) == 1 and created[0].closed
    assert discovery._cache.values() == [admitted]
    assert not admitted.closed


def test_primary_new_endpoint_enters_full_cache(monkeypatch):
    old = tuple((i, "A") for i in range(1, 10))
    discovery, created = primary_discovery(monkeypatch, primary_result({"A": 1}, old))
    assert discovery.execute_discovery() and discovery._cache.size == 9
    discovery._resolver.context_resolve.return_value.__enter__.return_value = primary_result(
        {"A": 3, "B": 1}, old + ((10, "B"),)
    )
    assert discovery.execute_discovery()
    assert discovery._cache.get().node_id == 10
    assert discovery._cache.size == 9 and sum(conn.closed for conn in created) == 1
    assert discovery.execute_discovery()
    assert discovery._cache.size == 9 and len(created) == 10


def test_failed_primary_does_not_evict_full_fallback_cache(monkeypatch):
    old = tuple((i, "A") for i in range(1, 10))
    discovery, created = primary_discovery(
        monkeypatch, primary_result({"A": 3, "B": 1}, old + ((10, "B"),)), failed={"node10:2135"}
    )
    assert discovery.execute_discovery()
    assert discovery._cache.size == 9 and not any(conn.closed for conn in created)
    assert discovery._cache.get().node_id in range(1, 10)


def test_full_cache_evicts_only_for_first_preferred_connection(monkeypatch):
    old = tuple((i, "A") for i in range(1, 10))
    nodes = old + ((10, "B"), (11, "B"))
    discovery, created = primary_discovery(monkeypatch, primary_result({"A": 1}, old))
    assert discovery.execute_discovery()

    resolve = discovery._resolver.context_resolve.return_value.__enter__
    resolve.return_value = primary_result({"A": 1, "B": 3}, nodes)
    assert discovery.execute_discovery()
    assert len(created) == 9 and not any(conn.closed for conn in created)

    resolve.return_value = primary_result({"A": 3, "B": 2}, nodes)
    assert discovery.execute_discovery()
    preferred = discovery._cache.get()
    assert preferred.node_id in (10, 11)
    assert discovery.execute_discovery()
    assert discovery._cache.get() is preferred
    assert len(created) == 10
    assert sum(conn.closed for conn in created) == 1


def test_primary_connection_retirement_preserves_other_address_node_affinity():
    cache = pool.ConnectionsCache()
    old, new = PrimaryConnection("old:2135", 1), PrimaryConnection("new:2135", 1)
    cache.add(old)
    cache.add(new)
    old.close()
    assert cache.get(connection.EndpointKey(None, 1)) is new


def test_driver_uses_primary_pile_preference_from_config(monkeypatch):
    from ydb import topic, table, scheme, coordination

    seen = []
    monkeypatch.setattr(pool.ConnectionPool, "__init__", lambda self, config: seen.append(config))
    for module, name in (
        (topic, "TopicClient"),
        (table, "TableClient"),
        (scheme, "SchemeClient"),
        (coordination, "CoordinationClient"),
    ):
        monkeypatch.setattr(module, name, MagicMock())
    config = driver.DriverConfig("grpc://test:2135", "/local", prefer_primary_pile=True)
    driver.Driver(config)
    assert seen[-1].prefer_primary_pile
