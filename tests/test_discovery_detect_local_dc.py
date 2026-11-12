# -*- coding: utf-8 -*-
from unittest.mock import Mock, MagicMock, patch
from ydb import driver, pool, _utilities, connection
from ydb import _apis, resolver


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


def test_primary_promoted_synchronized_and_unknown_fallback(monkeypatch):
    result = primary_result({"A": 1, "B": 2, "C": 3, "D": 99}, ((1, "A"), (2, "B"), (3, "C"), (4, "D"), (5, "missing")))
    discovery, _ = primary_discovery(monkeypatch, result)
    assert discovery.execute_discovery()
    assert {discovery._cache.get().node_id for _ in range(10)} == {1, 2}
    discovery._cache.get(connection.EndpointKey("node1:2135", 1)).close()
    discovery._cache.get(connection.EndpointKey("node2:2135", 2)).close()
    assert discovery._cache.get().node_id == 3
    discovery._cache.get().close()
    assert {discovery._cache.get().node_id for _ in range(10)} == {4, 5}


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


def test_primary_cache_retains_synchronized_fallback(monkeypatch):
    nodes = tuple((i, "A") for i in range(1, 11)) + ((11, "B"),)
    discovery, _ = primary_discovery(monkeypatch, primary_result({"A": 1, "B": 3}, nodes))
    assert discovery.execute_discovery()
    assert discovery._cache.size == 9
    assert discovery._cache.already_exists("node11:2135")
    for conn in discovery._cache.values():
        if conn.node_id != 11:
            conn.close()
    assert discovery._cache.get().node_id == 11


def test_primary_connection_retirement_preserves_other_address_node_affinity():
    cache = pool.ConnectionsCache()
    old, new = PrimaryConnection("old:2135", 1), PrimaryConnection("new:2135", 1)
    cache.add(old)
    cache.add(new)
    old.close()
    assert cache.get(connection.EndpointKey(None, 1)) is new


def test_primary_driver_keyword_and_config_override(monkeypatch):
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
    driver.Driver(endpoint="grpc://test:2135", database="/local", prefer_primary_pile=True)
    assert seen[-1].prefer_primary_pile
    config = driver.DriverConfig("grpc://test:2135", "/local", prefer_primary_pile=True)
    driver.Driver(config)
    assert seen[-1].prefer_primary_pile
    driver.Driver(config, prefer_primary_pile=False)
    assert not seen[-1].prefer_primary_pile


def slo_observations():
    from datetime import datetime, timezone
    from tests.slo.bridge.checks import MODES

    base = datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp()
    log, events = [], []

    def marker(second, text):
        when = datetime.fromtimestamp(base + second, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        log.append(f"[{when}] {text}")

    marker(0, "PRIMARY_FALLBACK_BEGIN pile-1")
    marker(20, "PRIMARY_FALLBACK_END pile-1")
    for mode in MODES:
        events.append(
            {
                "event": "session_created",
                "mode": mode,
                "ts": base + 10,
                "stable": True,
                "fallback": True,
                "primary": "pile-1",
                "pile": "pile-2",
            }
        )
    for name, start, pile in (("initial", 30, "pile-1"), ("switched", 200, "pile-2"), ("restored", 370, "pile-1")):
        marker(start, f"PRIMARY_WINDOW_BEGIN {name} {pile}")
        marker(start + 160, f"PRIMARY_WINDOW_END {name} {pile}")
        for mode in MODES:
            for offset in (140, 145, 150):
                events.append(
                    {
                        "event": "session_created",
                        "mode": mode,
                        "ts": base + start + offset,
                        "stable": True,
                        "both_piles_visible": True,
                        "primary": pile,
                        "pile": pile,
                    }
                )
                events.append({"event": "operation", "mode": mode, "ts": base + start + offset, "ok": True})
        for control_pile in ("pile-1", "pile-2"):
            events.append(
                {
                    "event": "session_created",
                    "mode": "control-table",
                    "ts": base + start + 145,
                    "stable": True,
                    "both_piles_visible": True,
                    "primary": pile,
                    "pile": control_pile,
                }
            )
    for second in (540, 650, 760, 870, 980):
        marker(second, "Recovered: scenario (restored)")
        for mode in MODES:
            for offset in (1, 2, 3):
                events.append({"event": "operation", "mode": mode, "ts": base + second + offset, "ok": True})
    for mode in MODES:
        for second in (1090, 1091, 1092):
            events.append({"event": "operation", "mode": mode, "ts": base + second, "ok": True})
    return "\n".join(log), events, base + 1100


def test_live_primary_slo_acceptance_and_wrong_pile_rejection():
    from tests.slo.bridge.checks import check_routing

    log, events, stopped_at = slo_observations()
    assert not check_routing(log, events, stopped_at)[1]
    sample = next(row for row in events if row.get("both_piles_visible") and row["mode"] == "sync-table")
    sample["pile"] = "pile-2"
    assert any("sync-table" in error for error in check_routing(log, events, stopped_at)[1])


def test_live_primary_slo_requires_control_and_all_modes():
    from tests.slo.bridge.checks import check_routing

    log, events, stopped_at = slo_observations()
    events = [row for row in events if row["mode"] != "control-table"]
    assert any("control" in error for error in check_routing(log, events, stopped_at)[1])
    events = [row for row in events if row["mode"] != "async-query"]
    assert any(
        "async-query" in error or "Some probe modes" in error for error in check_routing(log, events, stopped_at)[1]
    )


def test_live_primary_slo_independent_audit_and_docker_evidence():
    from tests.slo.bridge.checks import audit_rows, check_node_events

    probe = {"table": "primary_probe_abc", "modes": {"sync-table": {"confirmed": [1, 2]}}}
    rows = [{"mode": "sync-table", "seq": seq, "payload": f"primary_probe_abc:sync-table:{seq}"} for seq in (1, 2)]
    assert not audit_rows(probe, rows)
    rows[1]["payload"] = "corrupted"
    assert audit_rows(probe, rows) == [{"mode": "sync-table", "seq": 2}]
    log, _, stopped_at = slo_observations()
    base = stopped_at - 1100
    stop = {"time": base + 5, "Action": "stop", "Actor": {"Attributes": {"ydb.node.location.pile": "pile-1"}}}
    assert not check_node_events(log, [stop])
    assert check_node_events(log, [stop, {"time": base + 250, "Action": "start"}])


def test_live_primary_slo_oracle_and_cli_flag():
    from tests.slo.src.bridge_observer import route_observation
    from tests.slo.src.options import get_root_parser

    before = {"states": {"pile-1": 1, "pile-2": 3}, "primary": "pile-1", "node_piles": {"1": "pile-1", "2": "pile-2"}}
    assert route_observation(1, before, before)["stable"]
    assert route_observation(2, before, before)["fallback"]
    assert not route_observation(1, before, {**before, "primary": "pile-2"})["stable"]
    args = get_root_parser().parse_args(["table-run", "grpc://host:2136", "/Root/testdb", "--prefer-primary-pile"])
    assert args.prefer_primary_pile
