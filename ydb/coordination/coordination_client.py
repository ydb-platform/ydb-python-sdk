import typing
from typing import Optional

from ydb import _apis, issues
from ydb._grpc.grpcwrapper.ydb_coordination_public_types import NodeConfig

if typing.TYPE_CHECKING:
    import ydb


class CoordinationClient:
    def __init__(self, driver: "ydb.Driver"):
        self._driver = driver

    def _call_node(
        self,
        request,
        rpc_method,
        settings: Optional["ydb.BaseRequestSettings"] = None,
    ):
        response = self._driver(
            request,
            _apis.CoordinationService.Stub,
            rpc_method,
            settings=settings,
        )
        issues._process_response(response.operation)
        return response

    def create_node(
        self,
        path: str,
        config: Optional[_apis.ydb_coordination.Config] = None,
        settings: Optional["ydb.BaseRequestSettings"] = None,
    ):
        request = _apis.ydb_coordination.CreateNodeRequest(
            path=path,
            config=config,
        )
        self._call_node(request, _apis.CoordinationService.CreateNode, settings)

    def describe_node(
        self,
        path: str,
        settings: Optional["_apis.ydb_coordination.Config"] = None,
    ) -> Optional[NodeConfig]:
        request = _apis.ydb_coordination.DescribeNodeRequest(path=path)
        response = self._call_node(request, _apis.CoordinationService.DescribeNode, settings)
        result = _apis.ydb_coordination.DescribeNodeResult()
        response.operation.result.Unpack(result)
        result.config.path = path
        return NodeConfig.from_proto(result.config)

    def delete_node(
        self,
        path: str,
        settings: Optional["ydb.BaseRequestSettings"] = None,
    ):
        request = _apis.ydb_coordination.DropNodeRequest(path=path)
        self._call_node(request, _apis.CoordinationService.DropNode, settings)

    def alter_node(
        self,
        path: str,
        new_config: _apis.ydb_coordination.Config,
        settings: Optional["ydb.BaseRequestSettings"] = None,
    ):
        request = _apis.ydb_coordination.AlterNodeRequest(
            path=path,
            config=new_config,
        )
        self._call_node(request, _apis.CoordinationService.AlterNode, settings)

    def close(self):
        pass
