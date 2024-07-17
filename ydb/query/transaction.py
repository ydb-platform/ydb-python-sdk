import abc
import logging

from .. import (
    _apis,
    issues,
    _utilities,
)
from .._grpc.grpcwrapper import ydb_query as _ydb_query
from .._grpc.grpcwrapper import ydb_query_public_types as _ydb_query_public

from .._tx_ctx_impl import TxState, reset_tx_id_handler
from .._session_impl import bad_session_handler
from . import base

logger = logging.getLogger(__name__)

# def patch_table_service_tx_mode_to_query_service(tx_mode: AbstractTransactionModeBuilder):
#     if tx_mode.name == 'snapshot_read_only':
#         tx_mode = _ydb_query_public.QuerySnapshotReadOnly()
#     elif tx_mode.name == 'serializable_read_write':
#         tx_mode = _ydb_query_public.QuerySerializableReadWrite()
#     elif tx_mode.name =='online_read_only':
#         tx_mode = _ydb_query_public.QueryOnlineReadOnly()
#     elif tx_mode.name == 'stale_read_only':
#         tx_mode = _ydb_query_public.QueryStaleReadOnly()
#     else:
#         raise issues.YDBInvalidArgumentError(f'Unknown transaction mode: {tx_mode.name}')

#     return tx_mode


def _construct_tx_settings(tx_state):
    tx_settings = _ydb_query.TransactionSettings.from_public(tx_state.tx_mode)
    return tx_settings


def _create_begin_transaction_request(session_state, tx_state):
    request = _ydb_query.BeginTransactionRequest(
        session_id=session_state.session_id,
        tx_settings=_construct_tx_settings(tx_state),
    ).to_proto()

    print(request)

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


@bad_session_handler
def wrap_tx_begin_response(rpc_state, response_pb, session_state, tx_state, tx):
    # session_state.complete_query()
    # issues._process_response(response_pb.operation)
    print("wrap result")
    message = _ydb_query.BeginTransactionResponse.from_proto(response_pb)

    tx_state.tx_id = message.tx_meta.tx_id
    return tx


@bad_session_handler
@reset_tx_id_handler
def wrap_result_on_rollback_or_commit_tx(rpc_state, response_pb, session_state, tx_state, tx):

    # issues._process_response(response_pb.operation)
    # transaction successfully committed or rolled back
    tx_state.tx_id = None
    return tx


class BaseTxContext(base.IQueryTxContext):

    _COMMIT = "commit"
    _ROLLBACK = "rollback"

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
        self._tx_state = TxState(tx_mode)
        self._session_state = session_state
        self.session = session
        self._finished = ""

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
        if self._tx_state.tx_id is not None:
            return self

        print('try to begin tx')

        return self._driver(
            _create_begin_transaction_request(self._session_state, self._tx_state),
            _apis.QueryService.Stub,
            _apis.QueryService.BeginTransaction,
            wrap_result=wrap_tx_begin_response,
            wrap_args=(self._session_state, self._tx_state, self),
        )

    def commit(self, settings=None):
        """
        Calls commit on a transaction if it is open otherwise is no-op. If transaction execution
        failed then this method raises PreconditionFailed.

        :param settings: A request settings

        :return: A committed transaction or exception if commit is failed
        """

        self._set_finish(self._COMMIT)

        if self._tx_state.tx_id is None and not self._tx_state.dead:
            return self

        return self._driver(
            _create_commit_transaction_request(self._session_state, self._tx_state),
            _apis.QueryService.Stub,
            _apis.QueryService.CommitTransaction,
            wrap_result_on_rollback_or_commit_tx,
            settings,
            (self._session_state, self._tx_state, self),
        )

    def rollback(self, settings=None):
        pass

    def execute(self, query, parameters=None, commit_tx=False, settings=None):
        pass