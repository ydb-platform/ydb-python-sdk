import abc
import asyncio
import enum
import functools

import typing
from typing import (
    Optional,
)

from .._grpc.grpcwrapper import ydb_query
from .._grpc.grpcwrapper.ydb_query_public_types import (
    BaseQueryTxMode,
)
from ..connection import _RpcState as RpcState
from .. import convert
from .. import issues
from .. import _utilities
from .. import _apis

if typing.TYPE_CHECKING:
    from .transaction import BaseQueryTxContext


class QuerySyntax(enum.IntEnum):
    UNSPECIFIED = 0
    YQL_V1 = 1
    PG = 2


class QueryExecMode(enum.IntEnum):
    UNSPECIFIED = 0
    PARSE = 10
    VALIDATE = 20
    EXPLAIN = 30
    EXECUTE = 50


class StatsMode(enum.IntEnum):
    UNSPECIFIED = 0
    NONE = 10
    BASIC = 20
    FULL = 30
    PROFILE = 40


class SyncResponseContextIterator(_utilities.SyncResponseIterator):
    def __enter__(self) -> "SyncResponseContextIterator":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        #  To close stream on YDB it is necessary to scroll through it to the end
        for _ in self:
            pass


class QueryClientSettings:
    def __init__(self):
        self._native_datetime_in_result_sets = True
        self._native_date_in_result_sets = True
        self._native_json_in_result_sets = True
        self._native_interval_in_result_sets = True
        self._native_timestamp_in_result_sets = True

    def with_native_timestamp_in_result_sets(self, enabled: bool) -> "QueryClientSettings":
        self._native_timestamp_in_result_sets = enabled
        return self

    def with_native_interval_in_result_sets(self, enabled: bool) -> "QueryClientSettings":
        self._native_interval_in_result_sets = enabled
        return self

    def with_native_json_in_result_sets(self, enabled: bool) -> "QueryClientSettings":
        self._native_json_in_result_sets = enabled
        return self

    def with_native_date_in_result_sets(self, enabled: bool) -> "QueryClientSettings":
        self._native_date_in_result_sets = enabled
        return self

    def with_native_datetime_in_result_sets(self, enabled: bool) -> "QueryClientSettings":
        self._native_datetime_in_result_sets = enabled
        return self


class IQuerySessionState(abc.ABC):
    def __init__(self, settings: Optional[QueryClientSettings] = None):
        pass

    @abc.abstractmethod
    def reset(self) -> None:
        pass

    @property
    @abc.abstractmethod
    def session_id(self) -> Optional[str]:
        pass

    @abc.abstractmethod
    def set_session_id(self, session_id: str) -> "IQuerySessionState":
        pass

    @property
    @abc.abstractmethod
    def node_id(self) -> Optional[int]:
        pass

    @abc.abstractmethod
    def set_node_id(self, node_id: int) -> "IQuerySessionState":
        pass

    @property
    @abc.abstractmethod
    def attached(self) -> bool:
        pass

    @abc.abstractmethod
    def set_attached(self, attached: bool) -> "IQuerySessionState":
        pass


def create_execute_query_request(
    query: str,
    session_id: str,
    tx_id: Optional[str],
    commit_tx: Optional[bool],
    tx_mode: Optional[BaseQueryTxMode],
    syntax: Optional[QuerySyntax],
    exec_mode: Optional[QueryExecMode],
    parameters: Optional[dict],
    concurrent_result_sets: Optional[bool],
) -> ydb_query.ExecuteQueryRequest:
    syntax = QuerySyntax.YQL_V1 if not syntax else syntax
    exec_mode = QueryExecMode.EXECUTE if not exec_mode else exec_mode
    stats_mode = StatsMode.NONE  # TODO: choise is not supported yet

    tx_control = None
    if not tx_id and not tx_mode:
        tx_control = None
    elif tx_id:
        tx_control = ydb_query.TransactionControl(
            tx_id=tx_id,
            commit_tx=commit_tx,
            begin_tx=None,
        )
    else:
        tx_control = ydb_query.TransactionControl(
            begin_tx=ydb_query.TransactionSettings(
                tx_mode=tx_mode,
            ),
            commit_tx=commit_tx,
            tx_id=None,
        )

    return ydb_query.ExecuteQueryRequest(
        session_id=session_id,
        query_content=ydb_query.QueryContent.from_public(
            query=query,
            syntax=syntax,
        ),
        tx_control=tx_control,
        exec_mode=exec_mode,
        parameters=parameters,
        concurrent_result_sets=concurrent_result_sets,
        stats_mode=stats_mode,
    )


