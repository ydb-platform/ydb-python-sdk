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

    alter_res = client.alter_node(node_path, new_config)

    assert alter_res.status == ydb.StatusCode.SUCCESS, f"Alter operation failed: {alter_res.status}"


    node = client.describe_node(node_path)
    assert node.config.session_grace_period_millis == 12345, "Session grace period not updated"
    assert node.config.attach_consistency_mode == _apis.ydb_coordination.ConsistencyMode.CONSISTENCY_MODE_STRICT, \
        "Attach consistency mode not updated"
    assert node.config.read_consistency_mode == _apis.ydb_coordination.ConsistencyMode.CONSISTENCY_MODE_RELAXED, \
        "Read consistency mode not updated"

    client.delete_node(node_path)
