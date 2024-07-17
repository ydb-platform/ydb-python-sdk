import abc
from abc import abstractmethod
import asyncio
import concurrent
import logging
import threading
from typing import (
    Any,
    Optional,
    Set,
)

from . import base

from .. import _apis, issues, _utilities
from .._grpc.grpcwrapper import common_utils
from .._grpc.grpcwrapper import ydb_query as _ydb_query

from .transaction import BaseTxContext


logger = logging.getLogger(__name__)


def wrapper_create_session(rpc_state, response_pb, session_state: base.QuerySessionState, session):
    #TODO: process response
    message = _ydb_query.CreateSessionResponse.from_proto(response_pb)
    session_state.set_session_id(message.session_id).set_node_id(message.node_id)
    return session


def wrapper_delete_session(rpc_state, response_pb, session_state: base.QuerySessionState, session):
    #TODO: process response
    message = _ydb_query.DeleteSessionResponse.from_proto(response_pb)
    session_state.reset()
    return session


class BaseQuerySession(base.IQuerySession):
    _driver: base.SupportedDriverType
    _settings: Optional[base.QueryClientSettings]
    _state: base.QuerySessionState

    def __init__(self, driver: base.SupportedDriverType, settings: base.QueryClientSettings = None):
        self._driver = driver
        self._settings = settings
        self._state = base.QuerySessionState(settings)

    def _create_call(self):
        return self._driver(
            _apis.ydb_query.CreateSessionRequest(),
            _apis.QueryService.Stub,
            _apis.QueryService.CreateSession,
            wrap_result=wrapper_create_session,
            wrap_args=(self._state, self),
        )

    def _delete_call(self):
        return self._driver(
            _apis.ydb_query.DeleteSessionRequest(session_id=self._state.session_id),
            _apis.QueryService.Stub,
            _apis.QueryService.DeleteSession,
            wrap_result=wrapper_delete_session,
            wrap_args=(self._state, self),
        )

    def _attach_call(self):
        return self._driver(
            _apis.ydb_query.AttachSessionRequest(session_id=self._state.session_id),
            _apis.QueryService.Stub,
            _apis.QueryService.AttachSession,
        )

class QuerySessionSync(BaseQuerySession):
    _stream = None

    def _attach(self):
        self._stream = self._attach_call()
        status_stream = _utilities.SyncResponseIterator(
            self._stream,
            lambda response: common_utils.ServerStatus.from_proto(response),
        )

        first_response = next(status_stream)
        if first_response.status != issues.StatusCode.SUCCESS:
            pass
            # raise common_utils.YdbStatusError(first_response)

        self._state.set_attached(True)

        threading.Thread(
            target=self._chech_session_status_loop,
            args=(status_stream,),
            name="check session status thread",
            daemon=True,
        ).start()

    def _chech_session_status_loop(self, status_stream):
            print("CHECK STATUS")
            try:
                for status in status_stream:
                    if status.status != issues.StatusCode.SUCCESS:
                        print("STATUS NOT SUCCESS")
                        self._state.reset(False)
            except Exception as e:
                pass
            print("CHECK STATUS STOP")


    def delete(self) -> None:
        if not self._state.session_id:
            return
        self._delete_call()
        self._stream.cancel()

    def create(self) -> None:
        if self._state.session_id:
            return
        self._create_call()
        self._attach()

    def transaction(self, tx_mode: base.BaseQueryTxMode) -> base.IQueryTxContext:
        if not self._state.session_id:
            return
        return BaseTxContext(tx_mode)
