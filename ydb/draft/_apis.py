# -*- coding: utf-8 -*-
import typing

# Workaround for good IDE and universal for runtime
if typing.TYPE_CHECKING:
    from .._grpc.v4.draft import (
        ydb_dynamic_config_v1_pb2_grpc,
    )

    from .._grpc.v4.draft.protos import (
        ydb_dynamic_config_pb2,
    )
else:
    from .._grpc.common.draft import (
        ydb_dynamic_config_v1_pb2_grpc,
    )

    try:
        from .._grpc.common.draft.protos import (
            ydb_dynamic_config_pb2,
        )
    except ImportError:
        from .._grpc.common.protos.draft import (
            ydb_dynamic_config_pb2,
        )


ydb_dynamic_config = ydb_dynamic_config_pb2


class DynamicConfigService(object):
    Stub = ydb_dynamic_config_v1_pb2_grpc.DynamicConfigServiceStub

    ReplaceConfig = "ReplaceConfig"
    SetConfig = "SetConfig"
    GetConfig = "GetConfig"
    GetNodeLabels = "GetNodeLabels"
