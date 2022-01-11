#!/usr/bin/env python
# -*- coding: utf-8 -*-

import abc
import itertools
import logging
import collections
import time
import threading
import six

from concurrent.futures import Future
from six.moves import queue

import kikimr.public.api.protos.draft.persqueue_error_codes_pb2 as pq_err_codes
from kikimr.public.sdk.python.persqueue._util import RequestFutureTracker

from kikimr.public.sdk.python.persqueue._grpc import GRPCSingleSessionClient
from kikimr.public.sdk.python.persqueue.errors import ActorNotReadyException, SessionClosedException
from kikimr.public.sdk.python.persqueue.errors import SessionFailureResult, SessionDeathReason
from kikimr.public.sdk.python.persqueue.errors import ActorTerminatedException

import kikimr.public.sdk.python.persqueue._events as _events
from kikimr.public.sdk.python.persqueue._protobuf import locked_request
from kikimr.public.sdk.python.persqueue._protobuf import WRITE_STREAM_METHOD, write_init_request, write_request, write_request_batch
from kikimr.public.sdk.python.persqueue._protobuf import READ_STREAM_METHOD, read_init_request, read_request
from kikimr.public.sdk.python.persqueue._protobuf import RequestTypes, commit_request
from kikimr.public.sdk.python.persqueue._protobuf import cds_write_session_request, process_cds_response

from kikimr.public.sdk.python.persqueue.channel import PQConnectionPool

logger = logging.getLogger(__name__)
MAGIC_COOKIE_VALUE = 123456789


def make_endpoint(host, port):
    return "{}:{}".format(host, port)


class _Watcher(threading.Thread):
    def __init__(self, queue, event_processor, wakeup_timeouts=3.0, *args, **kwargs):
        super(_Watcher, self).__init__()
        self.name = "PQ lib watcher"
        self.__queue = queue
        self.__target = event_processor
        self._timeout = wakeup_timeouts
        self.__scheduled_events = {}
        self.__args = args
        self.__kwargs = kwargs
        self.__finished = threading.Event()

    def cancel(self):
        """Stop the watcher"""
        self.__finished.set()

    def run(self):
        while not self.__finished.is_set():
            curr_time = time.time()
            processed_events = []
            for target_time, events in self.__scheduled_events.items():
                if curr_time > target_time:
                    for event in events:
                        logger.debug("Watcher called scheduled event")
                        self.__target(event, *self.__args, **self.__kwargs)
                    processed_events.append(target_time)
            for t in processed_events:
                del self.__scheduled_events[t]
            try:
                event = self.__queue.get(block=True, timeout=self._timeout)
                if hasattr(event, "schedule_after"):
                    logger.debug("Watcher got scheduled event")
                    event_call_time = time.time() + event.schedule_after
                    self.__scheduled_events.setdefault(event_call_time, []).append(event)
                else:
                    # noinspection PyArgumentList
                    self.__target(event, *self.__args, **self.__kwargs)
            except queue.Empty:
                continue


