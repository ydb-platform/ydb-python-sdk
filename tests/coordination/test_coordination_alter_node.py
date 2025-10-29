import ydb
from ydb import _apis


def test_coordination_alter_node(driver_sync: ydb.Driver):
    client = driver_sync.coordination_client
    node_path = "/local/test_alter_node"

    try:
        client.delete_node(node_path)
    except ydb.SchemeError:
        pass

    client.create_node(node_path)

    new_config = _apis.ydb_coordination.Config(
        session_grace_period_millis=12345,
        attach_consistency_mode=_apis.ydb_coordination.ConsistencyMode.CONSISTENCY_MODE_STRICT,
        read_consistency_mode=_apis.ydb_coordination.ConsistencyMode.CONSISTENCY_MODE_RELAXED,
    )


    client.alter_node(node_path, new_config)

    node_config = client.describe_node(node_path)
    assert node_config.session_grace_period_millis == 12345, "Session grace period not updated"
    assert node_config.attach_consistency_mode == _apis.ydb_coordination.ConsistencyMode.CONSISTENCY_MODE_STRICT, \
        "Attach consistency mode not updated"
    assert node_config.read_consistency_mode == _apis.ydb_coordination.ConsistencyMode.CONSISTENCY_MODE_RELAXED, \
        "Read consistency mode not updated"

    client.delete_node(node_path)
