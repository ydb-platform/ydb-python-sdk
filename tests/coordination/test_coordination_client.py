import asyncio
import threading

import pytest

import ydb
from ydb.aio.coordination import CoordinationClient as AioCoordinationClient
from ydb import StatusCode

from ydb.coordination import (
    NodeConfig,
    ConsistencyMode,
    RateLimiterCountersMode,
    CoordinationClient,
)


@pytest.fixture
def sync_coordination_node(driver_sync):
    client = CoordinationClient(driver_sync)
    node_path = "/local/test_node"

    try:
        client.delete_node(node_path)
    except ydb.SchemeError:
        pass

    config = NodeConfig(
        session_grace_period_millis=1000,
        attach_consistency_mode=ConsistencyMode.STRICT,
        read_consistency_mode=ConsistencyMode.STRICT,
        rate_limiter_counters_mode=RateLimiterCountersMode.UNSET,
        self_check_period_millis=0,
    )
    client.create_node(node_path, config)

    yield client, node_path, config

    try:
        client.delete_node(node_path)
    except ydb.SchemeError:
        pass


@pytest.fixture
async def async_coordination_node(aio_connection):
    client = AioCoordinationClient(aio_connection)
    node_path = "/local/test_node"

    try:
        await client.delete_node(node_path)
    except ydb.SchemeError:
        pass

    config = NodeConfig(
        session_grace_period_millis=1000,
        attach_consistency_mode=ConsistencyMode.STRICT,
        read_consistency_mode=ConsistencyMode.STRICT,
        rate_limiter_counters_mode=RateLimiterCountersMode.UNSET,
        self_check_period_millis=0,
    )
    await client.create_node(node_path, config)

    yield client, node_path, config

    try:
        await client.delete_node(node_path)
    except ydb.SchemeError:
        pass


class TestCoordination:
    def test_coordination_node_lifecycle(self, sync_coordination_node):
        client, node_path, initial_config = sync_coordination_node

        node_conf = client.describe_node(node_path)
        assert node_conf == initial_config

        updated_config = NodeConfig(
            session_grace_period_millis=12345,
            attach_consistency_mode=ConsistencyMode.STRICT,
            read_consistency_mode=ConsistencyMode.RELAXED,
            rate_limiter_counters_mode=RateLimiterCountersMode.DETAILED,
            self_check_period_millis=10,
        )
        client.alter_node(node_path, updated_config)

        node_conf = client.describe_node(node_path)
        assert node_conf == updated_config

        client.delete_node(node_path)

        with pytest.raises(ydb.SchemeError):
            client.describe_node(node_path)

    async def test_coordination_node_lifecycle_async(self, async_coordination_node):
        client, node_path, initial_config = async_coordination_node

        node_conf = await client.describe_node(node_path)
        assert node_conf == initial_config

        updated_config = NodeConfig(
            session_grace_period_millis=12345,
            attach_consistency_mode=ConsistencyMode.STRICT,
            read_consistency_mode=ConsistencyMode.RELAXED,
            rate_limiter_counters_mode=RateLimiterCountersMode.DETAILED,
            self_check_period_millis=10,
        )
        await client.alter_node(node_path, updated_config)

        node_conf = await client.describe_node(node_path)
        assert node_conf == updated_config

        await client.delete_node(node_path)

        with pytest.raises(ydb.SchemeError):
            await client.describe_node(node_path)

    async def test_coordination_lock_describe_full_async(self, async_coordination_node):
        client, node_path, _ = async_coordination_node

        async with client.session(node_path) as node:
            lock = node.lock("test_lock")

            desc = await lock.describe()
            assert desc.status == StatusCode.NOT_FOUND

            async with lock:
                pass

            desc = await lock.describe()
            assert desc.data == b""

            await lock.update(new_data=b"world")

            desc2 = await lock.describe()
            assert desc2.data == b"world"

    def test_coordination_lock_describe_full(self, sync_coordination_node):
        client, node_path, _ = sync_coordination_node

        with client.session(node_path) as node:
            lock = node.lock("test_lock")

            desc = lock.describe()
            assert desc.status == StatusCode.NOT_FOUND

            with lock:
                pass

            desc = lock.describe()
            assert desc.data == b""

            lock.update(new_data=b"world")

            desc2 = lock.describe()
            assert desc2.data == b"world"

    async def test_coordination_lock_racing_async(self, async_coordination_node):
        client, node_path, _ = async_coordination_node
        timeout = 5

        async with client.session(node_path) as node:
            lock2_started = asyncio.Event()
            lock2_acquired = asyncio.Event()
            lock2_release = asyncio.Event()

            async def second_lock_task():
                lock2_started.set()
                async with node.lock("test_lock"):
                    lock2_acquired.set()
                    await lock2_release.wait()

            async with node.lock("test_lock"):
                t2 = asyncio.create_task(second_lock_task())
                await asyncio.wait_for(lock2_started.wait(), timeout=timeout)

            await asyncio.wait_for(lock2_acquired.wait(), timeout=timeout)
            lock2_release.set()
            await asyncio.wait_for(t2, timeout=timeout)

    def test_coordination_lock_racing(self, sync_coordination_node):
        client, node_path, _ = sync_coordination_node
        timeout = 5

        with client.session(node_path) as node:
            lock2_started = threading.Event()
            lock2_acquired = threading.Event()
            lock2_release = threading.Event()

            def second_lock_task():
                lock2_started.set()
                with node.lock("test_lock"):
                    lock2_acquired.set()
                    lock2_release.wait(timeout)

            with node.lock("test_lock"):
                t2 = threading.Thread(target=second_lock_task)
                t2.start()

                assert lock2_started.wait(timeout)

            assert lock2_acquired.wait(timeout)
            lock2_release.set()
            t2.join(timeout)

    async def test_coordination_reconnect_async(self, async_coordination_node):
        client, node_path, _ = async_coordination_node

        async with client.session(node_path) as node:
            lock = node.lock("test_lock")

            async with lock:
                pass

            await node._reconnector._stream.close()

            async with lock:
                pass

    async def test_same_lock_cannot_be_acquired_twice(self, async_coordination_node):
        client, node_path, _ = async_coordination_node

        async with client.session(node_path) as node:
            lock1 = node.lock("lock1")
            lock1_1 = node.lock("lock1")

            await lock1.acquire()

            acquire_task = asyncio.create_task(lock1_1.acquire())

            assert not acquire_task.done()

            await lock1.release()
            await asyncio.wait_for(acquire_task, timeout=5)