class MultiSessionStreamClient(object):
    """
    Container class user for starting and handling several PQ Stream sessions in single KikimrClient
    (and therefore single connection)

    """
    CreateSessionData = collections.namedtuple(
        'CdsRequestData',
        ["session_id", "method", "cds_params", "timeout"]
    )
    ActiveSessionData = collections.namedtuple(
        'ActiveSessionData',
        ["endpoint", "session", "generation"]
    )

    def __init__(self, responses_queue, base_host, port, driver_config_factory, use_cds, timeout=60):
        self.__driver_config_factory = driver_config_factory
        self.__use_cds = use_cds
        self.__base_endpoint = make_endpoint(base_host, port)
        self.__port = port
        self.__base_config = driver_config_factory(self.__base_endpoint)

        self.__client_lock = threading.RLock()
        self.__internal_lock = threading.RLock()
        self.__session_id_counter = itertools.count()
        self.__watcher_queue = queue.Queue()
        self.__watcher = _Watcher(self.__watcher_queue, self.__start_connection, wakeup_timeouts=0.1)
        self.__watcher.daemon = True
        self.__active_sessions = {}
        self.__responses_queue = responses_queue
        self._timeout = timeout

        self.__cds_pending_queue = queue.Queue()
        self.__cds_requested_queue = {}
        self.__session_create_queue = {}

        self.__connections = {}
        self.__connection_generations = {}

    def start(self):
        """
        Initial start of the client
        """
        self.__watcher.start()
        self.__get_connection(self.__base_endpoint)

    def create_new_session(self, method, session_id=None, timeout=60, **cds_params):
        with self.__internal_lock:
            if session_id is not None:
                assert self.__active_sessions[session_id] is None
            else:
                session_id = next(self.__session_id_counter)
        logger.debug("Will create new {} session with id {}".format(method, session_id))
        session_data = self.CreateSessionData(session_id, method=method, timeout=timeout, cds_params=cds_params)
        if self.__use_cds:
            self.__do_cds_request(session_data)
        else:
            with self.__internal_lock:
                connection = self.__get_connection(self.__base_endpoint)
                if connection.connected:
                    self.__make_new_session(session_data, connection, self.__base_endpoint)
                else:
                    self.__session_create_queue.setdefault(
                        self.__base_endpoint, queue.Queue()
                    ).put(session_data)
        return session_id

    def start_session(self, session_id):
        logger.debug("Starting session %s", session_id)
        self.__active_sessions[session_id].session.start()

    def destroy_session(self, session_id):
        """
        Terminate the session.
        :param session_id:
        :return: None
        """
        self.__active_sessions[session_id].session.stop()
        del self.__active_sessions[session_id]

    def notify_connect_failed(self, session_id):
        with self.__internal_lock:
            session_data = self.__active_sessions[session_id]
            generation = session_data.generation
            do_disconnect = generation == self.__connection_generations[session_data.endpoint]
        if do_disconnect:
            logger.info("Got connection failed signal from session {}".format(session_id))
            self.__disconnected(session_id=session_id)
        else:
            logger.debug("Ignored connection failed signal from session {} to endpoint ".format(session_id))

    def send_request_to_session(self, session_id, request):
        assert session_id in self.__active_sessions
        return self.__active_sessions[session_id].session.send_request(request)

    def set_proxy_cookie_and_send_request(self, session_id, get_full_request_method):
        request = get_full_request_method(MAGIC_COOKIE_VALUE)
        self.send_request_to_session(session_id, request)

    def __get_connection(self, endpoint):
        with self.__internal_lock:
            if endpoint in self.__connections:
                return self.__connections[endpoint]
            logger.info("Create connection to: {}".format(endpoint))
            generation = self.__connection_generations.setdefault(endpoint, 0) + 1
            self.__connection_generations[endpoint] = generation
            connection = PQConnectionPool(self.__driver_config_factory(endpoint), generation)
            self.__connections[endpoint] = connection
            self.__watcher_queue.put(_events.SessionClientReconnectEvent(0.1 if generation < 2 else 1, endpoint))
            return connection

    def __start_connection(self, start_connection_event):
        endpoint = start_connection_event.endpoint
        logger.info("Start connection to: {}".format(endpoint))
        connection = self.__get_connection(endpoint)
        with self.__internal_lock:
            f = connection.async_wait()
            f.add_done_callback(lambda future: self.__connected(endpoint, future))

    def __connected(self, endpoint, future):
        """
        Connection established event.
        That could be initial start or reestablished connection after failure.
        """
        if future.exception() is not None:
            logger.warning("Connection failed with error: {}".format(future.exception()))
            self.__disconnected(None, endpoint)
        elif future.result() is None:
            logger.info("Connection to {} established".format(endpoint))
            with self.__internal_lock:
                connection = self.__connections.get(endpoint, None)
                assert connection is not None
                assert not connection.connected
                connection.ready()

            if endpoint == self.__base_endpoint:
                self.__responses_queue.put(_events.ConnectionReadyEvent(future, endpoint))
                self.__process_cds_queue()
            self.__process_create_queue(endpoint)

    def __disconnected(self, session_id=None, endpoint=None):
        if session_id is not None:
            with self.__internal_lock:
                session_data = self.__active_sessions.get(session_id)
                assert session_data is not None
                endpoint = session_data.endpoint
        logger.info("Terminated connection to {}".format(endpoint))
        with self.__internal_lock:
            connection = self.__connections.get(endpoint, None)
            if connection is None:
                return
            del self.__connections[endpoint]
        connection.stop(0)

    def __process_cds_queue(self):
        connection = self.__get_connection(self.__base_endpoint)
        with self.__internal_lock:
            if not connection.connected:
                return
            while not self.__cds_pending_queue:
                cds_data = self.__cds_pending_queue.get_nowait()
                self.__exec_cds_request(cds_data, connection)

    def __process_scheduled_event(self, event):
        pass

    def __process_create_queue(self, endpoint):
        logger.debug("Process create session queue for endpoint: {}".format(endpoint))
        with self.__internal_lock:
            q = self.__session_create_queue.get(endpoint, None)
            connection = self.__get_connection(endpoint)
            assert connection.connected
        if q is None:
            return
        while not q.empty():
            session_data = q.get_nowait()
            self.__make_new_session(session_data, connection, endpoint)

    def __do_cds_request(self, session_data):
        if session_data.method != WRITE_STREAM_METHOD:
            raise NotImplementedError(
                "CDS is only supported for write sessions. If you want to read,"
                "please create SDK instance with use_cds = False"
            )
        connection = self.__get_connection(self.__base_endpoint)
        with self.__internal_lock:
            if not connection.connected:
                self.__cds_pending_queue.put(session_data)
                return
        self.__exec_cds_request(session_data, connection)

    def __exec_cds_request(self, request_data, connection):
        with self.__internal_lock:
            assert request_data.session_id not in self.__cds_requested_queue
            self.__cds_requested_queue[request_data.session_id] = request_data
        f = connection.run_cds_request_async(cds_write_session_request, **request_data.cds_params)
        f.add_done_callback(lambda future: self.__process_cds_response(request_data.session_id, future))

    def __process_cds_response(self, session_id, future):
        logger.debug("Processing cds response: {}".format(future.result()))
        with self.__internal_lock:
            session_data = self.__cds_requested_queue.get(session_id, None)
            assert session_data is not None
            del self.__cds_requested_queue[session_id]
        endpoint = make_endpoint(process_cds_response(future.result()), self.__port)
        logger.debug("Got endpoint from cds: {}".format(endpoint))
        if endpoint is None:
            self.__cds_pending_queue.put(session_data)
            return self.__process_cds_queue()
        connection = self.__get_connection(endpoint)
        with self.__internal_lock:
            if not connection.connected:
                self.__session_create_queue.setdefault(endpoint, queue.Queue()).put(session_data)

    def __make_new_session(self, session_data, connection, endpoint):
        assert connection.connected
        logger.debug("Making new session {} with id {} on endpoint {}".format(
            session_data.method, session_data.session_id, endpoint
        ))
        session = GRPCSingleSessionClient(
            connection, self.__client_lock, session_data.method, self.__responses_queue, session_data.session_id,
            timeout=session_data.timeout
        )
        self.__active_sessions[session_data.session_id] = self.ActiveSessionData(endpoint, session, connection.generation)
        self.__responses_queue.put(_events.session_created_event(session_id=session_data.session_id))
        return session_data.session_id

    def stop(self):
        for session_data in self.__active_sessions.values():
            if session_data.session is not None:
                session_data.session.stop()
        with self.__internal_lock:
            for _, connection in self.__connections.items():
                connection.stop()
            self.__connections.clear()
        self.__watcher.cancel()

    def __del__(self):
        self.stop()

    @staticmethod
    def factory(base_host, port, driver_config_factory, use_cds=False):
        return lambda responses_queue: MultiSessionStreamClient(
            responses_queue, base_host, port, driver_config_factory, use_cds
        )


