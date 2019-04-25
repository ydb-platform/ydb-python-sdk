#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import threading
import collections

from kikimr.public.sdk.python.persqueue._protobuf import error_response

logger = logging.getLogger(__name__)


class RequestFutureTracker(object):
    def __init__(self, future_ready_callback, request_type):
        self.__results = collections.deque()
        self.__future_ids = collections.deque()
        self.__future_ready_callback = future_ready_callback
        self.__request_type = request_type
        self.__lock = threading.RLock()

    def add_future(self, future_id):
        with self.__lock:
            if self.__results:
                assert not self.__future_ids
                result = self.__results.popleft()
                self.__future_ready_callback(future_id, result)
            else:
                self.__future_ids.append(future_id)

    def add_result(self, result):
        with self.__lock:
            if self.__future_ids:
                assert not self.__results
                future_id = self.__future_ids.popleft()
                self.__future_ready_callback(future_id, result)
            else:
                self.__results.append(result)

    def spoil_all(self):
        while self.__future_ids:
            self.__future_ready_callback(
                self.__future_ids.popleft(),
                error_response(
                    request_type=self.__request_type,
                    description="Request dropped as session was closed"
                )
            )
