import ydb
from ydb._grpc.v4.protos import ydb_coordination_pb2


def test_coordination_nodes(driver_sync: ydb.Driver):
    client = driver_sync.coordination_client
    node_path = "/local/test_node"

    try:
        drop_res = client.delete_node(node_path)
        print(f"Node deleted (pre-clean), operation id: {drop_res.operation.id}")
    except ydb.SchemeError:
        pass

    create_res = client.create_node(node_path)
    assert create_res.operation.id is not None
    print(f"Node created, operation id: {create_res.operation.id}")

    describe_res = client.describe_node(node_path)
    assert describe_res.operation.id is not None
    print(f"Node described, operation id: {describe_res.operation.id}")

    describe_result_proto = ydb_coordination_pb2.DescribeNodeResult()
    describe_res.operation.result.Unpack(describe_result_proto)

    print(f"Node path: {describe_result_proto.path}")
    if describe_result_proto.HasField("config"):
        print(f"Node config: {describe_result_proto.config}")

    # --- Удаляем узел ---
    drop_res = client.delete_node(node_path)
    assert drop_res.operation.id is not None
    print(f"Node deleted, operation id: {drop_res.operation.id}")
