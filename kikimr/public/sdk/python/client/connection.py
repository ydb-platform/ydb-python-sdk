# -*- coding: utf-8 -*-
import logging
import copy
from concurrent import futures
import uuid

from google.protobuf import text_format
import grpc
from kikimr.public.sdk.python.client import issues
from kikimr.public.api.grpc import ydb_table_v1_pb2_grpc as ydb_table_pb2_grpc
from kikimr.public.api.grpc import ydb_scheme_v1_pb2_grpc as ydb_scheme_pb2_grpc
from kikimr.public.api.grpc import ydb_discovery_v1_pb2_grpc as ydb_discovery_pb2_grpc
from kikimr.public.api.grpc import ydb_cms_v1_pb2_grpc as ydb_cms_pb2_grpc

_stubs_list = (
    ydb_table_pb2_grpc.TableServiceStub,
    ydb_scheme_pb2_grpc.SchemeServiceStub,
    ydb_discovery_pb2_grpc.DiscoveryServiceStub,
    ydb_cms_pb2_grpc.CmsServiceStub
)

logger = logging.getLogger(__name__)
DEFAULT_TIMEOUT = 600
YDB_DATABASE_HEADER = "x-ydb-database"
YDB_TRACE_ID_HEADER = "x-ydb-trace-id"


def _message_to_string(message):
    """
    Constructs a string representation of provided message or generator
    :param message: A protocol buffer or generator instance
    :return: A string
    """
    try:
        return text_format.MessageToString(message, as_one_line=True)
    except AttributeError:
        return str(message)


def _log_response(request_id, rpc_name, response):
    """
    Writes a message with response into debug logs
    :param request_id: An id of request
    :param rpc_name: A name of RPC
    :param response: A received response
    :return: None
    """
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(
            "Request_id = %s, rpc name = %s, response = { %s }", request_id, rpc_name, _message_to_string(
                response
            )
        )


def _log_request(request_id, rpc_name, request):
    """
    Writes a message with request into debug logs
    :param request_id: An id of request
    :param rpc_name: A name of RPC
    :param request: A received response
    :return: None
    """
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(
            "Request_id = %s, rpc name = %s, request = { %s }", request_id, rpc_name, _message_to_string(
                request
            )
        )


def _rpc_error_handler(request_id, rpc_error, on_disconnected=None):
    """
    RPC call error handler, that translates gRPC error into YDB issue
    :param request_id: An id of request
    :param rpc_error: an underlying rpc error to handle
    :param on_disconnected: a handler to call on disconnected connection
    """
    logger.info("Request_id = %s, RPC error, %s", request_id, str(rpc_error))
    if isinstance(rpc_error, grpc.Call):
        if rpc_error.code() == grpc.StatusCode.UNAUTHENTICATED:
            return issues.Unauthenticated('User should be authenticated!')
        elif rpc_error.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
            return issues.DeadlineExceed('Deadline exceeded on request')
        elif rpc_error.code() == grpc.StatusCode.UNIMPLEMENTED:
            return issues.Unimplemented('Method or feature is not implemented on server!')

    logger.debug("Request_id = %s, unhandled rpc error, disconnecting channel", request_id)
    if on_disconnected is not None:
        on_disconnected()

    return issues.ConnectionLost(
        "Rpc error, reason %s" % str(
            rpc_error
        )
    )


