#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import threading

import grpc
from six.moves import queue

from kikimr.public.sdk.python.persqueue._events import ResponseReceivedEvent
from kikimr.public.sdk.python.persqueue.errors import SessionFailureResult, SessionDeathReason


_TERMINATE_MARKER = 'END_OF_SESSION'

logger = logging.getLogger(__name__)


def requests_generator(requests_queue):
    while True:
        request = requests_queue.get(block=True)
        if request == _TERMINATE_MARKER:
            break
        yield request


def send_requests(client, lock, method, requests_queue, responses_queue, session_id):
    try:
        with lock:
            responses_iter = client.invoke(requests_generator(requests_queue), method=method)
    except Exception:
        responses_queue.put(
            ResponseReceivedEvent(
                session_uid=session_id,
                response=SessionFailureResult(
                    reason=SessionDeathReason.HostConnectionFailed,
                    description="Init session request failed with exception. Suppose connection troubles"
                )
            )
        )
        return

    reason = SessionDeathReason.ClosedUnexpectedly
    logger.debug("Session with method %s created", method)
    try:
        for response in responses_iter:
            responses_queue.put(
                ResponseReceivedEvent(
                    session_uid=session_id, response=response
                )
            )
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.UNAVAILABLE:
            reason = SessionDeathReason.HostConnectionFailed
        logger.debug("gRPC session failed with exception: %s", e)
    finally:
        responses_queue.put(
            ResponseReceivedEvent(
                session_uid=session_id,
                response=SessionFailureResult(
                    reason=reason
                )
            )
        )


class GRPCSingleSessionClient(object):
    def __init__(self, client, client_lock, method, responses_queue, my_session_id):
        self.__requests_queue = queue.Queue()
        self.__main_thread = threading.Thread(
            target=send_requests,
            args=(client, client_lock, method, self.__requests_queue, responses_queue, my_session_id),
            name="PQ lib grpc stream thread"
        )
        self.__main_thread.daemon = True

        self.__started = False

    def send_request(self, request):
        self.__requests_queue.put(request)

    def start(self):
        self.__main_thread.start()
        self.__started = True

    def stop(self):
        if self.__started:
            self.send_request(_TERMINATE_MARKER)
            self.__started = False
            self.__main_thread.join()

    def __del__(self):
        self.stop()

    @property
    def started(self):
        return self.started
