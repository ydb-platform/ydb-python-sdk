# -*- coding: utf-8 -*-
import logging
import threading
import random
import itertools
from . import connection as conn_impl, issues, settings as settings_impl, _apis

logger = logging.getLogger(__name__)


class EndpointInfo(object):
    __slots__ = ('address', 'endpoint', 'location', 'port', 'ssl')

    def __init__(self, endpoint_info):
        self.address = endpoint_info.address
        self.endpoint = "%s:%s" % (endpoint_info.address, endpoint_info.port)
        self.location = endpoint_info.location
        self.port = endpoint_info.port
        self.ssl = endpoint_info.ssl

    def __str__(self):
        return "<Endpoint %s, location %s, ssl: %s>" % (self.endpoint, self.location, self.ssl)

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return hash(self.endpoint)

    def __eq__(self, other):
        if not hasattr(other, 'endpoint'):
            return False

        return self.endpoint == other.endpoint


def _list_endpoints_request_factory(connection_params):
    request = _apis.ydb_discovery.ListEndpointsRequest()
    request.database = connection_params.database
    return request


class DiscoveryResult(object):
    def __init__(self, self_location, endpoints):
        self.self_location = self_location
        endpoints = list(set(endpoints))
        random.shuffle(endpoints)
        self.endpoints = list(
            sorted(
                endpoints,
                key=lambda x: self.self_location != x.location
            )
        )

    def __str__(self):
        return "DiscoveryResult <self_location: %s, endpoints %s>" % (self.self_location, self.endpoints)

    def __repr__(self):
        return self.__str__()

    @classmethod
    def from_response(cls, rpc_state, response):
        issues._process_response(response.operation)
        message = _apis.ydb_discovery.ListEndpointsResult()
        response.operation.result.Unpack(message)
        return cls(
            message.self_location, list(
                EndpointInfo(info)
                for info in message.endpoints
            )
        )


class DiscoveryEndpointsResolver(object):
    def __init__(self, driver_config):
        self.logger = logger.getChild(self.__class__.__name__)
        self._driver_config = driver_config
        self._request_timeout = 3
        self._ready_timeout = 2
        self._lock = threading.Lock()
        self._debug_details_history_size = 20
        self._debug_details_items = []
        self._endpoints = []
        self._endpoints.append(driver_config.endpoint)
        self._endpoints.extend(driver_config.endpoints)
        random.shuffle(self._endpoints)
        self._endpoints_iter = itertools.cycle(self._endpoints)

    def _add_debug_details(self, message, *args):
        self.logger.debug(message, *args)
        message = message % args
        with self._lock:
            self._debug_details_items.append(message)
            if len(self._debug_details_items) > self._debug_details_history_size:
                self._debug_details_items.pop()

    def debug_details(self):
        """
        Returns last resolver errors as a debug string.
        """
        with self._lock:
            return "\n".join(self._debug_details_items)

    def resolve(self):
        self.logger.debug("Preparing initial endpoint to resolve endpoints")
        endpoint = next(self._endpoints_iter)
        initial = conn_impl.Connection.ready_factory(endpoint, self._driver_config)
        if initial is None:
            self._add_debug_details("Failed to establish connection to YDB discovery endpoint: \"%s\". Check endpoint correctness." % endpoint)
            return None

        self.logger.debug("Resolving endpoints for database %s", self._driver_config.database)
        try:
            resolved = initial(
                _list_endpoints_request_factory(self._driver_config),
                _apis.DiscoveryService.Stub,
                _apis.DiscoveryService.ListEndpoints,
                DiscoveryResult.from_response,
                settings=settings_impl.BaseRequestSettings().with_timeout(
                    self._request_timeout
                )
            )

            self._add_debug_details(
                "Resolved endpoints for database %s: %s", self._driver_config.database, resolved)

            return resolved
        except Exception as e:

            self._add_debug_details(
                "Failed to resolve endpoints for database %s. Endpoint: \"%s\". Error details:\n %s", self._driver_config.database, endpoint, e)

        finally:
            initial.close()

        return None