@six.add_metaclass(abc.ABCMeta)
class AbstractStreamSession(object):
    def __init__(self, stream_client, my_actor, method, register_session_callback, timeout):
        self.__stream_client = stream_client
        self.__actor = my_actor
        self.__session_id = None
        self.__alive = False
        self.__dead = False
        self._method = method
        self.__register_callback = register_session_callback
        self._timeout = timeout

    def _set_alive(self, init_response=None):
        assert not self.__alive
        self.__alive = True
        self._actor.session_started(self._name, init_response)

    @property
    def _is_alive(self):
        return self.__alive

    @property
    def _dead(self):
        return self.__dead

    @property
    def _name(self):
        return self._method

    @property
    def _stream_client(self):
        return self.__stream_client

    @property
    def _register_callback(self):
        return self.__register_callback

    @property
    def _actor(self):
        return self.__actor

    @property
    def _session_id(self):
        return self.__session_id

    def _get_cds_params(self):
        return {}

    @abc.abstractproperty
    def _init_request_factory(self):
        pass

    def _process_init_response(self, response):
        if not response.HasField('init'):
            raise RuntimeError("Init read session response is probably malformed: {}".format(response))
        self._set_alive(response)

    def start(self):
        """
        Prepare the session. Create new GRPC stream. _events.SESSION_CREATED_MARKER will be send back when stream is ready.
        """
        self.__session_id = self._stream_client.create_new_session(
            self._method, session_id=None, timeout=self._timeout, **self._get_cds_params()
        )
        if self._session_id is None:
            self.die(
                reason=SessionFailureResult(
                    SessionDeathReason.HostConnectionFailed,
                    description="Session initialization failed! "
                                "Client had lost connection and didn't reconnect by now",
                )
            )
            return

        self.__register_callback(self._session_id, self.process_response)

    def session_created(self):
        """
        Actually start the session. Send session-init request.
        Init responses will be processed later in _process_init_response
        Session will be fully initialized only after getting and processing init response
        """
        self._stream_client.start_session(self._session_id)
        self._stream_client.set_proxy_cookie_and_send_request(self._session_id, self._init_request_factory)
        logger.debug("Session {} created, waiting for init response".format(self.__session_id))

    def send_request(self, request, result_future_id):
        """
        Send request to GRPC stream, async. Result will be reported to future with id specified.
        :param request:
        :param result_future_id:
        :return:
        """
        self._stream_client.send_request_to_session(self._session_id, request)

    def process_response(self, response):
        if isinstance(response, SessionFailureResult):
            if response.reason == SessionDeathReason.HostConnectionFailed:
                logger.debug("Session {} failed with error: {}".format(self.__session_id, response))
                self._stream_client.notify_connect_failed(self.__session_id)
            self.die(response)
            return None
        elif self._dead:
            return False
        elif response == _events.SESSION_CREATED_MARKER:
            self.session_created()
        elif response.HasField('error'):
            logger.debug("Session {} will die due to error: {}".format(self.__session_id, response))
            self.die(
                SessionFailureResult(reason=SessionDeathReason.FailedWithError, description=response)
            )
        elif not self.__alive:
            return self._process_init_response(response)
        else:
            return self._actor.response_ready(response)

    def die(self, reason=None, notify_actor=True):
        """
        Terminate the stream.

        Close session, get all responses already queued (as result of destroy_session() call) and answer them
        For all requests pending infly set Error as the result.
        Notify actor via session_failed() call.
        :param reason:
        :param notify_actor: Set to notify upstanding actor of session death. May be set to False if die() initiated
         by the actor itself.
        :return:
        """

        if self.__dead:
            return
        logger.debug("Session {} will now die".format(self._session_id))
        if reason is not None:
            logger.debug("Reason: {}, description: {}".format(reason.reason, reason.description))

        self.__alive = False
        if self._session_id is not None:
            self.__register_callback(self._session_id, None)
            self._stream_client.destroy_session(self._session_id)
        self.__dead = True
        if notify_actor:
            logger.debug("Session {} is dead, will now notify actor".format(self._session_id))
            self._actor.session_failed(self._name, reason)

    def __del__(self):
        # noinspection PyBroadException
        try:
            self.die()
        except Exception:
            pass


