# -*- coding: utf-8 -*-
import abc
import enum
from abc import abstractmethod
from . import issues, operation, settings as settings_impl, _apis


class SelfCheckSettings(settings_impl.BaseRequestSettings):
    pass


def _self_check_request_factory(return_verbose_status=None, minimum_status=None, maximum_level=None):
    request = _apis.ydb_monitoring.SelfCheckRequest()
    if return_verbose_status is not None:
        request.return_verbose_status = return_verbose_status
    if minimum_status is not None:
        request.minimum_status = minimum_status
    if maximum_level is not None:
        request.maximum_level = maximum_level
    return request


def _wrap_self_check_response(rpc_state, response):
    issues._process_response(response.operation)
    message = _apis.ydb_monitoring.SelfCheckResult()
    response.operation.result.Unpack(message)
    return message


class IMonitoringClient(abc.ABC):
    @abstractmethod
    def __init__(self, driver):
        pass

    @abstractmethod
    def self_check(self, return_verbose_status=None, minimum_status=None, maximum_level=None, settings=None):
        pass


class BaseMonitoringClient(IMonitoringClient):
    __slots__ = ("_driver",)

    def __init__(self, driver):
        self._driver = driver

    def self_check(self, return_verbose_status=None, minimum_status=None, maximum_level=None, settings=None):
        return self._driver(
            _self_check_request_factory(return_verbose_status, minimum_status, maximum_level),
            _apis.MonitoringService.Stub,
            _apis.MonitoringService.SelfCheck,
            _wrap_self_check_response,
            settings,
        )


class MonitoringClient(BaseMonitoringClient):
    def async_self_check(self, return_verbose_status=None, minimum_status=None, maximum_level=None, settings=None):
        return self._driver.future(
            _self_check_request_factory(return_verbose_status, minimum_status, maximum_level),
            _apis.MonitoringService.Stub,
            _apis.MonitoringService.SelfCheck,
            _wrap_self_check_response,
            settings,
        )
