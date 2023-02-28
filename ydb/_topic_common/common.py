import asyncio
import concurrent.futures
import threading
import typing
from typing import Optional

from .. import operation, issues
from .._grpc.grpcwrapper.common_utils import IFromProtoWithProtoType

TokenGetterFuncType = typing.Optional[typing.Callable[[], str]]
TimeoutType = typing.Union[int, float]


def wrap_operation(rpc_state, response_pb, driver=None):
    return operation.Operation(rpc_state, response_pb, driver)


ResultType = typing.TypeVar("ResultType", bound=IFromProtoWithProtoType)


def create_result_wrapper(
    result_type: typing.Type[ResultType],
) -> typing.Callable[[typing.Any, typing.Any, typing.Any], ResultType]:
    def wrapper(rpc_state, response_pb, driver=None):
        issues._process_response(response_pb.operation)
        msg = result_type.empty_proto_message()
        response_pb.operation.result.Unpack(msg)
        return result_type.from_proto(msg)

    return wrapper


_shared_event_loop_lock = threading.Lock()
_shared_event_loop = None  # type: Optional[asyncio.AbstractEventLoop]


def _get_shared_event_loop() -> asyncio.AbstractEventLoop:
    global _shared_event_loop

    if _shared_event_loop is not None:
        return _shared_event_loop

    with _shared_event_loop_lock:
        if _shared_event_loop is not None:
            return _shared_event_loop

        event_loop_set_done = concurrent.futures.Future()

        def start_event_loop():
            event_loop = asyncio.new_event_loop()
            event_loop_set_done.set_result(event_loop)
            asyncio.set_event_loop(event_loop)
            event_loop.run_forever()

        t = threading.Thread(
            target=start_event_loop,
            name="Common ydb topic event loop",
            daemon=True,
        )
        t.start()

        _shared_event_loop = event_loop_set_done.result()
        return _shared_event_loop