class WriteStreamSession(AbstractStreamSession):
    # noinspection PyProtectedMember
    def __init__(self, stream_client, my_actor, register_session_callback, configurator):
        super(WriteStreamSession, self).__init__(
            stream_client, my_actor, method=WRITE_STREAM_METHOD, register_session_callback=register_session_callback,
            timeout=configurator.deadline
        )
        self.__write_init_factory = lambda cookie: write_init_request(
            configurator=configurator, proxy_cookie=cookie, credentials_proto=self._actor._credentials_proto
        )
        self.__cds_params = {
            "topic": configurator.topic, "source_id": configurator.source_id,
            "partition_group": configurator.partition_group, "preferred_cluster": configurator.preferred_datacenter
        }

    @property
    def _init_request_factory(self):
        return self.__write_init_factory

    def _get_cds_params(self):
        return self.__cds_params

    def write(self, result_future_id, **kwargs):
        # noinspection PyArgumentList
        request = write_request(**kwargs)
        self.send_request(request, result_future_id)

    def write_batch(self, result_future_id, **kwargs):
        # noinspection PyArgumentList
        request = write_request_batch(**kwargs)
        self.send_request(request=request, result_future_id=result_future_id)


class ReadCommitStreamSession(AbstractStreamSession):
    # noinspection PyProtectedMember
    def __init__(
            self, stream_client, my_actor, register_session_callback, configurator
    ):
        super(ReadCommitStreamSession, self).__init__(
            stream_client, my_actor, method=READ_STREAM_METHOD, register_session_callback=register_session_callback,
            timeout=configurator.deadline
        )
        self.__read_init_factory = lambda cookie: read_init_request(
            configurator, proxy_cookie=cookie, credentials_proto=self._actor._credentials_proto
        )

    @property
    def _init_request_factory(self):
        return self.__read_init_factory

    def read(self, result_future_id, **kwargs):
        return self.send_request(read_request(**kwargs), result_future_id)

    def commit(self, result_future_id, **kwargs):
        return self.send_request(commit_request(**kwargs), result_future_id)

    def locked(self, result_future_id, **kwargs):
        request = locked_request(**kwargs)
        self.send_request(request, result_future_id)


