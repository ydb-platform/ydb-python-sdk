import ydb
from ydb import operation

from ydb._grpc.v5.ydb_coordination_v1_pb2_grpc import CoordinationServiceStub
from ydb._grpc.v5.protos import ydb_coordination_pb2
from ydb.coordination.coordination_lock import CoordinationLock
from ydb.coordination.сoordination_session import CoordinationSession


class CoordinationClient:
    def __init__(self, driver: "ydb.Driver"):
        self._driver = driver

    def session(self):
        return CoordinationSession(self._driver)


    def create_node(self, path: str, config=None, operation_params=None):
        request = ydb_coordination_pb2.CreateNodeRequest(
            path=path,
            config=config,
            operation_params=operation_params,
        )
        return self._driver(
            request,
            CoordinationServiceStub,
            "CreateNode",
            operation.Operation,
        )

    def describe_node(self, path: str, operation_params=None):
        request = ydb_coordination_pb2.DescribeNodeRequest(
            path=path,
            operation_params=operation_params,
        )
        return self._driver(
            request,
            CoordinationServiceStub,
            "DescribeNode",
            operation.Operation,
        )

    def delete_node(self, path: str, operation_params=None):
        request = ydb_coordination_pb2.DropNodeRequest(
            path=path,
            operation_params=operation_params,
        )
        return self._driver(
            request,
            CoordinationServiceStub,
            "DropNode",
            operation.Operation,
        )

    def lock(self, path: str, timeout: int = 5000, count: int = 1):
        return CoordinationLock(self.session(), path, timeout, count)
