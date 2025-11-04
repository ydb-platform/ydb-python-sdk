import typing
from typing import Optional

from ydb import _apis, issues
from ydb._grpc.grpcwrapper.ydb_coordination_public_types import NodeConfig, NodeDescription


def wrapper_create_node(rpc_state, response_pb, client: "BaseCoordinationClient"):
    issues._process_response(response_pb.operation)


def wrapper_describe_node(rpc_state, response_pb, client: "BaseCoordinationClient", path: str) -> NodeDescription:
    issues._process_response(response_pb.operation)
    return NodeDescription.from_proto(path, response_pb)


def wrapper_delete_node(rpc_state, response_pb, client: "BaseCoordinationClient"):
    issues._process_response(response_pb.operation)


def wrapper_alter_node(rpc_state, response_pb, client: "BaseCoordinationClient"):
    issues._process_response(response_pb.operation)


class BaseCoordinationClient:
    def __init__(self, driver):
        self._driver = driver

    def _call_create(self, request, settings=None, wrap_args=None):
        return self._driver(
            request,
            _apis.CoordinationService.Stub,
            _apis.CoordinationService.CreateNode,
            wrap_result=wrapper_create_node,
            wrap_args=wrap_args,
            settings=settings,
        )

    def _call_describe(self, request, settings=None, wrap_args=None):
        return self._driver(
            request,
            _apis.CoordinationService.Stub,
            _apis.CoordinationService.DescribeNode,
            wrap_result=wrapper_describe_node,
            wrap_args=wrap_args,
            settings=settings,
        )

    def _call_alter(self, request, settings=None, wrap_args=None):
        return self._driver(
            request,
            _apis.CoordinationService.Stub,
            _apis.CoordinationService.AlterNode,
            wrap_result=wrapper_alter_node,
            wrap_args=wrap_args,
            settings=settings,
        )

    def _call_delete(self, request, settings=None, wrap_args=None):
        return self._driver(
            request,
            _apis.CoordinationService.Stub,
            _apis.CoordinationService.DropNode,
            wrap_result=wrapper_delete_node,
            wrap_args=wrap_args,
            settings=settings,
        )
