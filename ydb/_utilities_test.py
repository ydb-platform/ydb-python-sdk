from pathlib import Path, PurePosixPath
import asyncio
from concurrent.futures import ThreadPoolExecutor
import subprocess
import sys
import tarfile
import threading
from types import SimpleNamespace
from unittest.mock import Mock
import zipfile

import grpc
import pytest

import ydb
from ydb.aio.connection import _SafeAsyncIterator
from ydb.aio.connection import Connection as AsyncConnection
from ydb.connection import Connection as SyncConnection
from ydb.connection import _rpc_error_handler

from ydb._errors import check_retriable_error
from ydb._utilities import check_module_exists
from ydb._utilities import get_first_message_with_timeout
from ydb._utilities import x_ydb_sdk_build_info_header
from .ydb_version import VERSION


@pytest.mark.parametrize(
    "path,result",
    [("sys", True), ("ydb", True), ("ydb.some.module.unexisted.test", False)],
)
def test_check_module_exists(path, result):
    assert check_module_exists(path) == result


def test_x_ydb_sdk_build_info_header():
    assert x_ydb_sdk_build_info_header(()) == ("x-ydb-sdk-build-info", "ydb-python-sdk/" + VERSION)
    assert x_ydb_sdk_build_info_header(("lib1/0.1.0",)) == (
        "x-ydb-sdk-build-info",
        "ydb-python-sdk/" + VERSION + ";lib1/0.1.0",
    )
    assert x_ydb_sdk_build_info_header(("lib1/0.1.0", "lib2/0.2.0")) == (
        "x-ydb-sdk-build-info",
        "ydb-python-sdk/" + VERSION + ";lib1/0.1.0;lib2/0.2.0",
    )


def test_get_first_message_with_timeout_returns_first_message():
    assert get_first_message_with_timeout(iter(["first", "second"]), timeout=5) == "first"


def test_get_first_message_with_timeout_reraises_stream_error():
    error = ydb.issues.Unavailable("Socket closed")

    def stream():
        raise error
        yield

    with pytest.raises(ydb.issues.Unavailable) as exc_info:
        get_first_message_with_timeout(stream(), timeout=5)
    assert exc_info.value is error


@pytest.mark.parametrize(
    "code,error,status",
    [
        (grpc.StatusCode.CANCELLED, ydb.ClientCancelled, ydb.StatusCode.CLIENT_CANCELLED),
        (grpc.StatusCode.DEADLINE_EXCEEDED, ydb.DeadlineExceed, ydb.StatusCode.DEADLINE_EXCEEDED),
    ],
)
def test_grpc_cancellation_and_deadline_have_distinct_statuses(code, error, status):
    rpc_error = Mock(spec=grpc.Call)
    rpc_error.code.return_value = code
    rpc_error.details.return_value = "transport error"

    result = _rpc_error_handler("test", rpc_error)

    assert type(result) is error
    assert result.status == status
    if error is ydb.ClientCancelled:
        assert isinstance(result, ydb.Cancelled)


def test_server_cancellation_preserves_server_status():
    response = SimpleNamespace(status=ydb.StatusCode.CANCELLED, issues=[])
    with pytest.raises(ydb.Cancelled) as exc_info:
        ydb.issues._process_response(response)
    assert type(exc_info.value) is ydb.Cancelled
    assert exc_info.value.status == ydb.StatusCode.CANCELLED


@pytest.mark.parametrize("idempotent", [False, True])
@pytest.mark.parametrize("retry_cancelled", [False, True])
@pytest.mark.parametrize("error", [ydb.ClientCancelled, ydb.Cancelled, ydb.DeadlineExceed, asyncio.CancelledError])
def test_cancellation_and_deadline_retry_policy(error, idempotent, retry_cancelled):
    retry_settings = ydb.RetrySettings(
        idempotent=idempotent,
        retry_cancelled=retry_cancelled,
        fast_backoff_settings=ydb.BackoffSettings(slot_duration=0),
    )

    result = check_retriable_error(error("cancelled"), retry_settings, 0)

    expected = (error is ydb.ClientCancelled and idempotent) or (error is ydb.Cancelled and retry_cancelled)
    assert result.is_retriable is expected
    assert result.sleep_timeout_seconds == (0 if expected else None)


@pytest.fixture
async def grpc_stream_endpoint():
    def responses(request, context):
        finished = threading.Event()
        context.add_callback(finished.set)
        yield request
        if request == b"cancel":
            context.abort(grpc.StatusCode.CANCELLED, "server cancelled")
        if request == b"deadline":
            context.abort(grpc.StatusCode.DEADLINE_EXCEEDED, "deadline exceeded")
        assert finished.wait(timeout=5)

    def bidirectional(requests, context):
        yield from responses(next(requests), context)

    with ThreadPoolExecutor(max_workers=4) as executor:
        server = grpc.server(executor)
        server.add_generic_rpc_handlers(
            (
                grpc.method_handlers_generic_handler(
                    "test.Transport",
                    {
                        "Query": grpc.unary_stream_rpc_method_handler(responses),
                        "Topic": grpc.stream_stream_rpc_method_handler(bidirectional),
                    },
                ),
            )
        )
        port = server.add_insecure_port("127.0.0.1:0")
        server.start()
        try:
            yield f"127.0.0.1:{port}"
        finally:
            assert await asyncio.to_thread(server.stop(0).wait, timeout=5)


