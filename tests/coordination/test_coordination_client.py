import asyncio
import threading
import time

import pytest

import ydb
from ydb import aio, StatusCode, logger

from ydb.coordination import (
    NodeConfig,
    ConsistencyMode,
    RateLimiterCountersMode,
    CoordinationClient,
    CreateSemaphoreResult,
    DescribeLockResult,
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

        create_resp: CreateSemaphoreResult = await lock.create(init_limit=1, init_data=b"init-data")
        assert create_resp.status == StatusCode.SUCCESS

        describe_resp: DescribeLockResult = await lock.describe()
        assert describe_resp.status == StatusCode.SUCCESS
        assert describe_resp.name == "test_lock"
        assert describe_resp.data == b"init-data"
        assert describe_resp.count == 0
        assert describe_resp.ephemeral is False
        assert list(describe_resp.owners) == []
        assert list(describe_resp.waiters) == []

        update_resp = await lock.update(new_data=b"updated-data")
        assert update_resp.status == StatusCode.SUCCESS

        describe_resp2: DescribeLockResult = await lock.describe()
        assert describe_resp2.status == StatusCode.SUCCESS
        assert describe_resp2.name == "test_lock"
        assert describe_resp2.data == b"updated-data"
        assert describe_resp2.count == 0
        assert describe_resp2.ephemeral is False
        assert list(describe_resp2.owners) == []
        assert list(describe_resp2.waiters) == []

        lock2_started = asyncio.Event()
        lock2_acquired = asyncio.Event()

        async def second_lock_task():
            lock2_started.set()
            async with client.lock("test_lock", node_path):
                lock2_acquired.set()
                await asyncio.sleep(0.5)

        async with client.lock("test_lock", node_path) as lock1:

            resp: DescribeLockResult = await lock1.describe()
            assert resp.status == StatusCode.SUCCESS
            assert resp.name == "test_lock"
            assert resp.data == b"updated-data"
            assert resp.count == 1
            assert resp.ephemeral is False
            assert len(list(resp.owners)) == 1
            assert list(resp.waiters) == []

            t2 = asyncio.create_task(second_lock_task())
            await lock2_started.wait()

            await asyncio.sleep(0.5)

        await asyncio.wait_for(lock2_acquired.wait(), timeout=5)
        await asyncio.wait_for(t2, timeout=5)

        async with client.lock("test_lock", node_path) as lock3:

            resp3: DescribeLockResult = await lock3.describe()
            assert resp3.status == StatusCode.SUCCESS
            assert resp3.count == 1

        delete_resp = await lock.delete()
        assert delete_resp.status == StatusCode.SUCCESS

        describe_after_delete: DescribeLockResult = await lock.describe()
        assert describe_after_delete.status == StatusCode.NOT_FOUND

    def test_coordination_lock_full_lifecycle_sync(self, driver_sync):
        client = CoordinationClient(driver_sync)
        node_path = "/local/test_lock_full_lifecycle"

        try:
            client.delete_node(node_path)
        except ydb.SchemeError:
            pass

        client.create_node(
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

        create_resp: CreateSemaphoreResult = lock.create(init_limit=1, init_data=b"init-data")
        assert create_resp.status == StatusCode.SUCCESS

        describe_resp: DescribeLockResult = lock.describe()
        assert describe_resp.status == StatusCode.SUCCESS
        assert describe_resp.data == b"init-data"

        update_resp = lock.update(new_data=b"updated-data")
        assert update_resp.status == StatusCode.SUCCESS
        assert lock.describe().data == b"updated-data"

        lock2_ready = threading.Event()
        lock2_acquired = threading.Event()
        thread_exc = {"err": None}

        def second_lock_task():
            try:
                lock2_ready.set()
                with client.lock("test_lock", node_path):
                    lock2_acquired.set()
                    logger.info("Second thread acquired lock")
            except Exception as e:
                logger.exception("second_lock_task failed")
                thread_exc["err"] = e

        t2 = threading.Thread(target=second_lock_task)

        with client.lock("test_lock", node_path) as lock1:
            resp = lock1.describe()
            assert resp.status == StatusCode.SUCCESS
            assert resp.count == 1

            t2.start()
            started = lock2_ready.wait(timeout=2.0)
            assert started, "Second thread did not signal readiness to acquire lock"

        acquired = lock2_acquired.wait(timeout=10.0)
        t2.join(timeout=5.0)

        if not acquired:
            if thread_exc["err"]:
                raise AssertionError(f"Second thread raised exception: {thread_exc['err']!r}") from thread_exc["err"]
            else:
                raise AssertionError("Second thread did not acquire the lock in time. Check logs for details.")

        assert not t2.is_alive(), "Second thread did not finish after acquiring lock"

        with client.lock("test_lock", node_path) as lock3:
            resp3: DescribeLockResult = lock3.describe()
            assert resp3.status == StatusCode.SUCCESS
            assert resp3.count == 1

        delete_resp = lock.delete()
        assert delete_resp.status == StatusCode.SUCCESS
        time.sleep(0.1)
        describe_after_delete: DescribeLockResult = lock.describe()
        assert describe_after_delete.status == StatusCode.NOT_FOUND