def bad_session_handler(func):
    @functools.wraps(func)
    def decorator(rpc_state, response_pb, session_state: IQuerySessionState, *args, **kwargs):
        try:
            return func(rpc_state, response_pb, session_state, *args, **kwargs)
        except issues.BadSession:
            session_state.reset()
            raise

    return decorator


@bad_session_handler
def wrap_execute_query_response(
    rpc_state: RpcState,
    response_pb: _apis.ydb_query.ExecuteQueryResponsePart,
    session_state: IQuerySessionState,
    tx: Optional["BaseQueryTxContext"] = None,
    commit_tx: Optional[bool] = False,
    settings: Optional[QueryClientSettings] = None,
) -> convert.ResultSet:
    issues._process_response(response_pb)
    if tx and commit_tx:
        tx._move_to_commited()
    elif tx and response_pb.tx_meta and not tx.tx_id:
        tx._move_to_beginned(response_pb.tx_meta.id)

    if response_pb.HasField("result_set"):
        return convert.ResultSet.from_message(response_pb.result_set, settings)

    return None


class TxListener:
    def _on_before_commit(self):
        pass

    def _on_after_commit(self, exc: typing.Optional[BaseException]):
        pass

    def _on_before_rollback(self):
        pass

    def _on_after_rollback(self, exc: typing.Optional[BaseException]):
        pass


class TxListenerAsyncIO:
    async def _on_before_commit(self):
        pass

    async def _on_after_commit(self, exc: typing.Optional[BaseException]):
        pass

    async def _on_before_rollback(self):
        pass

    async def _on_after_rollback(self, exc: typing.Optional[BaseException]):
        pass


def with_transaction_events(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        method_name = method.__name__
        before_event = f"_on_before_{method_name}"
        after_event = f"_on_after_{method_name}"

        self._notify_listeners_sync(before_event)

        try:
            result = method(self, *args, **kwargs)

            self._notify_listeners_sync(after_event, exc=None)

            return result
        except BaseException as e:
            self._notify_listeners_sync(after_event, exc=e)
            raise

    return wrapper


def with_async_transaction_events(method):
    @functools.wraps(method)
    async def wrapper(self, *args, **kwargs):
        method_name = method.__name__
        before_event = f"_on_before_{method_name}"
        after_event = f"_on_after_{method_name}"

        await self._notify_listeners_async(before_event)

        try:
            result = await method(self, *args, **kwargs)

            await self._notify_listeners_async(after_event, exc=None)

            return result
        except BaseException as e:
            await self._notify_listeners_async(after_event, exc=e)
            raise

    return wrapper


class ListenerHandlerMixin:
    def _init_listener_handler(self):
        self.listeners = []

    def _add_listener(self, listener):
        if listener not in self.listeners:
            self.listeners.append(listener)
        return self

    def _remove_listener(self, listener):
        if listener in self.listeners:
            self.listeners.remove(listener)
        return self

    def _clear_listeners(self):
        self.listeners.clear()
        return self

    def _notify_sync_listeners(self, event_name: str, **kwargs) -> None:
        for listener in self.listeners:
            if isinstance(listener, TxListener) and hasattr(listener, event_name):
                getattr(listener, event_name)(**kwargs)

    async def _notify_async_listeners(self, event_name: str, **kwargs) -> None:
        coros = []
        for listener in self.listeners:
            if isinstance(listener, TxListenerAsyncIO) and hasattr(listener, event_name):
                coros.append(getattr(listener, event_name)(**kwargs))

        if coros:
            await asyncio.gather(*coros)

    def _notify_listeners_sync(self, event_name: str, **kwargs) -> None:
        self._notify_sync_listeners(event_name, **kwargs)

    async def _notify_listeners_async(self, event_name: str, **kwargs) -> None:
        # self._notify_sync_listeners(event_name, **kwargs)

        await self._notify_async_listeners(event_name, **kwargs)