def _on_response_callback(
        response_future, wrap_future, rpc_name, request_id, call_state_unref, wrap_result=None,
        on_disconnected=None, wrap_args=()
):
    """
    Callback to be executed on received RPC response
    :param response_future: A future of response
    :param wrap_future: A future that wraps underlying response future
    :param rpc_name: A name of RPC
    :param wrap_result: A callable that wraps received response
    :param on_disconnected: A handler to executed on disconnected channel
    :param wrap_args: An arguments to be passed into wrap result callable
    :return: None
    """
    try:
        logger.debug("Request_id = %s, on response callback started", request_id)
        response = response_future.result()
        _log_response(request_id, rpc_name, response)
        response = response if wrap_result is None else wrap_result(response.operation, *wrap_args)
        wrap_future.set_result(response)
        logger.debug("Request_id = %s, on response callback success", request_id)
    except grpc.FutureCancelledError as e:
        logger.debug("Request_id = %s, request execution cancelled", request_id)
        if not wrap_future.cancelled():
            wrap_future.set_exception(e)

    except grpc.RpcError as rpc_call_error:
        wrap_future.set_exception(
            _rpc_error_handler(
                request_id, rpc_call_error, on_disconnected
            )
        )

    except Exception as e:
        logger.debug("Request_id = %s, received exception, %s", request_id, str(e))
        wrap_future.set_exception(e)

    call_state_unref()


def _construct_metadata(driver_config, settings):
    """
    Translates request settings into RPC metadata
    :param driver_config: A driver config
    :param settings: An instance of BaseRequestSettings
    :return: RPC metadata
    """
    metadata = []
    if driver_config.database is not None:
        metadata.append((YDB_DATABASE_HEADER, driver_config.database))

    if driver_config.credentials is not None:
        metadata.extend(driver_config.credentials.auth_metadata())

    if settings is not None and settings.trace_id is not None:
        metadata.append((YDB_TRACE_ID_HEADER, settings.trace_id))
    return metadata


def _get_request_timeout(settings):
    """
    Extracts RPC timeout from request settings
    :param settings: an instance of BaseRequestSettings
    :return: timeout of RPC execution
    """
    if settings is None or settings.timeout is None:
        return DEFAULT_TIMEOUT
    return settings.timeout


def _construct_channel_options(driver_config):
    """
    Constructs gRPC channel initialization options
    :param driver_config: A driver config instance
    :return: A channel initialization options
    """
    _max_message_size = 64 * 10 ** 6
    _default_connect_options = [
        ('grpc.max_receive_message_length', _max_message_size),
        ('grpc.max_send_message_length', _max_message_size),
        ('grpc.primary_user_agent', 'python-library'),
    ]
    if driver_config.channel_options is None:
        return _default_connect_options
    channel_options = copy.deepcopy(driver_config.channel_options)
    channel_options.extend(_default_connect_options)
    return channel_options


class _RpcState(object):
    __slots__ = ('_rpc', 'request_id', '_future')

    def __init__(self, stub_instance, rpc_name, request_id):
        """Stores all RPC related data"""
        self._rpc = getattr(stub_instance, rpc_name)
        self.request_id = request_id
        self._future = None

    def __call__(self, *args, **kwargs):
        return self._rpc(*args, **kwargs)

    def future(self, *args, **kwargs):
        self._future = self._rpc.future(*args, **kwargs)
        return self._future


