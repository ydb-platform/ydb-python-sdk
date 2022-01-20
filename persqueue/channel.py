#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

import kikimr.yndx.api.grpc.persqueue_pb2_grpc as pqv0_server
import ydb.public.api.grpc.draft.ydb_persqueue_v1_pb2_grpc as pqv1_server
from ydb.pool import ConnectionPool
from ydb.settings import BaseRequestSettings


_MAX_MESSAGE_SIZE = 130 * 2 ** 20
_STATUS_OK = 1
_CONNECT_OPTIONS = [
    ('grpc.max_receive_message_length', _MAX_MESSAGE_SIZE),
    ('grpc.max_send_message_length', _MAX_MESSAGE_SIZE),
    ('grpc.primary_user_agent', 'lb_python_pqlib')
]


logger = logging.getLogger(__name__)


class PQConnectionPool(ConnectionPool):
    def __init__(self, driver_config, generation):
        super(PQConnectionPool, self).__init__(driver_config)
        self.__started = False
        self.__connected = False
        self.__generation = generation

    def async_wait(self):
        self.__started = True
        return super(PQConnectionPool, self).async_wait()

    @property
    def started(self):
        return self.__started

    @property
    def connected(self):
        return self.__connected

    @property
    def generation(self):
        return self.__generation

    def ready(self):
        self.__connected = True

    def invoke(self, request, method, timeout=None):
        if timeout is None:
            timeout = 5 * 365 * 24 * 3600  # Can't use infinity as YDB SDK overrides timeout=None
        return self(
            request, pqv0_server.PersQueueServiceStub, method,
            settings=BaseRequestSettings().with_operation_timeout(timeout).with_timeout(timeout)
        )

    def stop(self, timeout=0):
        logger.debug("Stopping connection pool")
        super(PQConnectionPool, self).stop(timeout)

    def run_cds_request_async(self, request_factory, **params):
        request = request_factory(**params)
        logger.debug("Sending cds request: {}".format(request))
        return self.future(request, pqv1_server.ClusterDiscoveryServiceStub, "DiscoverClusters")
