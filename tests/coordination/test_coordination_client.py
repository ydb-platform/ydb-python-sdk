import asyncio

import pytest

import ydb
from ydb import aio, StatusCode

from ydb.coordination import (
    NodeConfig,
    ConsistencyMode,
    RateLimiterCountersMode,
    CoordinationClient,
)


class TestCoordination:
    def test_coordination_node_lifecycle(self, driver_sync: ydb.Driver):
        client = CoordinationClient(driver_sync)
        node_path = "/local/test_node_lifecycle"

        try:
            client.delete_node(node_path)
        except ydb.SchemeError:
            pass

        with pytest.raises(ydb.SchemeError):
            client.describe_node(node_path)

        initial_config = NodeConfig(
            session_grace_period_millis=1000,
            attach_consistency_mode=ConsistencyMode.STRICT,
            read_consistency_mode=ConsistencyMode.STRICT,
            rate_limiter_counters_mode=RateLimiterCountersMode.UNSET,
            self_check_period_millis=0,
        )
        client.create_node(node_path, initial_config)

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

    async def test_coordination_node_lifecycle_async(self, aio_connection):
        client = aio.CoordinationClient(aio_connection)
        node_path = "/local/test_node_lifecycle"

        try:
            await client.delete_node(node_path)
        except ydb.SchemeError:
            pass

        with pytest.raises(ydb.SchemeError):
            await client.describe_node(node_path)

        initial_config = NodeConfig(
            session_grace_period_millis=1000,
            attach_consistency_mode=ConsistencyMode.STRICT,
            read_consistency_mode=ConsistencyMode.STRICT,
            rate_limiter_counters_mode=RateLimiterCountersMode.UNSET,
            self_check_period_millis=0,
        )
        await client.create_node(node_path, initial_config)

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

    async def test_coordination_lock_full_lifecycle(self, aio_connection):
        client = aio.CoordinationClient(aio_connection)

        node_path = "/local/test_lock_full_lifecycle"

        try:
            await client.delete_node(node_path)
        except ydb.SchemeError:
            pass

        await client.create_node(
            node_path,
            NodeConfig(
                session_grace_period_millis=1000,
                attach_consistency_mode=ConsistencyMode.STRICT,
                read_consistency_mode=ConsistencyMode.STRICT,
                rate_limiter_counters_mode=RateLimiterCountersMode.UNSET,
                self_check_period_millis=0,
            ),
        )

        lock = client.lock("test_lock", node_path)

        create_resp = await lock.create(init_limit=1, init_data=b"init-data")
        assert create_resp.status == StatusCode.SUCCESS

        describe_resp = await lock.describe()
        assert describe_resp.status == StatusCode.SUCCESS

        sem = describe_resp.semaphore_description
        assert sem.name == "test_lock"
        assert sem.data == b"init-data"
        assert sem.count == 0
        assert sem.ephemeral is False
        assert list(sem.owners) == []
        assert list(sem.waiters) == []

        update_resp = await lock.update(new_data=b"updated-data")
        assert update_resp.status == StatusCode.SUCCESS

        describe_resp2 = await lock.describe()
        assert describe_resp2.status == StatusCode.SUCCESS

        sem2 = describe_resp2.semaphore_description
        assert sem2.name == "test_lock"
        assert sem2.data == b"updated-data"
        assert sem2.count == 0
        assert sem2.ephemeral is False
        assert list(sem2.owners) == []
        assert list(sem2.waiters) == []

        lock2_started = asyncio.Event()
        lock2_acquired = asyncio.Event()

        async def second_lock_task():
            lock2_started.set()
            async with client.lock("test_lock", node_path):
                lock2_acquired.set()
                await asyncio.sleep(0.5)

        async with client.lock("test_lock", node_path) as lock1:
            assert lock1._stream is not None
            assert lock1._stream.session_id is not None

            resp = await lock1.describe()
            assert resp.status == StatusCode.SUCCESS

            sem_under_lock = resp.semaphore_description
            assert sem_under_lock.name == "test_lock"
            assert sem_under_lock.data == b"updated-data"
            assert sem_under_lock.count == 1
            assert sem_under_lock.ephemeral is False
            assert len(list(sem_under_lock.owners)) == 1
            assert list(sem_under_lock.waiters) == []

            t2 = asyncio.create_task(second_lock_task())
            await lock2_started.wait()

            await asyncio.sleep(0.5)

            assert lock1._stream is not None

        await asyncio.wait_for(lock2_acquired.wait(), timeout=5)
        await asyncio.wait_for(t2, timeout=5)

        async with client.lock("test_lock", node_path) as lock3:
            assert lock3._stream is not None
            assert lock3._stream.session_id is not None

            resp3 = await lock3.describe()
            assert resp3.status == StatusCode.SUCCESS
            sem3 = resp3.semaphore_description
            assert sem3.count == 1

        delete_resp = await lock.delete()
        assert delete_resp.status == StatusCode.SUCCESS

        describe_after_delete = await lock.describe()
        assert describe_after_delete.status == StatusCode.NOT_FOUND
