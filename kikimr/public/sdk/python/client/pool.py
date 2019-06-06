# -*- coding: utf-8 -*-
import threading
import logging
from concurrent import futures
import collections
import random

from . import connection as connection_impl, issues, resolver, _utilities


logger = logging.getLogger(__name__)


class ConnectionsCache(object):
    def __init__(self):
        self.lock = threading.RLock()
        self.connections = collections.OrderedDict()
        self.outdated = collections.OrderedDict()
        self.subscriptions = set()
        self.preferred = collections.OrderedDict()
        self.logger = logging.getLogger(__name__)

    def add(self, connection, preferred=False):
        if connection is None:
            return False

        connection.add_cleanup_callback(self.remove)
        with self.lock:
            if preferred:
                self.preferred[connection.endpoint] = connection
            self.connections[connection.endpoint] = connection
            subscriptions = list(self.subscriptions)
            self.subscriptions.clear()

        for subscription in subscriptions:
            subscription.set_result(None)
        return True

    def _on_done_callback(self, subscription):
        """
        A done callback for the subscription future
        :param subscription: A subscription
        :return: None
        """
        with self.lock:
            try:
                self.subscriptions.remove(subscription)
            except KeyError:
                return subscription

    @property
    def size(self):
        with self.lock:
            return len(self.connections) - len(self.outdated)

    def already_exists(self, endpoint):
        with self.lock:
            return endpoint in self.connections

    def values(self):
        with self.lock:
            return list(self.connections.values())

    def make_outdated(self, connection):
        with self.lock:
            self.outdated[connection.endpoint] = connection
            return self

    def cleanup_outdated(self):
        with self.lock:
            outdated_connections = list(self.outdated.values())
            for outdated_connection in outdated_connections:
                outdated_connection.close()
        return self

    def cleanup(self):
        with self.lock:
            actual_connections = list(self.connections.values())
            for connection in actual_connections:
                connection.close()

    def subscribe(self):
        with self.lock:
            subscription = futures.Future()
            if len(self.connections) > 0:
                subscription.set_result(None)
                return subscription
            self.subscriptions.add(subscription)
            subscription.add_done_callback(self._on_done_callback)
            return subscription

    def get(self):
        with self.lock:
            try:
                endpoint, connection = self.preferred.popitem(last=False)
                self.preferred[endpoint] = connection
            except KeyError:
                try:
                    endpoint, connection = self.connections.popitem(last=False)
                    self.connections[endpoint] = connection
                except KeyError:
                    raise issues.ConnectionLost("Couldn't find valid connection")

            return connection

    def remove(self, connection):
        with self.lock:
            self.preferred.pop(connection.endpoint, None)
            self.connections.pop(connection.endpoint, None)
            self.outdated.pop(connection.endpoint, None)


class Discovery(threading.Thread):
    def __init__(self, store, driver_config):
        """
        A timer thread that implements endpoints discovery logic
        :param store: A store with endpoints
        :param driver_config: An instance of DriverConfig
        """
        super(Discovery, self).__init__()
        self.logger = logger.getChild(self.__class__.__name__)
        self.condition = threading.Condition()
        self.daemon = True
        self._cache = store
        self._driver_config = driver_config
        self._resolver = resolver.DiscoveryEndpointsResolver(self._driver_config)
        self._base_discovery_interval = 60
        self._ready_timeout = 4
        self._discovery_request_timeout = 2
        self._should_stop = threading.Event()
        self._max_size = 9
        self._base_emergency_retry_interval = 1

    def _emergency_retry_interval(self):
        return (1 + random.random()) * self._base_emergency_retry_interval

    def _discovery_interval(self):
        return (1 + random.random()) * self._base_discovery_interval

    def notify_disconnected(self):
        self._send_wake_up()

    def _send_wake_up(self):
        acquired = self.condition.acquire(blocking=False)

        if not acquired:
            return

        self.condition.notify_all()
        self.condition.release()

    def _handle_empty_database(self):
        if self._cache.size > 0:
            return True

        return self._cache.add(
            connection_impl.Connection.ready_factory(
                self._driver_config.endpoint, self._driver_config, self._ready_timeout
            )
        )

    def execute_discovery(self):
        if self._driver_config.database is None:
            return self._handle_empty_database()

        resolve_details = self._resolver.resolve()
        if resolve_details is None:
            return False

        resolved_endpoints = set(details.endpoint for details in resolve_details.endpoints)
        for cached_endpoint in self._cache.values():
            if cached_endpoint.endpoint not in resolved_endpoints:
                self._cache.make_outdated(cached_endpoint)

        for resolved_endpoint in resolve_details.endpoints:
            if self._cache.size >= self._max_size or self._cache.already_exists(resolved_endpoint.endpoint):
                continue
            endpoint = resolved_endpoint.endpoint
            preferred = resolve_details.self_location == resolved_endpoint.location
            ready_connection = connection_impl.Connection.ready_factory(
                endpoint, self._driver_config, self._ready_timeout)
            self._cache.add(ready_connection, preferred)

        self._cache.cleanup_outdated()

        return self._cache.size > 0

    def stop(self):
        self._should_stop.set()
        self._send_wake_up()

    def run(self):
        with self.condition:
            while True:
                if self._should_stop.is_set():
                    break

                successful = self.execute_discovery()
                if self._should_stop.is_set():
                    break

                interval = self._discovery_interval() if successful else self._emergency_retry_interval()
                self.condition.wait(interval)

            self._cache.cleanup()
        self.logger.info("Successfully terminated discovery process")


