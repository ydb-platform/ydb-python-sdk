import abc
import logging
import enum
import functools

from .. import (
    _apis,
    issues,
    _utilities,
)
from .._grpc.grpcwrapper import ydb_query as _ydb_query
from .._grpc.grpcwrapper import ydb_query_public_types as _ydb_query_public

from . import base

logger = logging.getLogger(__name__)


class QueryTxStateEnum(enum.Enum):
    NOT_INITIALIZED = "NOT_INITIALIZED"
    BEGINED = "BEGINED"
    COMMITTED = "COMMITTED"
    ROLLBACKED = "ROLLBACKED"
    DEAD = "DEAD"


class QueryTxStateHelper(abc.ABC):
    _VALID_TRANSITIONS = {
        QueryTxStateEnum.NOT_INITIALIZED: [QueryTxStateEnum.BEGINED, QueryTxStateEnum.DEAD],
        QueryTxStateEnum.BEGINED: [QueryTxStateEnum.COMMITTED, QueryTxStateEnum.ROLLBACKED, QueryTxStateEnum.DEAD],
        QueryTxStateEnum.COMMITTED: [],
        QueryTxStateEnum.ROLLBACKED: [],
        QueryTxStateEnum.DEAD: [],
    }

    _TERMINAL_STATES = [
        QueryTxStateEnum.COMMITTED,
        QueryTxStateEnum.ROLLBACKED,
        QueryTxStateEnum.DEAD,
    ]

    @classmethod
    def valid_transition(cls, before: QueryTxStateEnum, after: QueryTxStateEnum) -> bool:
        return after in cls._VALID_TRANSITIONS[before]

    @classmethod
    def terminal(cls, state: QueryTxStateEnum) -> bool:
        return state in cls._TERMINAL_STATES


def reset_tx_id_handler(func):
    @functools.wraps(func)
    def decorator(rpc_state, response_pb, session_state, tx_state, *args, **kwargs):
        try:
            return func(rpc_state, response_pb, session_state, tx_state, *args, **kwargs)
        except issues.Error:
            tx_state._change_state(QueryTxStateEnum.DEAD)
            tx_state.tx_id = None
            raise

    return decorator


class QueryTxState:
    def __init__(self, tx_mode: base.BaseQueryTxMode):
        """
        Holds transaction context manager info
        :param tx_mode: A mode of transaction
        """
        self.tx_id = None
        self.tx_mode = tx_mode
        self._state = QueryTxStateEnum.NOT_INITIALIZED

    def _check_invalid_transition(self, target: QueryTxStateEnum):
        if not QueryTxStateHelper.valid_transition(self._state, target):
            raise RuntimeError(f"Transaction could not be moved from {self._state.value} to {target.value}")

    def _change_state(self, target: QueryTxStateEnum):
        self._check_invalid_transition(target)
        self._state = target

    def _check_tx_not_terminal(self):
        if QueryTxStateHelper.terminal(self._state):
            raise RuntimeError(f"Transaction is in terminal state: {self._state.value}")

    def _already_in(self, target: QueryTxStateEnum):
        return self._state == target


def _construct_tx_settings(tx_state):
    tx_settings = _ydb_query.TransactionSettings.from_public(tx_state.tx_mode)
    return tx_settings


def _create_begin_transaction_request(session_state, tx_state):
    request = _ydb_query.BeginTransactionRequest(
        session_id=session_state.session_id,
        tx_settings=_construct_tx_settings(tx_state),
    ).to_proto()
    return request


def _create_commit_transaction_request(session_state, tx_state):
    request = _apis.ydb_query.CommitTransactionRequest()
    request.tx_id = tx_state.tx_id
    request.session_id = session_state.session_id
    return request


def _create_rollback_transaction_request(session_state, tx_state):
    request = _apis.ydb_query.RollbackTransactionRequest()
    request.tx_id = tx_state.tx_id
    request.session_id = session_state.session_id
    return request


@base.bad_session_handler
def wrap_tx_begin_response(rpc_state, response_pb, session_state, tx_state, tx):
    message = _ydb_query.BeginTransactionResponse.from_proto(response_pb)
    issues._process_response(message.status)
    tx_state._change_state(QueryTxStateEnum.BEGINED)
    tx_state.tx_id = message.tx_meta.tx_id
    return tx


@base.bad_session_handler
@reset_tx_id_handler
def wrap_tx_commit_response(rpc_state, response_pb, session_state, tx_state, tx):
    message = _ydb_query.CommitTransactionResponse.from_proto(response_pb)
    issues._process_response(message.status)
    tx_state.tx_id = None
    tx_state._change_state(QueryTxStateEnum.COMMITTED)
    return tx


@base.bad_session_handler
@reset_tx_id_handler
def wrap_tx_rollback_response(rpc_state, response_pb, session_state, tx_state, tx):
    message = _ydb_query.RollbackTransactionResponse.from_proto(response_pb)
    issues._process_response(message.status)
    tx_state.tx_id = None
    tx_state._change_state(QueryTxStateEnum.ROLLBACKED)
    return tx