class RetryingWriteSession(WriteStreamSession):
    def __init__(self, stream_client, my_actor, register_session_callback, configurator):
        super(RetryingWriteSession, self).__init__(
            stream_client, my_actor, register_session_callback, configurator
        )
        self.__requests_infly = collections.deque()
        self.__alive = False
        self.__started = False
        self.__dead = False

        self.__session_id = None

    @property
    def _session_id(self):
        return self.__session_id

    def start(self):
        self.__session_id = self._stream_client.create_new_session(self._method, timeout=self._timeout)
        logger.debug("Retrying session (re)starting, session id: {}".format(self.__session_id))
        self._register_callback(self.__session_id, self.process_response)

    def __session_created(self):
        self._stream_client.start_session(self.__session_id)
        logger.debug("Retrying session started, sending init request")
        self._stream_client.set_proxy_cookie_and_send_request(self.__session_id, self._init_request_factory)
        logger.debug("Retrying session is waiting for init response")

    def send_request(self, request, result_future_id):
        """
        Send request to GRPC stream, async. Result will be reported to future with id specified.
        :param request:
        :param result_future_id:
        :return:
        """
        if self.__alive:
            super(RetryingWriteSession, self).send_request(request, result_future_id)
        self.__requests_infly.append(request)

    def process_response(self, response):
        logger.debug("Retrying session got response: {}".format(response))
        if response == _events.SESSION_CREATED_MARKER:
            self.__session_created()
            return
        elif isinstance(response, SessionFailureResult):
            if response.reason == SessionDeathReason.HostConnectionFailed:
                logger.debug("Retrying session got connection failure, will notify connection client")
                self._stream_client.notify_connect_failed(self.__session_id)
            return self.__process_session_failure(response)
        elif response.HasField('error'):
            if response.error.code == pq_err_codes.CLUSTER_DISABLED:
                logger.debug("Retrying session got cluster disabled response, will notify connection client")
                self._stream_client.notify_connect_failed(self.__session_id)
            return self.__process_session_failure(response)
        elif self._dead:
            return False
        elif not self.__alive:
            return self._process_init_response(response)

        self.__requests_infly.popleft()
        self._actor.response_ready(response)
        return response

    def _process_init_response(self, response):
        logger.debug("Retrying session processing init response")
        if not response.HasField('init'):
            raise RuntimeError("Init read session response is probably malformed: {}".format(response))
        if not self.__started:  # Handle first ever start of the session
            self._set_alive(response)
            self.__started = True
        self.__alive = True

        for request in self.__requests_infly:
            self._stream_client.send_request_to_session(self.__session_id, request)

    def __process_session_failure(self, response, do_restart=True):
        logger.debug("Retrying writer session failed with response: {}".format(response))
        if self.__session_id is not None:
            self._register_callback(self.__session_id, None)
            self._stream_client.destroy_session(self.__session_id)
            self.__session_id = None
        self.__alive = False
        if do_restart:
            self._actor.request_credentials()
            self.start()


@six.add_metaclass(abc.ABCMeta)
class AbstractActorCore(object):
    def __init__(self, actor_uid):
        self._started = False
        self._stopped = False
        self._died = False
        self.__actor_uid = actor_uid

    @property
    def _actor_uid(self):
        return self.__actor_uid