class ConnectionPool(object):
    def __init__(self, driver_config):
        """
        An object that encapsulates discovery logic and provides ability to execute user requests
        on discovered endpoints.
        :param driver_config: An instance of DriverConfig
        """
        self._driver_config = driver_config
        self._store = ConnectionsCache()
        self._grpc_init = connection_impl.Connection(self._driver_config.endpoint, self._driver_config)
        self._discovery_thread = Discovery(self._store, self._driver_config)
        self._discovery_thread.start()
        self._stopped = False
        self._stop_guard = threading.Lock()

    def stop(self, timeout=10):
        """
        Stops underlying discovery process and cleanups
        :param timeout: A timeout to wait for stop completion
        :return: None
        """
        with self._stop_guard:
            if self._stopped:
                return

            self._stopped = True
            self._discovery_thread.stop()
        self._grpc_init.close()
        self._discovery_thread.join(timeout)

    def async_wait(self):
        """
        Returns a future to subscribe on endpoints availability.
        :return: A concurrent.futures.Future instance.
        """
        return self._store.subscribe()

    def wait(self, timeout=None):
        """
        Waits for endpoints to be are available to serve user requests
        :param timeout: A timeout to wait in seconds
        :return: None
        """
        self._store.subscribe().result(timeout)

    def _on_disconnected(self, connection):
        """
        Removes bad discovered endpoint and triggers discovery process
        :param connection: A disconnected connection
        :return: None
        """
        connection.close()
        self._discovery_thread.notify_disconnected()

    def __call__(self, request, stub, rpc_name, wrap_result=None, settings=None, wrap_args=()):
        """
        Synchronously sends request constructed by client library
        :param request: A request constructed by client
        :param stub: A stub instance to wrap channel
        :param rpc_name: A name of RPC to be executed
        :param wrap_result: A callable that intercepts call and wraps received response
        :param settings: An instance of BaseRequestSettings that can be used
        for RPC metadata construction
        :param wrap_args: And arguments to be passed into wrap_result callable
        :return: A result of computation
        """
        try:
            connection = self._store.get()
        except Exception:
            self._discovery_thread.notify_disconnected()
            raise

        return connection(
            request, stub, rpc_name, wrap_result, settings,
            wrap_args, lambda: self._on_disconnected(
                connection
            )
        )

    @_utilities.wrap_async_call_exceptions
    def future(self, request, stub, rpc_name, wrap_result=None, settings=None, wrap_args=()):
        """
        Sends request constructed by client
        :param request: A request constructed by client
        :param stub: A stub instance to wrap channel
        :param rpc_name: A name of RPC to be executed
        :param wrap_result: A callable that intercepts call and wraps received response
        :param settings: An instance of BaseRequestSettings that can be used
        for RPC metadata construction
        :param wrap_args: And arguments to be passed into wrap_result callable
        :return: A future of computation
        """
        try:
            connection = self._store.get()
        except Exception:
            self._discovery_thread.notify_disconnected()
            raise

        return connection.future(
            request, stub, rpc_name, wrap_result, settings,
            wrap_args, lambda: self._on_disconnected(
                connection
            )
        )

    def __enter__(self):
        """
        In some cases (scripts, for example) this context manager can be used.
        :return:
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