class BaseTxContext(base.IQueryTxContext):
    def __init__(self, driver, session_state, session, tx_mode=None):
        """
        An object that provides a simple transaction context manager that allows statements execution
        in a transaction. You don't have to open transaction explicitly, because context manager encapsulates
        transaction control logic, and opens new transaction if:

        1) By explicit .begin() and .async_begin() methods;
        2) On execution of a first statement, which is strictly recommended method, because that avoids useless round trip

        This context manager is not thread-safe, so you should not manipulate on it concurrently.

        :param driver: A driver instance
        :param session_state: A state of session
        :param tx_mode: A transaction mode, which is a one from the following choices:
         1) SerializableReadWrite() which is default mode;
         2) OnlineReadOnly();
         3) StaleReadOnly().
        """
        self._driver = driver
        if tx_mode is None:
            tx_mode = _ydb_query_public.QuerySerializableReadWrite()
        self._tx_state = QueryTxState(tx_mode)
        self._session_state = session_state
        self.session = session
        self._finished = ""
        self._prev_stream = None

    def __enter__(self):
        """
        Enters a context manager and returns a session

        :return: A session instance
        """
        return self

    def __exit__(self, *args, **kwargs):
        """
        Closes a transaction context manager and rollbacks transaction if
        it is not rolled back explicitly
        """
        if self._tx_state.tx_id is not None:
            # It's strictly recommended to close transactions directly
            # by using commit_tx=True flag while executing statement or by
            # .commit() or .rollback() methods, but here we trying to do best
            # effort to avoid useless open transactions
            logger.warning("Potentially leaked tx: %s", self._tx_state.tx_id)
            try:
                self.rollback()
            except issues.Error:
                logger.warning("Failed to rollback leaked tx: %s", self._tx_state.tx_id)

            self._tx_state.tx_id = None

    @property
    def session_id(self):
        """
        A transaction's session id

        :return: A transaction's session id
        """
        return self._session_state.session_id

    @property
    def tx_id(self):
        """
        Returns a id of open transaction or None otherwise

        :return: A id of open transaction or None otherwise
        """
        return self._tx_state.tx_id

    def begin(self, settings=None):
        """
        Explicitly begins a transaction

        :param settings: A request settings

        :return: An open transaction
        """
        self._tx_state._check_invalid_transition(QueryTxStateEnum.BEGINED)

        return self._driver(
            _create_begin_transaction_request(self._session_state, self._tx_state),
            _apis.QueryService.Stub,
            _apis.QueryService.BeginTransaction,
            wrap_tx_begin_response,
            settings,
            (self._session_state, self._tx_state, self),
        )

    def commit(self, settings=None):
        """
        Calls commit on a transaction if it is open otherwise is no-op. If transaction execution
        failed then this method raises PreconditionFailed.

        :param settings: A request settings

        :return: A committed transaction or exception if commit is failed
        """
        if self._tx_state._already_in(QueryTxStateEnum.COMMITTED):
            return
        self._ensure_prev_stream_finished()
        self._tx_state._check_invalid_transition(QueryTxStateEnum.COMMITTED)

        return self._driver(
            _create_commit_transaction_request(self._session_state, self._tx_state),
            _apis.QueryService.Stub,
            _apis.QueryService.CommitTransaction,
            wrap_tx_commit_response,
            settings,
            (self._session_state, self._tx_state, self),
        )

    def rollback(self, settings=None):
        if self._tx_state._already_in(QueryTxStateEnum.ROLLBACKED):
            return

        self._ensure_prev_stream_finished()
        self._tx_state._check_invalid_transition(QueryTxStateEnum.ROLLBACKED)

        return self._driver(
            _create_rollback_transaction_request(self._session_state, self._tx_state),
            _apis.QueryService.Stub,
            _apis.QueryService.RollbackTransaction,
            wrap_tx_rollback_response,
            settings,
            (self._session_state, self._tx_state, self),
        )

    def _execute_call(
        self,
        query: str,
        commit_tx: bool = False,
        tx_mode: base.BaseQueryTxMode = None,
        syntax: base.QuerySyntax = None,
        exec_mode: base.QueryExecMode = None,
        parameters: dict = None,
        concurrent_result_sets: bool = False,
    ):
        request = base.create_execute_query_request(
            query=query,
            session_id=self._session_state.session_id,
            commit_tx=commit_tx,
            tx_id=self._tx_state.tx_id,
            tx_mode=tx_mode,
            syntax=syntax,
            exec_mode=exec_mode,
            parameters=parameters,
            concurrent_result_sets=concurrent_result_sets,
        )

        return self._driver(
            request,
            _apis.QueryService.Stub,
            _apis.QueryService.ExecuteQuery,
        )

    def _ensure_prev_stream_finished(self):
        if self._prev_stream is not None:
            for _ in self._prev_stream:
                pass
            self._prev_stream = None

    def _handle_tx_meta(self, tx_meta=None):
        if not self.tx_id:
            self._tx_state._change_state(QueryTxStateEnum.BEGINED)
            self._tx_state.tx_id = tx_meta.id

    def _move_to_commited(self):
        if self._tx_state._already_in(QueryTxStateEnum.COMMITTED):
            return
        self._tx_state._change_state(QueryTxStateEnum.COMMITTED)

    def execute(
        self,
        query: str,
        commit_tx: bool = False,
        tx_mode: base.BaseQueryTxMode = None,
        syntax: base.QuerySyntax = None,
        exec_mode: base.QueryExecMode = None,
        parameters: dict = None,
        concurrent_result_sets: bool = False,
    ):
        self._ensure_prev_stream_finished()
        self._tx_state._check_tx_not_terminal()

        stream_it = self._execute_call(
            query=query,
            commit_tx=commit_tx,
            tx_mode=tx_mode,
            syntax=syntax,
            exec_mode=exec_mode,
            parameters=parameters,
            concurrent_result_sets=concurrent_result_sets,
        )
        self._prev_stream = _utilities.SyncResponseIterator(
            stream_it,
            lambda resp: base.wrap_execute_query_response(
                rpc_state=None,
                response_pb=resp,
                tx=self,
                commit_tx=commit_tx,
            ),
        )
        return self._prev_stream
