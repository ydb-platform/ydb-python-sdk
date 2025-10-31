import typing
from typing import Optional

from ydb import _apis, issues
from ydb._grpc.grpcwrapper.ydb_coordination_public_types import NodeConfig, NodeDescription, CoordinationClientSettings

if typing.TYPE_CHECKING:
    import ydb


class CoordinationClient:
    def __init__(self, driver: "ydb.Driver"):
        self._driver = driver

    def create_node(
        self,
        path: str,
        config: Optional[NodeConfig] = None,
        settings: Optional[CoordinationClientSettings] = None,
    ):
        proto_config = config.to_proto() if config else None
        base_driver_settings = settings.to_base_request_settings() if settings is not None else None
        request = _apis.ydb_coordination.CreateNodeRequest(
            path=path,
            config=proto_config,
        )

        response = self._driver(
            request,
            _apis.CoordinationService.Stub,
            _apis.CoordinationService.CreateNode,
            settings=base_driver_settings,
        )
        issues._process_response(response.operation)
        return response

    def describe_node(
        self,
        path: str,
        settings: Optional[CoordinationClientSettings] = None,
    ) -> NodeDescription:
        request = _apis.ydb_coordination.DescribeNodeRequest(path=path)
        base_driver_settings = settings.to_base_request_settings() if settings is not None else None
        response = self._driver(
            request,
            _apis.CoordinationService.Stub,
            _apis.CoordinationService.DescribeNode,
            settings=base_driver_settings,
        )
        issues._process_response(response.operation)

        result = _apis.ydb_coordination.DescribeNodeResult()
        response.operation.result.Unpack(result)

        return NodeDescription(
            path=path,
            config=NodeConfig.from_proto(result.config),
        )

    def delete_node(
        self,
        path: str,
        settings: Optional[CoordinationClientSettings] = None,
    ):
        base_driver_settings = settings.to_base_request_settings() if settings is not None else None
        request = _apis.ydb_coordination.DropNodeRequest(path=path)
        response = self._driver(
            request,
            _apis.CoordinationService.Stub,
            _apis.CoordinationService.DropNode,
            settings=base_driver_settings,
        )
        issues._process_response(response.operation)
        return response

    def alter_node(
        self,
        path: str,
        new_config: NodeConfig,
        settings: Optional[CoordinationClientSettings] = None,
    ):
        proto_config = new_config.to_proto() if new_config else None
        base_driver_settings = settings.to_base_request_settings() if settings is not None else None

        request = _apis.ydb_coordination.AlterNodeRequest(
            path=path,
            config=proto_config,
        )

        response = self._driver(
            request,
            _apis.CoordinationService.Stub,
            _apis.CoordinationService.AlterNode,
            settings=base_driver_settings,
        )
        issues._process_response(response.operation)
        return response

    def close(self):
        pass
