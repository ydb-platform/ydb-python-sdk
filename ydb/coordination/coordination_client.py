import typing
from typing import Optional

from ydb import _apis, issues


from .operations import DescribeNodeOperation, CreateNodeOperation, DropNodeOperation, AlterNodeOperation

if typing.TYPE_CHECKING:
    import ydb


def wrapper_create_node(rpc_state, response_pb, path, *_args, **_kwargs):
    issues._process_response(response_pb.operation)
    return CreateNodeOperation(rpc_state, response_pb, path)


def wrapper_describe_node(rpc_state, response_pb, *_args, **_kwargs):
    issues._process_response(response_pb.operation)
    return DescribeNodeOperation(rpc_state, response_pb)


def wrapper_delete_node(rpc_state, response_pb, path, *_args, **_kwargs):
    issues._process_response(response_pb.operation)
    return DropNodeOperation(rpc_state, response_pb, path)

def wrapper_alter_node(rpc_state, response_pb, path, *_args, **_kwargs):
    issues._process_response(response_pb.operation)
    return AlterNodeOperation(rpc_state, response_pb, path)


class CoordinationClient:
    def __init__(self, driver: "ydb.Driver"):
        self._driver = driver

    def _call_node(
            self,
            request,
            rpc_method,
            wrapper_fn,
            wrap_args=(),
            settings: Optional["ydb.BaseRequestSettings"] = None,
    ):
        return self._driver(
            request,
            _apis.CoordinationService.Stub,
            rpc_method,
            wrap_result=wrapper_fn,
            wrap_args=wrap_args,
            settings=settings,
        )

    def create_node(
            self,
            path: str,
            config: typing.Optional[typing.Any] = None,
            operation_params: typing.Optional[typing.Any] = None,
            settings: Optional["ydb.BaseRequestSettings"] = None,
    ) -> CreateNodeOperation:
        request = _apis.ydb_coordination.CreateNodeRequest(
            path=path,
            config=config,
            operation_params=operation_params,
        )
        return self._call_node(
            request,
            _apis.CoordinationService.CreateNode,
            wrapper_create_node,
            wrap_args=(path,),
            settings=settings,
        )

    def describe_node(
        self,
        path: str,
        operation_params: typing.Optional[typing.Any] = None,
        settings: Optional["ydb.BaseRequestSettings"] = None,
    ) -> DescribeNodeOperation:
        request = _apis.ydb_coordination.DescribeNodeRequest(
            path=path,
            operation_params=operation_params,
        )
        return self._call_node(
            request,
            _apis.CoordinationService.DescribeNode,
            wrapper_describe_node,
            wrap_args=(path,),
            settings=settings,
        )

    def delete_node(
            self,
            path: str,
            operation_params: typing.Optional[typing.Any] = None,
            settings: Optional["ydb.BaseRequestSettings"] = None,
    ):
        request = _apis.ydb_coordination.DropNodeRequest(
            path=path,
            operation_params=operation_params,
        )
        return self._call_node(
            request,
            _apis.CoordinationService.DropNode,
            wrapper_delete_node,
            wrap_args=(path,),
            settings=settings,
        )

    def alter_node(
            self,
            path: str,
            new_config: typing.Optional[typing.Any] = None,
            operation_params: typing.Optional[typing.Any] = None,
            settings: Optional["ydb.BaseRequestSettings"] = None,
    ):
        """
        Alter node configuration.
        """
        request = _apis.ydb_coordination.AlterNodeRequest(
            path=path,
            config=new_config,
            operation_params=operation_params,
        )

        return self._call_node(
            request,
            _apis.CoordinationService.AlterNode,
            wrapper_alter_node,
            wrap_args=(path,),
            settings=settings,
        )

    def close(self):
        pass

