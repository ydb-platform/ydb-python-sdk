import typing
from typing import Optional

import ydb
from ydb import _apis, issues

from .coordination_lock import CoordinationLock
from .сoordination_session import CoordinationSession


def wrapper_create_node(rpc_state, response_pb, *_args, **_kwargs):
    from .._grpc.grpcwrapper.ydb_coordination import CreateNodeResponse

    issues._process_response(response_pb.operation)
    return CreateNodeResponse.from_proto(response_pb)


def wrapper_describe_node(rpc_state, response_pb, *_args, **_kwargs):
    from .._grpc.grpcwrapper.ydb_coordination import DescribeNodeResponse

    issues._process_response(response_pb.operation)
    return DescribeNodeResponse.from_proto(response_pb)


def wrapper_delete_node(rpc_state, response_pb, *_args, **_kwargs):
    from .._grpc.grpcwrapper.ydb_coordination import DropNodeResponse

    issues._process_response(response_pb.operation)
    return DropNodeResponse.from_proto(response_pb)


class CoordinationClient:
    def __init__(self, driver: "ydb.Driver"):
        self._driver = driver

    def session(self) -> "CoordinationSession":
        return CoordinationSession(self._driver)

    def _call_node(
            self,
            request,
            rpc_method,
            wrapper_fn,
            settings: Optional["ydb.BaseRequestSettings"] = None,
    ):
        return self._driver(
            request,
            _apis.CoordinationService.Stub,
            rpc_method,
            wrap_result=wrapper_fn,
            wrap_args=(),
            settings=settings,
        )

    def create_node(
            self,
            path: str,
            config: typing.Optional[typing.Any] = None,
            operation_params: typing.Optional[typing.Any] = None,
            settings: Optional["ydb.BaseRequestSettings"] = None,
    ) -> _apis.ydb_coordination.CreateNodeResponse:
        request = _apis.ydb_coordination.CreateNodeRequest(
            path=path,
            config=config,
            operation_params=operation_params,
        )
        return self._call_node(
            request,
            _apis.CoordinationService.CreateNode,
            wrapper_create_node,
            settings,
        )

    def describe_node(
        self,
        path: str,
        operation_params: typing.Optional[typing.Any] = None,
        settings: Optional["ydb.BaseRequestSettings"] = None,
    ) -> _apis.ydb_coordination.DescribeNodeResponse:
        request = _apis.ydb_coordination.DescribeNodeRequest(
            path=path,
            operation_params=operation_params,
        )
        return self._call_node(
            request,
            _apis.CoordinationService.DescribeNode,
            wrapper_describe_node,
            settings,
        )

    def delete_node(
            self,
            path: str,
            operation_params: typing.Optional[typing.Any] = None,
            settings: Optional["ydb.BaseRequestSettings"] = None,
    ) -> _apis.ydb_coordination.DropNodeResponse:
        request = _apis.ydb_coordination.DropNodeRequest(
            path=path,
            operation_params=operation_params,
        )
        return self._call_node(
            request,
            _apis.CoordinationService.DropNode,
            wrapper_delete_node,
            settings,
        )

    def lock(
        self,
        path: str,
        timeout: int = 5000,
        count: int = 1,
    ) -> "CoordinationLock":
        return CoordinationLock(self.session(), path, timeout, count)
