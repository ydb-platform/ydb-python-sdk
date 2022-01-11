#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import threading
import collections

from concurrent.futures import Future
from kikimr.public.sdk.python.persqueue._protobuf import error_response

logger = logging.getLogger(__name__)


class RequestFutureTracker(object):
    def __init__(self, make_result_method, request_type):
        self.__responses = collections.deque()
        self.__futures = collections.deque()
        self.__make_res_method = make_result_method
        self.__request_type = request_type
        self.__lock = threading.RLock()

    def add_request(self):
        f = Future()
        f.set_running_or_notify_cancel()
        with self.__lock:
            if self.__responses:
                assert not self.__futures
                response = self.__responses.popleft()
                f.set_result(self.__make_res_method(response))
            else:
                self.__futures.append(f)
        return f

    def add_response(self, response):
        with self.__lock:
            if self.__futures:
                assert not self.__responses
                f = self.__futures.popleft()
                f.set_result(self.__make_res_method(response))

            else:
                self.__responses.append(response)

    def spoil_all(self):
        while self.__futures:
            f = self.__futures.popleft()
            response = error_response(
                request_type=self.__request_type,
                description="Request dropped as session was closed"
            )
            f.set_result(self.__make_res_method(response))
