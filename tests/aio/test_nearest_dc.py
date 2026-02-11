import asyncio
import pytest
from ydb.aio import nearest_dc


class MockEndpoint:
    def __init__(self, address, port, location):
        self.address = address
        self.port = port
        self.endpoint = f"{address}:{port}"
        self.location = location


class MockWriter:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True

    async def wait_closed(self):
        await asyncio.sleep(0)


@pytest.mark.asyncio
async def test_check_fastest_endpoint_empty():
    assert await nearest_dc._check_fastest_endpoint([]) is None


@pytest.mark.asyncio
async def test_check_fastest_endpoint_all_fail(monkeypatch):
    async def fake_open_connection(host, port):
        raise OSError("connect failed")

    monkeypatch.setattr(nearest_dc.asyncio, "open_connection", fake_open_connection)

    endpoints = [
        MockEndpoint("a", 1, "dc1"),
        MockEndpoint("b", 1, "dc2"),
    ]
    assert await nearest_dc._check_fastest_endpoint(endpoints, timeout=0.05) is None


@pytest.mark.asyncio
async def test_check_fastest_endpoint_fastest_wins(monkeypatch):
    async def fake_open_connection(host, port):
        if host == "slow":
            await asyncio.sleep(0.05)
        return None, MockWriter()

    monkeypatch.setattr(nearest_dc.asyncio, "open_connection", fake_open_connection)

    endpoints = [
        MockEndpoint("slow", 1, "dc_slow"),
        MockEndpoint("fast", 1, "dc_fast"),
    ]
    winner = await nearest_dc._check_fastest_endpoint(endpoints, timeout=0.2)
    assert winner is not None
    assert winner.location == "dc_fast"


@pytest.mark.asyncio
async def test_check_fastest_endpoint_respects_main_timeout(monkeypatch):
    async def fake_open_connection(host, port):
        await asyncio.sleep(0.2)
        return None, MockWriter()

    monkeypatch.setattr(nearest_dc.asyncio, "open_connection", fake_open_connection)

    endpoints = [
        MockEndpoint("hang1", 1, "dc1"),
        MockEndpoint("hang2", 1, "dc2"),
    ]

    winner = await nearest_dc._check_fastest_endpoint(endpoints, timeout=0.05)

    assert winner is None


@pytest.mark.asyncio
async def test_detect_local_dc_empty_endpoints():
    with pytest.raises(ValueError, match="Empty endpoints"):
        await nearest_dc.detect_local_dc([])


@pytest.mark.asyncio
async def test_detect_local_dc_single_location_returns_immediately(monkeypatch):
    async def fail_if_called(*args, **kwargs):
        raise AssertionError("open_connection should not be called for single location")

    monkeypatch.setattr(nearest_dc.asyncio, "open_connection", fail_if_called)

    endpoints = [
        MockEndpoint("h1", 1, "dc1"),
        MockEndpoint("h2", 1, "dc1"),
    ]
    assert await nearest_dc.detect_local_dc(endpoints) == "dc1"


@pytest.mark.asyncio
async def test_detect_local_dc_returns_none_when_all_fail(monkeypatch):
    async def fake_open_connection(host, port):
        raise OSError("connect failed")

    monkeypatch.setattr(nearest_dc.asyncio, "open_connection", fake_open_connection)

    endpoints = [
        MockEndpoint("bad1", 9999, "dc1"),
        MockEndpoint("bad2", 9999, "dc2"),
    ]
    assert await nearest_dc.detect_local_dc(endpoints, timeout=0.05) is None


@pytest.mark.asyncio
async def test_detect_local_dc_returns_location_of_fastest(monkeypatch):
    async def fake_open_connection(host, port):
        if host == "dc1_host":
            await asyncio.sleep(0.05)
        return None, MockWriter()

    monkeypatch.setattr(nearest_dc.asyncio, "open_connection", fake_open_connection)

    endpoints = [
        MockEndpoint("dc1_host", 1, "dc1"),
        MockEndpoint("dc2_host", 1, "dc2"),
    ]
    assert await nearest_dc.detect_local_dc(endpoints, max_per_location=5, timeout=0.2) == "dc2"


@pytest.mark.asyncio
async def test_detect_local_dc_respects_max_per_location(monkeypatch):
    calls = []

    async def fake_open_connection(host, port):
        calls.append((host, port))
        raise OSError("connect failed")

    monkeypatch.setattr(nearest_dc.asyncio, "open_connection", fake_open_connection)

    endpoints = [MockEndpoint(f"dc1_{i}", 1, "dc1") for i in range(5)] + [
        MockEndpoint(f"dc2_{i}", 1, "dc2") for i in range(5)
    ]
    await nearest_dc.detect_local_dc(endpoints, max_per_location=2, timeout=0.2)

    assert len(calls) == 4


@pytest.mark.asyncio
async def test_detect_local_dc_validates_max_per_location():
    endpoints = [MockEndpoint("h1", 1, "dc1")]
    with pytest.raises(ValueError, match="max_per_location must be >= 1"):
        await nearest_dc.detect_local_dc(endpoints, max_per_location=0)


@pytest.mark.asyncio
async def test_detect_local_dc_validates_timeout():
    endpoints = [MockEndpoint("h1", 1, "dc1")]
    with pytest.raises(ValueError, match="timeout must be > 0"):
        await nearest_dc.detect_local_dc(endpoints, timeout=0)
