# -*- coding: utf-8 -*-
from . import issues
from . import _apis


def _forget_operation_request(self):
    request = _apis.ydb_operation.ForgetOperationRequest(id=self.id)
    return request


def _forget_operation_response(rpc_state, response):
    issues._process_response(response)


def _cancel_operation_request(self):
    request = _apis.ydb_operation.CancelOperationRequest(id=self.id)
    return request


def _cancel_operation_response(rpc_state, response):
    issues._process_response(response)


def _get_operation_request(self):
    request = _apis.ydb_operation.GetOperationRequest(id=self.id)
    return request


class Operation(object):
    __slots__ = ('id', '_driver', 'self_cls')

    def __init__(self, rpc_state, response, driver=None):
        # implement proper interface a bit later
        issues._process_response(response.operation)
        self.id = response.operation.id
        self._driver = driver
        # self.ready = operation.ready

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "<Operation %s>" % (self.id, )

    def _ensure_implements(self):
        if self._driver is None:
            raise ValueError("Operation doesn't implement request!")

    def cancel(self, settings=None):
        self._ensure_implements()
        return self._driver(
            _cancel_operation_request(self),
            _apis.OperationService.Stub,
            _apis.OperationService.CancelOperation,
            _cancel_operation_response,
            settings,
        )

    def forget(self, settings=None):
        self._ensure_implements()
        return self._driver(
            _forget_operation_request(self),
            _apis.OperationService.Stub,
            _apis.OperationService.ForgetOperation,
            _forget_operation_response,
            settings,
        )

    def get(self, settings=None):
        self._ensure_implements()
        return self._driver(
            _get_operation_request(self),
            _apis.OperationService.Stub,
            _apis.OperationService.GetOperation,
            self.__class__,
            settings,
            (
                self._driver,
            )
        )