@six.add_metaclass(abc.ABCMeta)
class AbstractActorBackend(AbstractActorCore):
    """
    Abstract class for actors backend.
    Interacts with Reactor: all calls (start(), send_request() are lightweight and don't provide result,
    but schedule some operations to be done.
    Jobs are actually done with do_work() call

    """

    def __init__(
            self, actor_uid, my_reactor, stream_client, session_class, create_future_id, death_future_id,
            configurator, credentials_proto
    ):
        super(AbstractActorBackend, self).__init__(actor_uid)

        self.__create_future_id = create_future_id
        self.__death_future_id = death_future_id
        self._configurator = configurator
        self.__credentials_proto = credentials_proto

        self.__reactor = my_reactor
        self.__client = stream_client

        self._death_future_response = None

        self._session = session_class(
            stream_client, self, register_session_callback=my_reactor.register_session,
            configurator=configurator
        )

    @property
    def _credentials_proto(self):
        return self.__credentials_proto

    def update_credentials(self, credentials_proto):
        self.__credentials_proto = credentials_proto

    def request_credentials(self):
        self._report_upstream_event(_events.RenewTicketRequest, None)

    @property
    def _reactor(self):
        return self.__reactor

    @property
    def _client(self):
        return self.__client

    def _start(self):
        self._session.start()

    def _stop(self):
        self._session.die(
            reason=SessionFailureResult(SessionDeathReason.KilledByOwner),
            notify_actor=False
        )

    @abc.abstractmethod
    def send_request(self, request_type, request_args, result_future_id):
        pass

    def start(self):
        self._start()

    def stop(self):
        logger.debug("Actor id {} will now stop".format(self._actor_uid))
        if self._stopped:
            return
        self._stop()
        self._stopped = True
        if self._death_future_response is None:
            self._death_future_response = SessionFailureResult(reason=SessionDeathReason.KilledByOwner)
        self._report_upstream_event(_events.ActorStoppedEvent, self._death_future_response)

    def die(self):
        logger.debug("Actor id {} will now die".format(self._actor_uid))
        if self._died:
            return
        if not self._stopped:
            self._stop()
            self._stopped = True
        self._died = True
        if not self._started:
            assert self._death_future_response is not None
        if self._death_future_response is None:
            self._death_future_response = SessionFailureResult(SessionDeathReason.KilledByOwner)
        self._report_upstream_event(_events.ActorDeadEvent, self._death_future_response)
        self._reactor.actor_terminated(self._actor_uid)

        logger.debug("Actor id {} is now dead".format(self._actor_uid))

    def session_failed(self, session_name, reason):
        if self._death_future_response is None:
            if reason is not None:
                self._death_future_response = reason
            else:
                self._death_future_response = SessionDeathReason.ClosedUnexpectedly
        logger.debug("Session %s failed in actor %s", session_name, self._actor_uid)
        if self._started:
            logger.debug("Actor backend %s stopping", self._actor_uid)
            self.stop()
        else:
            logger.debug("Actor backend %s dying", self._actor_uid)
            self.die()

    def session_started(self, session_name, init_response):
        self._started = True
        if not self._died:  # Don't notify ActorStarted if died on startup
            self._report_upstream_event(_events.ActorStartedEvent, init_response)

    def _report_upstream_event(self, event_class, result):
        self.__reactor.report_event(self._actor_uid, event_class, result)

    def response_ready(self, result):
        self._report_upstream_event(_events.ResponseReceivedEvent, result)

    def __del__(self):
        # noinspection PyBroadException
        try:
            self.die()
        except Exception:
            pass


class WriteActorBackend(AbstractActorBackend):
    def __init__(
            self, actor_uid, my_reactor, stream_client, create_future_id, death_future_id, credentials_proto,
            configurator, session_class=WriteStreamSession
    ):
        super(WriteActorBackend, self).__init__(
            actor_uid, my_reactor, stream_client, session_class, create_future_id, death_future_id,
            configurator=configurator, credentials_proto=credentials_proto
        )

    def send_request(self, request_type, request_args, result_future_id):
        if request_type == RequestTypes.WriteRequest:
            self._session.write(result_future_id, **request_args)
        elif request_type == RequestTypes.WriteBatchRequest:
            self._session.write_batch(result_future_id, **request_args)
        else:
            raise AssertionError("Invalid request type")


