import pytest

import ydb
from ydb.aio.coordination import CoordinationClient as AioCoordinationClient

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
        client = AioCoordinationClient(aio_connection)
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