class _StreamTestStub:
    def __init__(self, channel):
        self.Query = channel.unary_stream("/test.Transport/Query")
        self.Topic = channel.stream_stream("/test.Transport/Topic")


@pytest.mark.parametrize("notify", [False, True])
@pytest.mark.parametrize("cancellation", ["channel", "call", "call-and-channel", "server", "deadline"])
def test_sync_stream_distinguishes_channel_close_from_cancellation(grpc_stream_endpoint, cancellation, notify):
    disconnected = []
    with SyncConnection(grpc_stream_endpoint, ydb.DriverConfig(grpc_stream_endpoint)) as connection:
        request = {"server": b"cancel", "deadline": b"deadline"}.get(cancellation, b"first")
        stream = connection(
            request,
            _StreamTestStub,
            "Query",
            on_disconnected=(lambda: disconnected.append(True)) if notify else None,
        )
        assert next(stream) == request

        if cancellation in ("call", "call-and-channel"):
            stream.cancel()
        if cancellation in ("channel", "call-and-channel"):
            connection.close()

        error = {
            "channel": ydb.ClientCancelled,
            "call": ydb.Cancelled,
            "call-and-channel": ydb.Cancelled,
            "server": ydb.ClientCancelled,
            "deadline": ydb.DeadlineExceed,
        }[cancellation]
        with pytest.raises(error) as exc_info:
            next(stream)
        assert type(exc_info.value) is error
    assert disconnected == ([True] if cancellation in ("channel", "server") and notify else [])


@pytest.mark.parametrize("idempotent", [False, True])
@pytest.mark.parametrize("failure", ["channel", "server", "deadline"])
def test_sync_retry_handles_transport_cancellation_and_deadline(grpc_stream_endpoint, failure, idempotent):
    attempts = []
    first_request = {"server": b"cancel", "deadline": b"deadline"}.get(failure, b"first")

    def operation():
        with SyncConnection(grpc_stream_endpoint, ydb.DriverConfig(grpc_stream_endpoint)) as connection:
            stream = connection(first_request if not attempts else b"first", _StreamTestStub, "Query")
            attempts.append(next(stream))
            if len(attempts) == 1:
                if failure == "channel":
                    connection.close()
                next(stream)
            stream.cancel()
            return attempts[-1]

    retry_settings = ydb.RetrySettings(
        idempotent=idempotent, max_retries=1, fast_backoff_settings=ydb.BackoffSettings(slot_duration=0)
    )
    if idempotent and failure != "deadline":
        assert ydb.retry_operation_sync(operation, retry_settings=retry_settings) == b"first"
        assert attempts == [first_request, b"first"]
    else:
        error = ydb.DeadlineExceed if failure == "deadline" else ydb.ClientCancelled
        with pytest.raises(error):
            ydb.retry_operation_sync(operation, retry_settings=retry_settings)
        assert attempts == [first_request]


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["Query", "Topic"])
@pytest.mark.parametrize("notify", [False, True])
@pytest.mark.parametrize("cancellation", ["channel", "call", "call-and-channel", "server", "deadline"])
async def test_async_stream_distinguishes_channel_close_from_cancellation(
    grpc_stream_endpoint, method, cancellation, notify
):
    disconnected = []

    async def on_disconnected():
        disconnected.append(True)

    async with AsyncConnection(grpc_stream_endpoint, ydb.DriverConfig(grpc_stream_endpoint)) as connection:
        request = {"server": b"cancel", "deadline": b"deadline"}.get(cancellation, b"first")
        stream = await connection(
            request if method == "Query" else iter([request]),
            _StreamTestStub,
            method,
            on_disconnected=on_disconnected if notify else None,
        )
        assert await asyncio.wait_for(stream.__anext__(), timeout=5) == request

        if cancellation in ("call", "call-and-channel"):
            stream.cancel()
        if cancellation in ("channel", "call-and-channel"):
            await connection.close()

        error = {
            "channel": ydb.ClientCancelled,
            "call": asyncio.CancelledError,
            "call-and-channel": asyncio.CancelledError,
            "server": ydb.ClientCancelled,
            "deadline": ydb.DeadlineExceed,
        }[cancellation]
        with pytest.raises(error) as exc_info:
            await asyncio.wait_for(stream.__anext__(), timeout=5)
        assert type(exc_info.value) is error
    assert disconnected == ([True] if cancellation in ("channel", "server") and notify else [])


