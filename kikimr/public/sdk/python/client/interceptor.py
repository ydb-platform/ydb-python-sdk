# -*- coding: utf-8 -*-
import grpc
from concurrent import futures
from grpc._cython import cygrpc
from grpc._channel import _handle_event, _EMPTY_FLAGS


def patch_async_iterator(it, wrapper):
    def _handle_future(self, f):
        if self._state.response is not None:
            response = self._state.response
            self._state.response = None
            try:
                f.set_result(wrapper(response))
            except Exception as e:
                f.set_exception(e)
        elif cygrpc.OperationType.receive_message not in self._state.due:
            if self._state.code is grpc.StatusCode.OK:
                f.set_exception(StopIteration())
            elif self._state.code is not None:
                f.set_exception(self)

    def _event_handler(state, response_deserializer, f, self):
        def handle_event(event):
            with state.condition:
                callbacks = _handle_event(event, state, response_deserializer)
                state.condition.notify_all()
                done = not state.due
                _handle_future(self, f)
            for callback in callbacks:
                callback()
            return done and state.fork_epoch >= cygrpc.get_fork_epoch()
        return handle_event

    def _next(self):
        with self._state.condition:
            future = futures.Future()
            if self._state.code is None:
                event_handler = _event_handler(self._state,
                                               self._response_deserializer, future, self)
                operating = self._call.operate(
                    (cygrpc.ReceiveMessageOperation(_EMPTY_FLAGS),),
                    event_handler)
                if operating:
                    self._state.due.add(cygrpc.OperationType.receive_message)
                return future
            elif self._state.code is grpc.StatusCode.OK:
                raise StopIteration()
            else:
                raise self

    it._next = lambda: _next(it)
    return it
