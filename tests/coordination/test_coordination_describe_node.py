import ydb


def test_coordination_nodes(driver_sync: ydb.Driver):
    client = driver_sync.coordination_client
    node_path = "/local/test_node"

    try:
        client.delete_node(node_path)
    except ydb.SchemeError:
        pass

    client.create_node(node_path)

    node = client.describe_node(node_path)

    assert node.status == ydb.StatusCode.SUCCESS, f"Unexpected operation status: {node.status}"

    assert node.path.split("/")[-1] == "test_node", "Node name mismatch"


    assert node.config is not None, "Node config is missing"

    client.delete_node(node_path)