class RetryingWriterBackend(WriteActorBackend):
    def __init__(
            self, actor_uid, my_reactor, stream_client, create_future_id, death_future_id, credentials_proto,
            configurator,
    ):
        super(RetryingWriterBackend, self).__init__(
            actor_uid, my_reactor, stream_client, create_future_id, death_future_id, credentials_proto, configurator,
            session_class=RetryingWriteSession
        )


class ReadActorBackend(AbstractActorBackend):
    def __init__(
            self, actor_uid, my_reactor, stream_client, create_future_id, death_future_id, credentials_proto,
            configurator
    ):
        super(ReadActorBackend, self).__init__(
            actor_uid, my_reactor, stream_client, ReadCommitStreamSession, create_future_id, death_future_id,
            configurator=configurator, credentials_proto=credentials_proto
        )
        self.__stream_client = stream_client
        self.__locks_enabled = configurator.use_client_locks
        self.__init_result = None

    def send_request(self, request_type, request_args, result_future_id):
        if request_type == RequestTypes.ReadRequest:
            return self._session.read(result_future_id, **request_args)
        elif request_type == RequestTypes.CommitRequest:
            self._session.commit(result_future_id, **request_args)
        elif request_type == RequestTypes.LockedAck:
            self._session.locked(result_future_id, **request_args)
        else:
            raise TypeError("Unknown request type: {}".format(request_type))


actor_backend_classes = {
    'Writer': WriteActorBackend, 'RetryingWriter': RetryingWriterBackend,
    'Reader': ReadActorBackend
}


class BackendReactor(threading.Thread):
    """
    Backend class processing all the async activities in separate process.
    Takes tasks as input events from one queue and puts responses into another queue.

    Output queue is used for signals (such actor's death) and for data (responses).
    """

    def __init__(self, input_event_queue, output_event_queue, stream_client_factory, start_future):
        super(BackendReactor, self).__init__()
        self.name = "PQ lib backend"
        self.daemon = True
        self.__input_queue = input_event_queue
        self.__output_queue = output_event_queue

        self.__start_future = start_future
        self.__actors = {}
        self.__registered_sessions = {}
        self.__pending_requests = {}
        self.__client = stream_client_factory(input_event_queue)
        self.__client_started = False

    def run(self):
        """
        Main loop.
        First try to get new events from input queue and process them.
        Here we can get events from Frontend (such as start/terminate actor or send request)
        and from running sessions (responses)

        :return:
        """
        self.__client.start()
        while True:
            try:
                event = self.__input_queue.get()
                if isinstance(event, _events.StopReactorEvent):
                    self.__client.stop()
                    logger.debug("Closing PQlib client")
                    break
                self.__dispatch_event(event)
                continue
            except queue.Empty:
                pass

    def __dispatch_event(self, event):
        if not self.__client_started:
            if isinstance(event, _events.ConnectionReadyEvent):
                self.__output_queue.put(_events.ReactorStartedEvent())
                self.__client_started = True  # // ! ToDo !
            else:
                raise RuntimeError(
                    "Internal state corrupted, there is definitely some bug!\nCrash-causing event was: {}".format(event)
                )
        elif isinstance(event, _events.CreateActorEvent):
            actor_id = event.actor_uid
            assert actor_id not in self.__actors
            assert event.actor_type in actor_backend_classes
            # noinspection PyCallingNonCallable
            actor = actor_backend_classes[event.actor_type](
                actor_id, self, self.__client, event.create_future_id, event.death_future_id,
                configurator=event.configurator, credentials_proto=event.credentials_proto
            )
            self.__actors[event.actor_uid] = actor
            actor.start()

        elif isinstance(event, _events.DestroyActorEvent):
            """
            Destroy is processed immediately
            """
            actor_id = event.actor_uid
            assert actor_id in self.__actors
            self.__actors[actor_id].die()

        elif isinstance(event, _events.SendRequestEvent):
            actor_id = event.actor_uid
            assert actor_id in self.__actors
            self.__actors[actor_id].send_request(event.request_type, event.request_args, event.future_id)

        elif isinstance(event, _events.ResponseReceivedEvent):
            try:
                method = self.__registered_sessions[event.session_id]
            except KeyError:
                logger.debug("Got response for unregistered session {}".format(event.response))
                return
            method(event.response)

        elif isinstance(event, _events.ConnectionReadyEvent):
            pass
        elif isinstance(event, _events.RenewTicketResponse):
            actor_id = event.actor_uid
            assert actor_id in self.__actors
            self.__actors[actor_id].update_credentials(event.credentials_proto)
        else:
            raise RuntimeError(
                "Internal error: failed to process event {} of type {}\nThis is a bug!".format(event, type(event))
            )

    def register_session(self, session_id, process_response_method):
        """
        Register session to pass its' responses from reactor input queue
        :param session_id: session_id that also must be passed to session _GRPCSingleSessionClient
        indicates which session responses should be passed to
        :param process_response_method: method to pass responses to
        :return: None
        """
        if process_response_method is None:
            del self.__registered_sessions[session_id]
        else:
            self.__registered_sessions[session_id] = process_response_method

    def report_event(self, actor_uid, event_class, result):
        self.__output_queue.put(event_class(actor_uid, result))

    def actor_terminated(self, actor_uid):
        assert actor_uid in self.__actors
        del self.__actors[actor_uid]


