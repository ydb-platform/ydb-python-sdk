import ydb

from ydb.coordination import (
    NodeConfig,
    ConsistencyMode,
    RateLimiterCountersMode,
    CoordinationClient
)


class TestCoordination:

    def test_coordination_alter_node(self, driver_sync: ydb.Driver):
        client = CoordinationClient(driver_sync)
        node_path = "/local/test_alter_node"

        try:
            client.delete_node(node_path)
        except ydb.SchemeError:
            pass

        client.create_node(node_path)

        new_config = NodeConfig(
            session_grace_period_millis=12345,
            attach_consistency_mode=ConsistencyMode.STRICT,
            read_consistency_mode=ConsistencyMode.RELAXED,
            rate_limiter_counters_mode=RateLimiterCountersMode.UNSET,
            self_check_period_millis=0,
        )

        client.alter_node(node_path, new_config)

        node_desc = client.describe_node(node_path)
        node_config = node_desc.config
        path = node_desc.path

        assert node_path == path
        assert node_config.session_grace_period_millis == 12345
        assert node_config.attach_consistency_mode == ConsistencyMode.STRICT
        assert node_config.read_consistency_mode == ConsistencyMode.RELAXED

        client.delete_node(node_path)

    def test_coordination_nodes(self, driver_sync: ydb.Driver):
        client = CoordinationClient(driver_sync)
        node_path = "/local/test_node"

        try:
            client.delete_node(node_path)
        except ydb.SchemeError:
            pass

        client.create_node(node_path)

        node_descr = client.describe_node(node_path)

        node_descr_path = node_descr.path

        assert node_descr_path == node_path

        client.delete_node(node_path)
