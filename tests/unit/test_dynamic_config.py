# -*- coding: utf-8 -*-
import pytest

from ydb import issues, operation
from ydb._apis import ydb_operation
from ydb.draft import dynamic_config as dc
from ydb.draft import _apis


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


def _get_config_response(version=7, cluster="cluster-1", config="cfg-text", status=issues.StatusCode.SUCCESS):
    result = _apis.ydb_dynamic_config.GetConfigResult()
    result.identity.version = version
    result.identity.cluster = cluster
    result.config = config
    op = ydb_operation.Operation(status=status)
    op.result.Pack(result)
    return _apis.ydb_dynamic_config.GetConfigResponse(operation=op)


def _get_node_labels_response(labels, status=issues.StatusCode.SUCCESS):
    result = _apis.ydb_dynamic_config.GetNodeLabelsResult()
    for label, value in labels.items():
        result.labels.add(label=label, value=value)
    op = ydb_operation.Operation(status=status)
    op.result.Pack(result)
    return _apis.ydb_dynamic_config.GetNodeLabelsResponse(operation=op)


def test_dynamic_config_dataclass():
    cfg = dc.DynamicConfig(3, "cl", "text", "extra")
    assert cfg.version == 3
    assert cfg.cluster == "cl"
    assert cfg.config == "text"


def test_node_labels_dataclass():
    nl = dc.NodeLabels({"dc": "vla"})
    assert nl.labels == {"dc": "vla"}


def test_replace_and_set_config_request_factory():
    replace = dc._replace_config_request_factory("cfg", True, False)
    assert replace.config == "cfg"
    assert replace.dry_run is True
    assert replace.allow_unknown_fields is False

    set_req = dc._set_config_request_factory("cfg2", False, True)
    assert set_req.config == "cfg2"
    assert set_req.dry_run is False
    assert set_req.allow_unknown_fields is True


def test_get_config_and_node_labels_request_factory():
    assert dc._get_config_request_factory() is not None
    node_req = dc._get_node_labels_request_factory(42)
    assert node_req.node_id == 42


def test_wrap_dynamic_config():
    result = _apis.ydb_dynamic_config.GetConfigResult()
    result.identity.version = 11
    result.identity.cluster = "prod"
    result.config = "yaml-config"
    wrapped = dc._wrap_dynamic_config(result)
    assert wrapped.version == 11
    assert wrapped.cluster == "prod"
    assert wrapped.config == "yaml-config"


def test_wrap_get_config_response_success_and_error():
    wrapped = dc._wrap_get_config_response(None, _get_config_response(version=9, cluster="c", config="cfg"))
    assert isinstance(wrapped, dc.DynamicConfig)
    assert wrapped.version == 9
    assert wrapped.cluster == "c"
    assert wrapped.config == "cfg"

    with pytest.raises(issues.BadRequest):
        dc._wrap_get_config_response(None, _get_config_response(status=issues.StatusCode.BAD_REQUEST))


def test_wrap_node_labels():
    result = _apis.ydb_dynamic_config.GetNodeLabelsResult()
    result.labels.add(label="dc", value="vla")
    result.labels.add(label="rack", value="7")
    wrapped = dc._wrap_node_labels(result)
    assert wrapped.labels == {"dc": "vla", "rack": "7"}


def test_wrap_get_node_labels_response_success_and_error():
    wrapped = dc._wrap_get_node_labels_response(None, _get_node_labels_response({"dc": "sas"}))
    assert isinstance(wrapped, dc.NodeLabels)
    assert wrapped.labels == {"dc": "sas"}

    with pytest.raises(issues.PreconditionFailed):
        dc._wrap_get_node_labels_response(
            None, _get_node_labels_response({}, status=issues.StatusCode.PRECONDITION_FAILED)
        )


def test_base_client_dispatch():
    driver = _FakeDriver()
    client = dc.BaseDynamicConfigClient(driver)

    client.replace_config("cfg", True, False)
    request, stub, method, wrapper, settings = driver.calls[-1]
    assert request.config == "cfg"
    assert stub is _apis.DynamicConfigService.Stub
    assert method == _apis.DynamicConfigService.ReplaceConfig
    assert wrapper is operation.Operation

    client.set_config("cfg2", False, True)
    assert driver.calls[-1][2] == _apis.DynamicConfigService.SetConfig

    client.get_config()
    request, _, method, wrapper, _ = driver.calls[-1]
    assert method == _apis.DynamicConfigService.GetConfig
    assert wrapper is dc._wrap_get_config_response

    client.get_node_labels(5)
    request, _, method, wrapper, _ = driver.calls[-1]
    assert request.node_id == 5
    assert method == _apis.DynamicConfigService.GetNodeLabels
    assert wrapper is dc._wrap_get_node_labels_response


def test_async_client_dispatch():
    driver = _FakeDriver()
    client = dc.DynamicConfigClient(driver)

    client.async_replace_config("cfg", True, False)
    assert driver.calls[-1][2] == _apis.DynamicConfigService.ReplaceConfig

    client.async_set_config("cfg", False, True)
    assert driver.calls[-1][2] == _apis.DynamicConfigService.SetConfig

    client.async_get_config()
    assert driver.calls[-1][3] is dc._wrap_get_config_response

    client.async_get_node_labels(9)
    request, _, method, wrapper, _ = driver.calls[-1]
    assert request.node_id == 9
    assert wrapper is dc._wrap_get_node_labels_response
