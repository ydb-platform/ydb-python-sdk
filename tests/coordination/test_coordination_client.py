import asyncio
import threading
import time

import pytest

import ydb
from ydb.aio.coordination import CoordinationClient as AioCoordinationClient
from ydb import StatusCode, logger

from ydb.coordination import (
    NodeConfig,
    ConsistencyMode,
    RateLimiterCountersMode,
    CoordinationClient,
    CreateSemaphoreResult,
    DescribeLockResult,
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
        client, node_path, config = async_coordination_node

        lock = client.lock("test_lock", node_path)

        create = await lock.create(init_limit=1, init_data=b"hello")
        assert create.status == StatusCode.SUCCESS

        desc = await lock.describe()
        assert desc.status == StatusCode.SUCCESS
        assert desc.name == "test_lock"
        assert desc.data == b"hello"
        assert desc.count == 0
        assert desc.ephemeral is False
        assert list(desc.owners) == []
        assert list(desc.waiters) == []

        upd = await lock.update(new_data=b"world")
        assert upd.status == StatusCode.SUCCESS

        desc2 = await lock.describe()
        assert desc2.status == StatusCode.SUCCESS
        assert desc2.name == "test_lock"
        assert desc2.data == b"world"
        assert desc2.count == 0
        assert desc2.ephemeral is False
        assert list(desc2.owners) == []
        assert list(desc2.waiters) == []

        delete = await lock.delete()
        assert delete.status == StatusCode.SUCCESS

        desc_after = await lock.describe()
        assert desc_after.status == StatusCode.NOT_FOUND

    def test_coordination_lock_describe_full_sync(self, sync_coordination_node):
        client, node_path, config = sync_coordination_node

        lock = client.lock("test_lock", node_path)

        create = lock.create(init_limit=1, init_data=b"hello")
        assert create.status == StatusCode.SUCCESS

        desc = lock.describe()
        assert desc.status == StatusCode.SUCCESS
        assert desc.name == "test_lock"
        assert desc.data == b"hello"
        assert desc.count == 0
        assert desc.ephemeral is False
        assert list(desc.owners) == []
        assert list(desc.waiters) == []
        upd = lock.update(new_data=b"world")
        assert upd.status == StatusCode.SUCCESS

        desc2 = lock.describe()
        assert desc2.status == StatusCode.SUCCESS
        assert desc2.name == "test_lock"
        assert desc2.data == b"world"
        assert desc2.count == 0
        assert desc2.ephemeral is False
        assert list(desc2.owners) == []
        assert list(desc2.waiters) == []

        delete = lock.delete()
        assert delete.status == StatusCode.SUCCESS

        desc_after = lock.describe()
        assert desc_after.status == StatusCode.NOT_FOUND

    async def test_coordination_lock_racing_async(self, async_coordination_node):
        client, node_path, initial_config = async_coordination_node
        small_timeout = 0.5

        lock = client.lock("test_lock", node_path)

        await lock.create(init_limit=1, init_data=b"init-data")

        describe_resp: DescribeLockResult = await lock.describe()
        assert describe_resp.status == StatusCode.SUCCESS

        lock2_started = asyncio.Event()
        lock2_acquired = asyncio.Event()

        async def second_lock_task():
            lock2_started.set()
            async with client.lock("test_lock", node_path):
                lock2_acquired.set()
                await asyncio.sleep(small_timeout)

        async with client.lock("test_lock", node_path) as lock1:

            resp: DescribeLockResult = await lock1.describe()
            assert resp.status == StatusCode.SUCCESS

            t2 = asyncio.create_task(second_lock_task())
            await lock2_started.wait()

            await asyncio.sleep(small_timeout)

        await asyncio.wait_for(lock2_acquired.wait(), timeout=small_timeout)
        await asyncio.wait_for(t2, timeout=small_timeout)

        delete_resp = await lock.delete()
        assert delete_resp.status == StatusCode.SUCCESS

        describe_after_delete: DescribeLockResult = await lock.describe()
        assert describe_after_delete.status == StatusCode.NOT_FOUND

    def test_coordination_lock_racing_sync(self, sync_coordination_node):
        client, node_path, initial_config = sync_coordination_node
        small_timeout = 0.5

        lock = client.lock("test_lock", node_path)

        create_resp: CreateSemaphoreResult = lock.create(init_limit=1, init_data=b"init-data")
        assert create_resp.status == StatusCode.SUCCESS

        describe_resp: DescribeLockResult = lock.describe()
        assert describe_resp.status == StatusCode.SUCCESS

        lock2_ready = threading.Event()
        lock2_acquired = threading.Event()

        def second_lock_task():
            try:
                lock2_ready.set()
                with client.lock("test_lock", node_path):
                    lock2_acquired.set()
                    logger.info("Second thread acquired lock")
            except Exception as e:
                logger.exception(f"{e} | second_lock_task failed")

        t2 = threading.Thread(target=second_lock_task)

        with client.lock("test_lock", node_path) as lock1:
            resp = lock1.describe()
            assert resp.status == StatusCode.SUCCESS
            t2.start()
            lock2_ready.wait(timeout=small_timeout)

        lock2_acquired.wait(timeout=small_timeout)
        t2.join(timeout=small_timeout)

        delete_resp = lock.delete()
        assert delete_resp.status == StatusCode.SUCCESS
        time.sleep(small_timeout)
        describe_after_delete: DescribeLockResult = lock.describe()
        assert describe_after_delete.status == StatusCode.NOT_FOUND
