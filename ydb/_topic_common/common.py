import typing

from .. import operation, issues
from .._grpc.grpcwrapper.common_utils import IFromProtoWithProtoType

# Workaround for good IDE and universal for runtime
# noinspection PyUnreachableCode
if typing.TYPE_CHECKING:
    from .._grpc.v4.protos import ydb_topic_pb2, ydb_operation_pb2
else:
    from .._grpc.common.protos import ydb_topic_pb2, ydb_operation_pb2


TokenGetterFuncType = typing.Optional[typing.Callable[[], str]]


def wrap_operation(rpc_state, response_pb, driver=None):
    return operation.Operation(rpc_state, response_pb, driver)


ResultType = typing.TypeVar("ResultType", bound=IFromProtoWithProtoType)


def create_result_wrapper(result_type: typing.Type[ResultType]) -> typing.Callable[[typing.Any, typing.Any, typing.Any], ResultType]:
    def wrapper(rpc_state, response_pb, driver=None):
        issues._process_response(response_pb.operation)
        msg = result_type.empty_proto_message()
        response_pb.operation.result.Unpack(msg)
        return result_type.from_proto(msg)

    return wrapper