class Connection(object):
    __slots__ = (
        'endpoint', '_channel', '_call_states', '_stub_instances', '_driver_config', '_cleanup_callbacks',
        '__weakref__'
    )

    def __init__(self, endpoint, driver_config=None):
        """
        Object that wraps gRPC channel and encapsulates gRPC request execution logic
        :param endpoint: endpoint to connect (in pattern host:port), constructed by user or
        discovered by the YDB endpoint discovery mechanism
        :param driver_config: A driver config instance to be used for RPC call interception
        """
        global _stubs_list
        self.endpoint = endpoint
        self._channel = grpc.insecure_channel(self.endpoint, _construct_channel_options(driver_config))
        self._driver_config = driver_config
        self._call_states = {}
        self._stub_instances = {}
        self._cleanup_callbacks = []
        # pre-initialize stubs
        for stub in _stubs_list:
            self._stub_instances[stub] = stub(self._channel)

    def add_cleanup_callback(self, callback):
        self._cleanup_callbacks.append(callback)

    def _call_state(self, request_id, stub, rpc_name, settings, keep_ref=True):
        timeout, metadata = _get_request_timeout(settings), _construct_metadata(
            self._driver_config, settings)
        call_state = _RpcState(self._stub_instances[stub], rpc_name, request_id)
        logger.debug("Request_id = %s, creating call state", request_id)
        if keep_ref:
            self._call_states[call_state.request_id] = call_state
        return call_state, timeout, metadata

    def _unref_call_state(self, call_state):
        logger.debug("Request_id = %s, unref call state", call_state.request_id)
        self._call_states.pop(call_state.request_id)

    def future(self, request, stub, rpc_name, wrap_result=None, settings=None, on_disconnected=None, wrap_args=()):
        """
        Sends request constructed by client
        :param request: A request constructed by client
        :param stub: A stub instance to wrap channel
        :param rpc_name: A name of RPC to be executed
        :param wrap_result: A callable that intercepts call and wraps received response
        :param settings: An instance of BaseRequestSettings that can be used
        for RPC metadata construction
        :param on_disconnected: A callable to be executed when underlying channel becomes disconnected
        :param wrap_args: And arguments to be passed into wrap_result callable
        :return: A future of computation
        """
        request_id = uuid.uuid4()
        _log_request(request_id, rpc_name, request)
        call_state, timeout, metadata = self._call_state(request_id, stub, rpc_name, settings)
        wrap_future = futures.Future()
        response_future = call_state.future(request, timeout, metadata)

        def _cancel_callback(f):
            """forwards cancel to gPRC future"""
            if f.cancelled():
                response_future.cancel()

        wrap_future.add_done_callback(_cancel_callback)
        response_future.add_done_callback(
            lambda resp_future: _on_response_callback(
                resp_future, wrap_future, rpc_name, request_id, lambda: self._unref_call_state(call_state),
                wrap_result, on_disconnected, wrap_args,
            )
        )
        return wrap_future

    def __call__(self, request, stub, rpc_name, wrap_result=None, settings=None, on_disconnected=None, wrap_args=()):
        """
        Synchronously sends request constructed by client library
        :param request: A request constructed by client
        :param stub: A stub instance to wrap channel
        :param rpc_name: A name of RPC to be executed
        :param wrap_result: A callable that intercepts call and wraps received response
        :param settings: An instance of BaseRequestSettings that can be used
        for RPC metadata construction
        :param on_disconnected: A callable to be executed when underlying channel becomes disconnected
        :param wrap_args: And arguments to be passed into wrap_result callable
        :return: A result of computation
        """
        request_id = uuid.uuid4()
        try:
            _log_request(request_id, rpc_name, request)
            call_state, timeout, metadata = self._call_state(request_id, stub, rpc_name, settings, keep_ref=False)
            response = call_state(request, timeout, metadata)
            _log_response(request_id, rpc_name, response)
            return response if wrap_result is None else wrap_result(response.operation, *wrap_args)
        except grpc.RpcError as rpc_error:
            raise _rpc_error_handler(
                request_id,
                rpc_error,
                on_disconnected
            )

    @classmethod
    def ready_factory(cls, endpoint, driver_config, ready_timeout=2):
        candidate = cls(endpoint, driver_config)
        ready_future = candidate.ready_future()
        try:
            ready_future.result(timeout=ready_timeout)
            return candidate
        except grpc.FutureTimeoutError:
            ready_future.cancel()
            candidate.close()
            return None

        except Exception:
            candidate.close()
            return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """
        Closes the underlying gRPC channel
        :return: None
        """
        logger.info("Closing channel for endpoint %s", self.endpoint)
        if hasattr(self, '_channel') and hasattr(self._channel, 'close'):
            self._channel.close()

        for callback in self._cleanup_callbacks:
            callback(self)

    def ready_future(self):
        """
        Creates a future that tracks underlying gRPC channel is ready
        :return: A Future object that matures when the underlying channel is ready
        to receive request
        """
        return grpc.channel_ready_future(self._channel)