@pytest.mark.asyncio
@pytest.mark.parametrize("close_channel", [False, True])
async def test_async_stream_preserves_caller_task_cancellation(grpc_stream_endpoint, close_channel):
    entered = asyncio.Event()
    disconnected = []

    async def on_disconnected():
        disconnected.append(True)

    async with grpc.aio.insecure_channel(grpc_stream_endpoint) as channel:
        response = channel.unary_stream("/test.Transport/Query")(b"first")
        assert await asyncio.wait_for(response.__aiter__().__anext__(), timeout=5) == b"first"

        async def observed():
            entered.set()
            async for message in response:
                yield message

        stream = _SafeAsyncIterator(observed(), "test", on_disconnected)
        task = asyncio.create_task(stream.__anext__())
        try:
            await asyncio.wait_for(entered.wait(), timeout=5)
            task.cancel()
            if close_channel:
                await channel.close()
            with pytest.raises(asyncio.CancelledError):
                await asyncio.wait_for(task, timeout=5)
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
    assert disconnected == []


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["Query", "Topic"])
@pytest.mark.parametrize("idempotent", [False, True])
@pytest.mark.parametrize("failure", ["channel", "server", "deadline"])
async def test_async_retry_handles_transport_cancellation_and_deadline(
    grpc_stream_endpoint, method, failure, idempotent
):
    from ydb.retries import retry_operation_async

    attempts = []
    first_request = {"server": b"cancel", "deadline": b"deadline"}.get(failure, b"first")

    async def operation():
        async with AsyncConnection(grpc_stream_endpoint, ydb.DriverConfig(grpc_stream_endpoint)) as connection:
            request = first_request if not attempts else b"first"
            stream = await connection(request if method == "Query" else iter([request]), _StreamTestStub, method)
            attempts.append(await asyncio.wait_for(stream.__anext__(), timeout=5))
            if len(attempts) == 1:
                if failure == "channel":
                    await connection.close()
                await asyncio.wait_for(stream.__anext__(), timeout=5)
            stream.cancel()
            return attempts[-1]

    retry_settings = ydb.RetrySettings(
        idempotent=idempotent, max_retries=1, fast_backoff_settings=ydb.BackoffSettings(slot_duration=0)
    )
    if idempotent and failure != "deadline":
        assert await retry_operation_async(operation, retry_settings=retry_settings) == b"first"
        assert attempts == [first_request, b"first"]
    else:
        error = ydb.DeadlineExceed if failure == "deadline" else ydb.ClientCancelled
        with pytest.raises(error):
            await retry_operation_async(operation, retry_settings=retry_settings)
        assert attempts == [first_request]


def test_convert_floats_to_embedding_bytes_encodes_float32_values():
    assert ydb.convert_floats_to_embedding_bytes([1, -2, 0.5]) == bytes.fromhex("0000803f000000c00000003f01")


def test_convert_floats_to_embedding_bytes_converts_integers_to_float32():
    assert ydb.convert_floats_to_embedding_bytes([16777217, -2]) == bytes.fromhex("0000804b000000c001")


def test_convert_floats_to_embedding_bytes_converts_float64_to_float32():
    assert ydb.convert_floats_to_embedding_bytes([1.00000001]) == bytes.fromhex("0000803f01")


def test_convert_floats_to_embedding_bytes_rejects_empty_values():
    with pytest.raises(ValueError, match="embedding must not be empty"):
        ydb.convert_floats_to_embedding_bytes([])


def test_iam_is_available_from_ydb_package():
    assert ydb.iam.ServiceAccountCredentials is not None


def test_iam_is_loaded_lazily():
    code = (
        "import sys, ydb; "
        "print('iam' in dir(ydb)); "
        "print(hasattr(ydb, 'importlib')); "
        "print('ydb.iam' in sys.modules); "
        "ydb.iam; "
        "print('ydb.iam' in sys.modules)"
    )
    output = subprocess.check_output([sys.executable, "-c", code], text=True)

    assert output.splitlines() == ["True", "False", "False", "True"]


@pytest.fixture(scope="module")
def built_distributions(tmp_path_factory):
    dist_dir = tmp_path_factory.mktemp("dist")
    subprocess.run(
        [sys.executable, "-m", "build", "--outdir", str(dist_dir)],
        cwd=Path(__file__).resolve().parent.parent,
        check=True,
    )
    return dist_dir


def test_py_typed_is_in_wheel(built_distributions):
    wheel_path = next(built_distributions.glob("*.whl"))
    with zipfile.ZipFile(wheel_path) as wheel:
        assert "ydb/py.typed" in wheel.namelist()


def test_py_typed_is_in_sdist(built_distributions):
    sdist_path = next(built_distributions.glob("*.tar.gz"))
    with tarfile.open(sdist_path) as sdist:
        assert any(PurePosixPath(member.name).parts[-2:] == ("ydb", "py.typed") for member in sdist.getmembers())
