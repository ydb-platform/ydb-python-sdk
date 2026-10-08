# -*- coding: utf-8 -*-
import pytest

from ydb import import_client, issues, _apis
from ydb._grpc.common.protos import ydb_import_pb2
from ydb._grpc.common import ydb_import_v1_pb2_grpc


class _FakeDriver:
    def __init__(self, result="RESULT"):
        self._result = result
        self.calls = []

    def __call__(self, *args):
        self.calls.append(args)
        return self._result


def _s3_response(progress=ydb_import_pb2.ImportProgress.PROGRESS_DONE, operation_id="imp-1"):
    op = _apis.ydb_operation.Operation(id=operation_id, status=issues.StatusCode.SUCCESS)
    op.metadata.Pack(ydb_import_pb2.ImportFromS3Metadata(progress=progress))
    return _apis.ydb_operation.GetOperationResponse(operation=op)


def test_import_progress_enum_initialized():
    assert import_client._progresses[ydb_import_pb2.ImportProgress.PROGRESS_DONE] is import_client.ImportProgress.DONE
    assert (
        import_client._progresses[ydb_import_pb2.ImportProgress.PROGRESS_BUILD_INDEXES]
        is import_client.ImportProgress.BUILD_INDEXES
    )


def test_s3_settings_builders():
    s = (
        import_client.ImportFromS3Settings()
        .with_bucket("bucket")
        .with_endpoint("endpoint")
        .with_access_key("ak")
        .with_secret_key("sk")
        .with_scheme(1)
        .with_uid("uid-1")
        .with_number_of_retries(7)
        .with_source_and_destination("src", "dst")
        .with_items(("s2", "d2"))
        .with_item(("s3", "d3"))
    )
    assert s.bucket == "bucket"
    assert s.endpoint == "endpoint"
    assert s.access_key == "ak"
    assert s.secret_key == "sk"
    assert s.scheme == 1
    assert s.uid == "uid-1"
    assert s.number_of_retries == 7
    assert s.items == [("src", "dst"), ("s2", "d2"), ("s3", "d3")]


def test_s3_request_factory_defaults():
    request = import_client._import_from_s3_request_factory(import_client.ImportFromS3Settings())
    assert request.settings.scheme == 2
    assert len(request.settings.items) == 0
    assert "uid" not in request.operation_params.labels
    assert request.settings.number_of_retries == 0


def test_s3_request_factory_full():
    settings = (
        import_client.ImportFromS3Settings()
        .with_bucket("b")
        .with_endpoint("e")
        .with_access_key("ak")
        .with_secret_key("sk")
        .with_uid("uid-2")
        .with_number_of_retries(2)
        .with_source_and_destination("source-prefix", "/dest/table")
    )
    request = import_client._import_from_s3_request_factory(settings)
    assert request.settings.bucket == "b"
    assert request.settings.endpoint == "e"
    assert request.settings.access_key == "ak"
    assert request.settings.secret_key == "sk"
    assert request.operation_params.labels["uid"] == "uid-2"
    assert request.settings.number_of_retries == 2
    assert request.settings.items[0].source_prefix == "source-prefix"
    assert request.settings.items[0].destination_path == "/dest/table"


def test_import_operation_wrapper():
    op = import_client.ImportFromS3Operation(None, _s3_response(), driver=None)
    assert op.id == "imp-1"
    assert op.progress is import_client.ImportProgress.DONE
    assert "ImportFromS3Operation" in str(op)
    assert repr(op) == str(op)


def test_import_operation_error_status_raises():
    op = _apis.ydb_operation.Operation(status=issues.StatusCode.BAD_REQUEST)
    op.metadata.Pack(ydb_import_pb2.ImportFromS3Metadata())
    response = _apis.ydb_operation.GetOperationResponse(operation=op)
    with pytest.raises(issues.BadRequest):
        import_client.ImportFromS3Operation(None, response, driver=None)


def test_import_client_dispatch():
    driver = _FakeDriver()
    client = import_client.ImportClient(driver)

    client.import_from_s3(import_client.ImportFromS3Settings())
    request, stub, method, wrapper, settings, wrap_args = driver.calls[-1]
    assert stub is ydb_import_v1_pb2_grpc.ImportServiceStub
    assert method == import_client._ImportFromS3
    assert wrapper is import_client.ImportFromS3Operation
    assert wrap_args == (driver,)

    client.get_import_from_s3_operation("imp-x")
    request, _, method, wrapper, _, _ = driver.calls[-1]
    assert request.id == "imp-x"
    assert method == _apis.OperationService.GetOperation
    assert wrapper is import_client.ImportFromS3Operation
