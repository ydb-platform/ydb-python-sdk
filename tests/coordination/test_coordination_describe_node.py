import ydb

def test_coordination_nodes(driver_sync: ydb.Driver):
    client = driver_sync.coordination_client
    node_path = "/local/test_node"

    try:
        client.delete_node(node_path)
    except ydb.SchemeError:
        pass

    client.create_node(node_path)

    node_config = client.describe_node(node_path)

    assert node_config.path == "/local/test_node"

    client.delete_node(node_path)
