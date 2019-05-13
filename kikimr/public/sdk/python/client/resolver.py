# -*- coding: utf-8 -*-
import logging

from kikimr.public.sdk.python.client import connection as conn_impl
from kikimr.public.sdk.python.client import issues
from kikimr.public.api.protos import ydb_discovery_pb2
from kikimr.public.sdk.python.client import settings as settings_impl
from kikimr.public.api.grpc import ydb_discovery_v1_pb2_grpc as ydb_discovery_pb2_grpc

logger = logging.getLogger(__name__)


_ListEndpoints = 'ListEndpoints'


class EndpointInfo(object):
    __slots__ = ('endpoint', 'location', 'port')

    def __init__(self, endpoint_info):
        self.endpoint = "%s:%s" % (endpoint_info.address, endpoint_info.port)
        self.location = endpoint_info.location
        self.port = endpoint_info.port

    def __str__(self):
        return "<Endpoint %s, location %s>" % (self.endpoint, self.location)

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return hash(self.endpoint)

    def __eq__(self, other):
        if not hasattr(other, 'endpoint'):
            return False

        return self.endpoint == other.endpoint


def _list_endpoints_request_factory(connection_params):
    request = ydb_discovery_pb2.ListEndpointsRequest()
    request.database = connection_params.database
    return request


class DiscoveryResult(object):
    def __init__(self, self_location, endpoints):
        self.self_location = self_location
        self.endpoints = list(
            reversed(
                sorted(
                    endpoints,
                    key=lambda x: self.self_location == x.location
                )
            )
        )

    def __str__(self):
        return "DiscoveryResult <self_location: %s, endpoints %s>" % (self.self_location, self.endpoints)

    def __repr__(self):
        return self.__str__()

    @classmethod
    def from_response(cls, response):
        issues._process_response(response)
        message = ydb_discovery_pb2.ListEndpointsResult()
        response.result.Unpack(message)
        return cls(
            message.self_location,
            list(
                set(
                    EndpointInfo(info)
                    for info in message.endpoints
                )
            )
        )


class DiscoveryEndpointsResolver(object):
    def __init__(self, driver_config):
        self.logger = logger.getChild(self.__class__.__name__)
        self._driver_config = driver_config
        self._request_timeout = 3
        self._ready_timeout = 2

    def resolve(self):
        self.logger.debug("Preparing initial endpoint to resolve endpoints")
        initial = conn_impl.Connection.ready_factory(self._driver_config.endpoint, self._driver_config)
        if initial is None:
            self.logger.info("Failed to prepare initial endpoint to resolve endpoints")
            return None

        self.logger.debug("Resolving endpoints for database %s", self._driver_config.database)
        try:
            resolved = initial(
                _list_endpoints_request_factory(self._driver_config),
                ydb_discovery_pb2_grpc.DiscoveryServiceStub,
                _ListEndpoints,
                DiscoveryResult.from_response,
                settings=settings_impl.BaseRequestSettings().with_timeout(
                    self._request_timeout
                )
            )

            self.logger.debug("Resolved endpoints for database %s: %s", self._driver_config.database, resolved)
            return resolved
        except Exception as e:

            self.logger.info(
                "Failed to resolve endpoints for database %s, details: %s", self._driver_config.database, e)

        finally:
            initial.close()

        return None
