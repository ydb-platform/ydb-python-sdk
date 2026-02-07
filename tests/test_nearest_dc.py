import time
import pytest
from ydb import nearest_dc


class MockEndpoint:
    def __init__(self, address, port, location):
        self.address = address
        self.port = port
        self.endpoint = f"{address}:{port}"
        self.location = location


class DummySock:
    def close(self):
        pass


def test_check_fastest_endpoint_empty():
    assert nearest_dc._check_fastest_endpoint([]) is None


def test_check_fastest_endpoint_all_fail(monkeypatch):
    def fake_create_connection(addr_port, timeout=None):
        raise OSError("connect failed")

    monkeypatch.setattr(nearest_dc.socket, "create_connection", fake_create_connection)

    endpoints = [
        MockEndpoint("a", 1, "dc1"),
        MockEndpoint("b", 1, "dc2"),
    ]
    assert nearest_dc._check_fastest_endpoint(endpoints, timeout=0.05) is None


def test_check_fastest_endpoint_fastest_wins(monkeypatch):
    def fake_create_connection(addr_port, timeout=None):
        host, _ = addr_port
        if host == "slow":
            time.sleep(0.05)
        return DummySock()

    monkeypatch.setattr(nearest_dc.socket, "create_connection", fake_create_connection)

    endpoints = [
        MockEndpoint("slow", 1, "dc_slow"),
        MockEndpoint("fast", 1, "dc_fast"),
    ]
    winner = nearest_dc._check_fastest_endpoint(endpoints, timeout=0.2)
    assert winner is not None
    assert winner.location == "dc_fast"


def test_check_fastest_endpoint_respects_main_timeout(monkeypatch):
    def fake_create_connection(addr_port, timeout=None):
        time.sleep(0.2)
        return DummySock()

    monkeypatch.setattr(nearest_dc.socket, "create_connection", fake_create_connection)

    endpoints = [
        MockEndpoint("hang1", 1, "dc1"),
        MockEndpoint("hang2", 1, "dc2"),
    ]

    winner = nearest_dc._check_fastest_endpoint(endpoints, timeout=0.05)

    assert winner is None


def test_detect_local_dc_empty_endpoints():
    with pytest.raises(ValueError, match="Empty endpoints"):
        nearest_dc.detect_local_dc([])


def test_detect_local_dc_single_location_returns_immediately(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("create_connection should not be called for single location")

    monkeypatch.setattr(nearest_dc.socket, "create_connection", fail_if_called)

    endpoints = [
        MockEndpoint("h1", 1, "dc1"),
        MockEndpoint("h2", 1, "dc1"),
    ]
    assert nearest_dc.detect_local_dc(endpoints) == "dc1"


def test_detect_local_dc_returns_none_when_all_fail(monkeypatch):
    def fake_create_connection(addr_port, timeout=None):
        raise OSError("connect failed")

    monkeypatch.setattr(nearest_dc.socket, "create_connection", fake_create_connection)

    endpoints = [
        MockEndpoint("bad1", 9999, "dc1"),
        MockEndpoint("bad2", 9999, "dc2"),
    ]
    assert nearest_dc.detect_local_dc(endpoints, timeout=0.05) is None


def test_detect_local_dc_returns_location_of_fastest(monkeypatch):
    def fake_create_connection(addr_port, timeout=None):
        host, _ = addr_port
        if host == "dc1_host":
            time.sleep(0.05)
        return DummySock()

    monkeypatch.setattr(nearest_dc.socket, "create_connection", fake_create_connection)

    endpoints = [
        MockEndpoint("dc1_host", 1, "dc1"),
        MockEndpoint("dc2_host", 1, "dc2"),
    ]
    assert nearest_dc.detect_local_dc(endpoints, max_per_location=5, timeout=0.2) == "dc2"


def test_detect_local_dc_respects_max_per_location(monkeypatch):
    calls = []

    def fake_create_connection(addr_port, timeout=None):
        calls.append(addr_port)
        raise OSError("connect failed")

    monkeypatch.setattr(nearest_dc.socket, "create_connection", fake_create_connection)

    endpoints = [MockEndpoint(f"dc1_{i}", 1, "dc1") for i in range(5)] + [
        MockEndpoint(f"dc2_{i}", 1, "dc2") for i in range(5)
    ]
    nearest_dc.detect_local_dc(endpoints, max_per_location=2, timeout=0.2)

    assert len(calls) == 4