# noinspection PyProtectedMember
@six.add_metaclass(abc.ABCMeta)
class AbstractActorFrontend(AbstractActorCore):
    def __init__(
            self, actor_uid, pqlib, credentials_provider, make_result_method, request_method_name
    ):
        super(AbstractActorFrontend, self).__init__(actor_uid)
        self.__pqlib = pqlib
        self.__create_future = Future()
        self.__create_future.set_running_or_notify_cancel()
        self.__death_future = Future()
        self.__credentials_provider = credentials_provider

        self.__request_tracker = RequestFutureTracker(make_result_method, request_method_name)

    def start(self):
        """
        Start actor. Async
        :return: concurrent.futures.Future.
        Future result will be protobuf kikimr/yndx/api/protos/persqueue.proto::<RequestType>::Init
        Request type is ReadResponse OR WriteResponse depending on type of actor
        """
        self.__pqlib._start_actor(self._actor_uid)
        return self.__create_future

    def stop(self):
        """
        Stop and kill the actor. Async
        :return: concurrent.futures.Future.
        Future result is generally a string with death description.
        """
        if not self._stopped:
            logger.debug("Actor {} received stop signal, killing backend".format(self._actor_uid))
            self._stopped = True
            self.__pqlib._kill_backend(self._actor_uid)
        else:
            logger.debug("Actor {} ignoring stop signal, already stopped".format(self._actor_uid))
        return self.stop_future

    @abc.abstractmethod
    def _request_sent(self):
        pass

    @abc.abstractmethod
    def _request_complete(self, response):
        pass

    @property
    def _frontend(self):
        return self.__pqlib

    @property
    def start_future(self):
        return self.__create_future

    @property
    def stop_future(self):
        return self.__death_future

    @property
    def _request_tracker(self):
        return self.__request_tracker

    def _backend_started(self, result):
        assert not self._started and not self._stopped and not self._died
        self._started = True
        self.__create_future.set_result(result)

    def _backend_stopped(self, result):
        assert not self._stopped and not self._died
        self._stopped = True
        if not self._started:
            self.__create_future.set_result(result)
        self.__death_future.set_result(result)
        self.__pqlib._kill_backend(self._actor_uid)

    def _backend_dead(self, result):
        for f in (self.start_future, self.stop_future):
            if not f.done():
                f.set_result(result)
        self._die()

    def _die(self):
        if self._died:
            return
        self._died = True
        self._request_tracker.spoil_all()
        return self.__pqlib._actor_terminated(self._actor_uid)

    def _send_request(self, request_type, request_args):
        if self._died:
            raise ActorTerminatedException("Request sent to already dead actor")
        if not self._started:
            raise ActorNotReadyException("Actor was not started")
        if self._stopped:
            raise SessionClosedException("Session was already closed")
        if self.__credentials_provider is not None:
            request_args['credentials_proto'] = self.__credentials_provider.protobuf
        self.__pqlib._send_request(self._actor_uid, request_type, request_args)
        return self._request_sent()

    def _get_credentials_proto(self):
        if self.__credentials_provider is not None:
            return self.__credentials_provider.protobuf
        return None

    def __del__(self):
        # noinspection PyBroadException
        try:
            self._die()
        except Exception:
            pass
