# -*- coding: utf-8 -*-
import grpc
import functools
from concurrent import futures
from grpc._cython import cygrpc
from grpc._channel import _handle_event, _EMPTY_FLAGS, _start_unary_request, _InitialMetadataFlags, _RPCState
from grpc._channel import _UNARY_STREAM_INITIAL_DUE, _Rendezvous, _channel_managed_call_management, _common


def _handle_future(state):
    if getattr(state, 'last_future', None) is None:
        # nothing to handle actually
        return

    if state.response is not None:
        response = state.response
        state.response = None
        if not state.last_future.done():
            try:
                state.last_future.set_result(state.response_wrapper(response))
            except Exception as e:
                state.last_future.set_exception(e)
    elif cygrpc.OperationType.receive_message not in state.due:
        if state.code is grpc.StatusCode.OK:
            if not state.last_future.done():
                state.last_future.set_exception(
                    StopIteration())
        elif state.code is not None:
            if not state.last_future.done():
                state.last_future.set_exception(
                    state.rendezvous)


def _event_handler_patched(state, response_deserializer):
    def handle_event(event):
        with state.condition:
            callbacks = _handle_event(event, state, response_deserializer)
            state.condition.notify_all()
            done = not state.due
            _handle_future(state)
        for callback in callbacks:
            callback()
        return done and state.fork_epoch >= cygrpc.get_fork_epoch()
    return handle_event


def patch_async_iterator(it, wrapper):
    def _next(self):
        with self._state.condition:
            future = futures.Future()
            self._state.rendezvous = self
            self._state.last_future = future
            self._state.response_wrapper = wrapper
            if self._state.code is None:
                event_handler = _event_handler_patched(self._state,
                                                       self._response_deserializer)
                operating = self._call.operate(
                    (cygrpc.ReceiveMessageOperation(_EMPTY_FLAGS),),
                    event_handler)
                if operating:
                    self._state.due.add(cygrpc.OperationType.receive_message)
            elif self._state.code is grpc.StatusCode.OK:
                future.set_exception(StopIteration())
            else:
                future.set_exception(self)
            return future

    it._next = functools.partial(_next, it)
    return it


class _UnaryStreamMultiCallablePatched(grpc.UnaryStreamMultiCallable):

    # pylint: disable=too-many-arguments
    def __init__(self, channel, managed_call, method, request_serializer,
                 response_deserializer):
        self._channel = channel
        self._managed_call = managed_call
        self._method = method
        self._request_serializer = request_serializer
        self._response_deserializer = response_deserializer
        self._context = cygrpc.build_census_context()

    def __call__(self,
                 request,
                 timeout=None,
                 metadata=None,
                 credentials=None,
                 wait_for_ready=None):
        deadline, serialized_request, rendezvous = _start_unary_request(
            request, timeout, self._request_serializer)
        initial_metadata_flags = _InitialMetadataFlags().with_wait_for_ready(
            wait_for_ready)
        if serialized_request is None:
            raise rendezvous  # pylint: disable-msg=raising-bad-type
        else:
            state = _RPCState(_UNARY_STREAM_INITIAL_DUE, None, None, None, None)
            operationses = (
                (
                    cygrpc.SendInitialMetadataOperation(metadata,
                                                        initial_metadata_flags),
                    cygrpc.SendMessageOperation(serialized_request,
                                                _EMPTY_FLAGS),
                    cygrpc.SendCloseFromClientOperation(_EMPTY_FLAGS),
                    cygrpc.ReceiveStatusOnClientOperation(_EMPTY_FLAGS),
                ),
                (cygrpc.ReceiveInitialMetadataOperation(_EMPTY_FLAGS),),
            )
            event_handler = _event_handler_patched(state, self._response_deserializer)
            call = self._managed_call(
                cygrpc.PropagationConstants.GRPC_PROPAGATE_DEFAULTS,
                self._method, None, deadline, metadata, None
                if credentials is None else credentials._credentials,
                operationses, event_handler, self._context)
            return _Rendezvous(state, call, self._response_deserializer,
                               deadline)


def patch_unary_stream_on_channel(channel):

    def unary_stream(self,
                     method,
                     request_serializer=None,
                     response_deserializer=None):
        return _UnaryStreamMultiCallablePatched(
            self._channel, _channel_managed_call_management(self._call_state),
            _common.encode(method), request_serializer, response_deserializer)

    channel.unary_stream = functools.partial(unary_stream, channel)
    return channel
