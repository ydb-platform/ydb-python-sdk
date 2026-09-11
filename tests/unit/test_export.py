# -*- coding: utf-8 -*-
import pytest

from ydb import export, issues, _apis
from ydb._grpc.common.protos import ydb_export_pb2
from ydb._grpc.common import ydb_export_v1_pb2_grpc


class _FakeDriver:
    def __init__(self, result="RESULT"):
        self._result = result
        self.calls = []

    def __call__(self, *args):
        self.calls.append(args)
        return self._result

    def future(self, *args):
        self.calls.append(args)
        return self._result


def _s3_response(progress=ydb_export_pb2.ExportProgress.PROGRESS_DONE, operation_id="op-1"):
    op = _apis.ydb_operation.Operation(id=operation_id, status=issues.StatusCode.SUCCESS)
    op.metadata.Pack(ydb_export_pb2.ExportToS3Metadata(progress=progress))
    return _apis.ydb_operation.GetOperationResponse(operation=op)


def _yt_response(progress=ydb_export_pb2.ExportProgress.PROGRESS_TRANSFER_DATA, operation_id="op-2"):
    op = _apis.ydb_operation.Operation(id=operation_id, status=issues.StatusCode.SUCCESS)
    op.metadata.Pack(ydb_export_pb2.ExportToYtMetadata(progress=progress))
    return _apis.ydb_operation.GetOperationResponse(operation=op)


def test_export_progress_enum_initialized():
    # PROGRESS_* proto values are mapped onto the ExportProgress enum at import.
    assert export._progresses[ydb_export_pb2.ExportProgress.PROGRESS_DONE] is export.ExportProgress.DONE
    assert export._progresses[ydb_export_pb2.ExportProgress.PROGRESS_PREPARING] is export.ExportProgress.PREPARING


def test_s3_settings_builders():
    s = (
        export.ExportToS3Settings()
        .with_bucket("bucket")
        .with_endpoint("endpoint")
        .with_access_key("ak")
        .with_secret_key("sk")
        .with_scheme(1)
        .with_uid("uid-1")
        .with_number_of_retries(5)
        .with_storage_class(2)
        .with_export_compression("zstd")
        .with_source_and_destination("/table", "prefix")
        .with_items(("/t2", "p2"))
        .with_item(("/t3", "p3"))
    )
    assert s.bucket == "bucket"
    assert s.endpoint == "endpoint"
    assert s.access_key == "ak"
    assert s.secret_key == "sk"
    assert s.scheme == 1
    assert s.uid == "uid-1"
    assert s.number_of_retries == 5
    assert s.storage_class == 2
    assert s.export_compression == "zstd"
    assert s.items == [("/table", "prefix"), ("/t2", "p2"), ("/t3", "p3")]


def test_s3_request_factory_defaults():
    request = export._export_to_s3_request_factory(export.ExportToS3Settings())
    assert request.settings.scheme == 2
    assert len(request.settings.items) == 0
    assert "uid" not in request.operation_params.labels
    assert request.settings.number_of_retries == 0


def test_s3_request_factory_full():
    settings = (
        export.ExportToS3Settings()
        .with_bucket("b")
        .with_endpoint("e")
        .with_access_key("ak")
        .with_secret_key("sk")
        .with_uid("uid-9")
        .with_number_of_retries(3)
        .with_export_compression("gzip")
        .with_source_and_destination("/table", "prefix")
    )
    request = export._export_to_s3_request_factory(settings)
    assert request.settings.bucket == "b"
    assert request.settings.endpoint == "e"
    assert request.operation_params.labels["uid"] == "uid-9"
    assert request.settings.number_of_retries == 3
    assert request.settings.compression == "gzip"
    assert request.settings.items[0].source_path == "/table"
    assert request.settings.items[0].destination_prefix == "prefix"


def test_yt_settings_builders():
    s = (
        export.ExportToYTSettings()
        .with_host("host")
        .with_port(8080)
        .with_uid("uid")
        .with_token("token")
        .with_number_of_retries(2)
        .with_use_type_v3(True)
        .with_source_and_destination("/a", "/b")
        .with_items(("/c", "/d"))
    )
    assert s.host == "host"
    assert s.port == 8080
    assert s.uid == "uid"
    assert s.token == "token"
    assert s.number_of_retries == 2
    assert s.use_type_v3 is True
    assert s.items == [("/a", "/b"), ("/c", "/d")]


def test_yt_request_factory_defaults():
    request = export._export_to_yt_request_factory(export.ExportToYTSettings())
    assert request.settings.number_of_retries == 0
    assert request.settings.port == 0
    assert request.settings.use_type_v3 is False
    assert len(request.settings.items) == 0


def test_yt_request_factory_full():
    settings = (
        export.ExportToYTSettings()
        .with_host("host")
        .with_token("token")
        .with_port(9090)
        .with_number_of_retries(4)
        .with_use_type_v3(True)
        .with_source_and_destination("/a", "/b")
    )
    request = export._export_to_yt_request_factory(settings)
    assert request.settings.host == "host"
    assert request.settings.token == "token"
    assert request.settings.port == 9090
    assert request.settings.number_of_retries == 4
    assert request.settings.use_type_v3 is True
    assert request.settings.items[0].source_path == "/a"
    assert request.settings.items[0].destination_path == "/b"


def test_export_operation_wrappers():
    s3 = export.ExportToS3Operation(None, _s3_response(), driver=None)
    assert s3.id == "op-1"
    assert s3.progress is export.ExportProgress.DONE
    assert "ExportToS3Operation" in str(s3)
    assert repr(s3) == str(s3)

    yt = export.ExportToYTOperation(None, _yt_response(), driver=None)
    assert yt.id == "op-2"
    assert yt.progress is export.ExportProgress.TRANSFER_DATA
    assert "ExportToYTOperation" in str(yt)
    assert repr(yt) == str(yt)


def test_export_client_dispatch():
    driver = _FakeDriver()
    client = export.ExportClient(driver)

    client.export_to_s3(export.ExportToS3Settings())
    request, stub, method, wrapper, settings, wrap_args = driver.calls[-1]
    assert stub is ydb_export_v1_pb2_grpc.ExportServiceStub
    assert method == export._ExportToS3
    assert wrapper is export.ExportToS3Operation
    assert wrap_args == (driver,)

    client.export_to_yt(export.ExportToYTSettings())
    _, _, method, wrapper, _, _ = driver.calls[-1]
    assert method == export._ExportToYt
    assert wrapper is export.ExportToYTOperation

    client.async_export_to_yt(export.ExportToYTSettings())
    _, _, method, wrapper, _, _ = driver.calls[-1]
    assert method == export._ExportToYt

    client.get_export_to_s3_operation("op-x")
    request, _, method, wrapper, _, _ = driver.calls[-1]
    assert request.id == "op-x"
    assert method == _apis.OperationService.GetOperation
    assert wrapper is export.ExportToS3Operation


def test_export_operation_error_status_raises():
    op = _apis.ydb_operation.Operation(status=issues.StatusCode.BAD_REQUEST)
    op.metadata.Pack(ydb_export_pb2.ExportToS3Metadata())
    response = _apis.ydb_operation.GetOperationResponse(operation=op)
    with pytest.raises(issues.BadRequest):
        export.ExportToS3Operation(None, response, driver=None)
