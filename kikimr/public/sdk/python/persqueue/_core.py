#!/usr/bin/env python
# -*- coding: utf-8 -*-

import abc
import itertools
import logging
from collections import deque
import threading

import six
from six.moves import queue

from kikimr.public.sdk.python.persqueue._grpc import GRPCSingleSessionClient
from kikimr.public.sdk.python.persqueue._util import RequestFutureTracker
from kikimr.public.sdk.python.persqueue.errors import ActorNotReadyException, SessionClosedException
from kikimr.public.sdk.python.persqueue.errors import SessionFailureResult, SessionDeathReason
from kikimr.public.sdk.python.persqueue.errors import ActorTerminatedException

from kikimr.public.sdk.python.persqueue._events import CreateActorEvent, DestroyActorEvent, ActorStartedEvent
from kikimr.public.sdk.python.persqueue._events import RenewTicketRequest, RenewTicketResponse, ConnectionReadyEvent
from kikimr.public.sdk.python.persqueue._events import session_created_event, SESSION_CREATED_MARKER
from kikimr.public.sdk.python.persqueue._events import FutureRunningEvent, FutureSetResultEvent
from kikimr.public.sdk.python.persqueue._events import SendRequestEvent, ResponseReceivedEvent
from kikimr.public.sdk.python.persqueue._events import ActorStoppedEvent, ActorDeadEvent, StopReactorEvent

from kikimr.public.sdk.python.persqueue._protobuf import locked_request
from kikimr.public.sdk.python.persqueue._protobuf import WRITE_STREAM_METHOD, write_init_request, write_request
from kikimr.public.sdk.python.persqueue._protobuf import READ_STREAM_METHOD, read_init_request, read_request
from kikimr.public.sdk.python.persqueue._protobuf import RequestTypes, commit_request
from kikimr.public.sdk.python.persqueue import channel

logger = logging.getLogger(__name__)


class MultiSessionStreamClient(object):
    """
    Container class user for starting and handling several PQ Stream sessions in single KikimrClient
    (and therefore single connection)

    """

    def __init__(self, host, port, responses_queue, timeout=60):
        self.__kikimr_client_factory = lambda: channel.ChannelOpsHandler(host, port)
        self.__kikimr_client = None
        self.__client_lock = threading.RLock()
        self.__internal_lock = threading.RLock()
        self.__session_uid_counter = itertools.count()

        self.__active_sessions = {}
        self.__responses_queue = responses_queue
        self.__timeout = timeout

        self.__is_started = False
        self.__is_connected = False
        self.__session_create_queue = queue.Queue()

    def start(self):
        """
        Initial start of the client
        """
        self.__connect()

    def send_request_to_session(self, session_uid, request):
        assert session_uid in self.__active_sessions
        return self.__active_sessions[session_uid].send_request(request)

    def set_proxy_cookie_and_send_request(self, session_uid, get_full_request_method):
        request = get_full_request_method(self.__kikimr_client.proxy_cookie)
        self.send_request_to_session(session_uid, request)

    def create_new_session(self, method, session_id=None):
        if not self.__is_connected:
            logger.warn(
                "Client tried to create new session while host connection not ready. Session will not be created"
            )
            return None
        if session_id is not None:
            assert self.__active_sessions[session_id] is None
        else:
            session_id = next(self.__session_uid_counter)
        session = GRPCSingleSessionClient(
            self.__kikimr_client, self.__client_lock, method, self.__responses_queue, session_id
        )
        self.__active_sessions[session_id] = session
        return session_id

    def create_session_when_available(self, method):
        if self.__is_connected:
            return self.__create_session_delayed(method)
        else:
            session_id = next(self.__session_uid_counter)
            self.__active_sessions[session_id] = None
            self.__session_create_queue.put(({'method': method, 'session_id': session_id}))
            return session_id

    def __create_session_delayed(self, method, session_id=None):
        session_id = self.create_new_session(method, session_id)
        self.__responses_queue.put(
            session_created_event(session_uid=session_id)
        )
        return session_id

    def __process_create_queue(self):
        while not self.__session_create_queue.empty():
            item = self.__session_create_queue.get_nowait()
            self.__create_session_delayed(**item)

    def start_session(self, session_uid):
        logger.debug("Started session %s", session_uid)
        self.__active_sessions[session_uid].start()

    def destroy_session(self, session_uid):
        """
        Terminate the session.
        :param session_uid:
        :return: None
        """
        self.__active_sessions[session_uid].stop()
        del self.__active_sessions[session_uid]

    def notify_connect_failed(self):
        logger.warn("Session client disconnected, will try to reconnect")
        with self.__internal_lock:
            if not self.__is_connected:
                return
            self.__is_connected = False
            # self.__responses_queue.put(ClientConnectLostEvent())
            if self.__kikimr_client is not None:
                self.__kikimr_client.close()
        self.__connect()

    def __connect(self):
        """
        Connect the client.
        It will also send Choose Proxy request and set ProxyCookie, then initialize client on ProxyName server
        :return:
        """
        logger.info("Session client trying to [re]connect")

        def add_connected_event(f):
            self.__responses_queue.put(ConnectionReadyEvent(f))

        with self.__internal_lock:
            if self.__kikimr_client is not None:
                self.__kikimr_client.close(True)
            self.__kikimr_client = self.__kikimr_client_factory()
            f = self.__kikimr_client.async_connect()
            f.add_done_callback(add_connected_event)

    def connected(self, future):
        """
        Connection established event.
        That could be initial start or reestablished connection after failure.
        :param future:
        :return:
        """
        if future.exception() is not None:
            logger.warn("Connection failed with error: {}".format(future.exception()))
            return self.__connect()
        elif future.result() is None:
            with self.__internal_lock:
                self.__is_connected = True
            if not self.__is_started:
                self.__is_started = True
                logger.info("Session client connected")
            else:
                logger.info("Session client reconnected")
                self.__process_create_queue()

    def stop(self):
        for session in self.__active_sessions.values():
            if session is not None:
                session.stop()
        if self.__kikimr_client is not None:
            self.__kikimr_client.close()

    def __del__(self):
        self.stop()

    @staticmethod
    def factory(host, port):
        return lambda responses_queue: MultiSessionStreamClient(host, port, responses_queue)


@six.add_metaclass(abc.ABCMeta)
class AbstractStreamSession(object):
    def __init__(self, stream_client, my_actor, method, register_session_callback):
        self.__stream_client = stream_client
        self.__actor = my_actor
        self.__session_uid = None
        # self.__futures = deque()
        self._futures_tracker = RequestFutureTracker(self._actor.report_future, method)
        self.__alive = False
        self.__dead = False
        self._method = method
        self.__register_callback = register_session_callback

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
    def _session_uid(self):
        return self.__session_uid

    @abc.abstractproperty
    def _init_request_factory(self):
        pass

    def _process_init_response(self, response):
        if not response.HasField('init'):
            raise RuntimeError("Init read session response is probably malformed: {}".format(response))
        self._set_alive(response)

    def start(self):
        """
        Start session: create new GRPC stream and start it. Send session-init request.
        Init responses will be processed later in _process_init_response
        Session will be fully initialized only after getting and processing init response

        :return: init response as is

        """
        self.__session_uid = self._stream_client.create_new_session(self._method)
        if self._session_uid is None:
            self.die(
                reason=SessionFailureResult(
                    SessionDeathReason.HostConnectionFailed,
                    description="Session initialization failed! "
                                "Client had lost connection and didn't reconnect by now"
                )
            )
            return

        self.__register_callback(self._session_uid, self.process_response)
        self._stream_client.start_session(self._session_uid)
        self._stream_client.set_proxy_cookie_and_send_request(self._session_uid, self._init_request_factory)
        logger.debug("Waiting for init response")

    def send_request(self, request, result_future_id):
        """
        Send request to GRPC stream, async. Result will be reported to future with id specified.
        :param request:
        :param result_future_id:
        :return:
        """
        if result_future_id is not None:
            self._actor.report_future(result_future_id)
            self._futures_tracker.add_future(result_future_id)
        self._stream_client.send_request_to_session(self._session_uid, request)

    def process_response(self, response):
        if isinstance(response, SessionFailureResult):
            if response.reason == SessionDeathReason.HostConnectionFailed:
                self._stream_client.notify_connect_failed()
            self.die(response)
            return None
        elif self._dead:
            return False
        elif response.HasField('error'):
            self.die(
                SessionFailureResult(reason=SessionDeathReason.FailedWithError, description=response),
            )
        elif not self.__alive:
            return self._process_init_response(response)
        return self._process_data_response(response)

    def _process_data_response(self, response):
        self._futures_tracker.add_result(response)
        return response

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
        logger.debug("Session {} will now die".format(self._session_uid))
        if reason is not None:
            logger.debug("Reason: {}, description: {}".format(reason.reason, reason.description))

        self.__alive = False
        if self._session_uid is not None:
            self.__register_callback(self._session_uid, None)
            self._stream_client.destroy_session(self._session_uid)
        self._futures_tracker.spoil_all()
        self.__dead = True
        if notify_actor:
            logger.debug("Session {} is dead, will now notify actor".format(self._session_uid))
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
            stream_client, my_actor, method=WRITE_STREAM_METHOD, register_session_callback=register_session_callback
        )
        self.__write_init_factory = lambda cookie: write_init_request(
            configurator=configurator, proxy_cookie=cookie, credentials_proto=self._actor._credentials_proto
        )

    @property
    def _init_request_factory(self):
        return self.__write_init_factory

    def write(self, result_future_id, **kwargs):
        # noinspection PyArgumentList
        self.send_request(
            write_request(**kwargs),
            result_future_id
        )


class ReadCommitStreamSession(AbstractStreamSession):
    # noinspection PyProtectedMember
    def __init__(
            self, stream_client, my_actor, register_session_callback, configurator
    ):
        super(ReadCommitStreamSession, self).__init__(
            stream_client, my_actor, method=READ_STREAM_METHOD, register_session_callback=register_session_callback
        )
        self.__read_init_factory = lambda cookie: read_init_request(
            configurator, proxy_cookie=cookie, credentials_proto=self._actor._credentials_proto
        )

    @property
    def _init_request_factory(self):
        return self.__read_init_factory

    def read(self, request_args):
        return self.send_request(read_request(**request_args), None)

    def commit(self, request_args):
        return self.send_request(commit_request(**request_args), None)

    def locked(self, request_args):
        request = locked_request(**request_args)
        logger.debug("Got locked ack %s", request)
        self.send_request(request, None)

    def next_event(self, result_future_id):
        self._futures_tracker.add_future(result_future_id)

    def _process_data_response(self, response):
        self._futures_tracker.add_result(response)


class RetryingWriteSession(WriteStreamSession):
    def __init__(self, stream_client, my_actor, register_session_callback, configurator):
        super(RetryingWriteSession, self).__init__(
            stream_client, my_actor, register_session_callback, configurator
        )
        self.__requests_infly = deque()
        self.__alive = False
        self.__started = False
        self.__dead = False

        self.__session_uid = None

    @property
    def _session_uid(self):
        return self.__session_uid

    def start(self):
        logger.debug("Retrying session (re)starting")
        self.__session_uid = self._stream_client.create_session_when_available(self._method)
        self._register_callback(self.__session_uid, self.process_response)

    def __session_created(self):
        self._stream_client.start_session(self.__session_uid)
        logger.debug("Retry session started, sending init request")
        self._stream_client.set_proxy_cookie_and_send_request(self.__session_uid, self._init_request_factory)
        logger.debug("Waiting for init response")

    def send_request(self, request, result_future_id):
        """
        Send request to GRPC stream, async. Result will be reported to future with id specified.
        :param request:
        :param result_future_id:
        :return:
        """
        if self.__alive:
            logger.debug("Retrying session send request: {}".format(request))
            super(RetryingWriteSession, self).send_request(request, result_future_id)
        else:
            self._futures_tracker.add_future(result_future_id)
        self.__requests_infly.append(request)

    def process_response(self, response):
        logger.debug("Retrying session got response: {}".format(response))
        if response == SESSION_CREATED_MARKER:
            self.__session_created()
            return
        elif isinstance(response, SessionFailureResult):
            if response.reason == SessionDeathReason.HostConnectionFailed:
                self._stream_client.notify_connect_failed()
            return self.__process_session_failure()
        elif response.HasField('error'):
            return self.__process_session_failure()
        elif self._dead:
            return False
        elif not self.__alive:
            return self._process_init_response(response)

        self.__requests_infly.popleft()
        self._futures_tracker.add_result(response)
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
            self._stream_client.send_request_to_session(self.__session_uid, request)

    def __process_session_failure(self, do_restart=True):
        logger.debug("Retrying writer session failed")
        if self.__session_uid is not None:
            self._register_callback(self.__session_uid, None)
            self._stream_client.destroy_session(self.__session_uid)
            self.__session_uid = None
        self.__alive = False
        if do_restart:
            self._actor.request_credentials()
            self.start()

    def die(self, reason=None, notify_actor=True):
        if self.__dead:
            return
        logger.debug("Session {} with id {} will now die".format(self._name, self.__session_uid))
        self.__process_session_failure(do_restart=False)
        self.__dead = True
        self._futures_tracker.spoil_all()


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
        self._report_upstream_event(RenewTicketRequest)

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
        self.report_future(self.__create_future_id)
        self._start()

    def stop(self):
        logger.debug("Actor id {} will now stop".format(self._actor_uid))
        if self._stopped:
            return
        self.report_future(self.__death_future_id)
        self._stop()
        self._stopped = True
        if self._death_future_response is None:
            self._death_future_response = SessionFailureResult(reason=SessionDeathReason.KilledByOwner)
        self._report_upstream_event(ActorStoppedEvent)

    def die(self):
        logger.debug("Actor id {} will now die".format(self._actor_uid))
        if self._died:
            return
        if not self._stopped:
            self._stop()
            self._stopped = True
        self._died = True
        self._report_upstream_event(ActorDeadEvent)
        self._reactor.actor_terminated(self._actor_uid)
        if not self._started:
            assert self._death_future_response is not None
            self.report_future(self.__create_future_id, self._death_future_response)
        if self._death_future_response is None:
            self._death_future_response = SessionFailureResult(SessionDeathReason.KilledByOwner)
        self.report_future(self.__death_future_id, self._death_future_response)

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
            self._report_upstream_event(ActorStartedEvent)
        self.report_future(self.__create_future_id, init_response)

    def _report_upstream_event(self, event_class):
        self.__reactor.report_event(self._actor_uid, event_class)

    def report_future(self, future_id, result=None):
        self._reactor.report_future(future_id, result)

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
        assert request_type == RequestTypes.WriteRequest
        self._session.write(result_future_id, **request_args)


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
            return self._session.read(request_args)
        elif request_type == RequestTypes.CommitRequest:
            self._session.commit(request_args)
        elif request_type == RequestTypes.LockedAck:
            self._session.locked(request_args)
        elif request_type == RequestTypes.NextEventRequest:
            self._session.next_event(result_future_id)
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
                if isinstance(event, StopReactorEvent):
                    self.__client.stop()
                    logger.debug("Closing PQlib client")
                    break
                self.__dispatch_event(event)
                continue
            except queue.Empty:
                pass

    def __dispatch_event(self, event):
        if not self.__client_started:
            if isinstance(event, ConnectionReadyEvent):
                self.__client.connected(event.future)
                self.report_future(self.__start_future, True)
                self.__client_started = True
            else:
                raise RuntimeError(
                    "Internal state corrupted, there is definitely some bug!\nCrash-causing event was: {}".format(event)
                )
        elif isinstance(event, CreateActorEvent):
            logger.debug("Backend is processing event: {}".format(event))
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

        elif isinstance(event, DestroyActorEvent):
            """
            Destroy is processed immediately
            """
            actor_id = event.actor_uid
            assert actor_id in self.__actors
            self.__actors[actor_id].die()

        elif isinstance(event, SendRequestEvent):
            actor_id = event.actor_uid
            assert actor_id in self.__actors
            self.__actors[actor_id].send_request(event.request_type, event.request_args, event.future_id)

        elif isinstance(event, ResponseReceivedEvent):
            try:
                method = self.__registered_sessions[event.session_uid]
            except KeyError:
                logger.debug("Got response for unregistered session {}".format(event.response))
                return
            method(event.response)

        elif isinstance(event, ConnectionReadyEvent):
            self.__client.connected(event.future)
        elif isinstance(event, RenewTicketResponse):
            actor_id = event.actor_uid
            assert actor_id in self.__actors
            self.__actors[actor_id].update_credentials(event.credentials_proto)
        else:
            raise RuntimeError(
                "Internal error: failed to process event {} of type {}\nThis is a bug!".format(event, type(event))
            )

    def register_session(self, session_uid, process_response_method):
        """
        Register session to pass its' responses from reactor input queue
        :param session_uid: session_id that also must be passed to session _GRPCSingleSessionClient
        indicates which session responses should be passed to
        :param process_response_method: method to pass responses to
        :return: None
        """
        if process_response_method is None:
            del self.__registered_sessions[session_uid]
        else:
            self.__registered_sessions[session_uid] = process_response_method

    def report_event(self, actor_uid, event_class):
        self.__output_queue.put(event_class(actor_uid))

    def report_future(self, future_uid, result):
        if result is not None:
            self.__output_queue.put(FutureSetResultEvent(future_id=future_uid, result=result))
        else:
            self.__output_queue.put(FutureRunningEvent(future_id=future_uid))

    def actor_terminated(self, actor_uid):
        assert actor_uid in self.__actors
        del self.__actors[actor_uid]


# noinspection PyProtectedMember
@six.add_metaclass(abc.ABCMeta)
class AbstractActorFrontend(AbstractActorCore):
    def __init__(self, actor_uid, my_frontend, create_future, death_future, credentials_provider):
        super(AbstractActorFrontend, self).__init__(actor_uid)
        self.__frontend = my_frontend
        self.__create_future = create_future
        self.__death_future = death_future
        self.__credentials_provider = credentials_provider

    def start(self):
        """
        Start actor. Async
        :return: concurrent.futures.Future.
        Future result will be protobuf kikimr/core/protos/grpc_pq.proto::<RequestType>::Init
        Request type is ReadResponse OR WriteResponse depending on type of actor
        """
        self.__frontend._start_actor(self._actor_uid)
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
            self.__frontend._kill_backend(self._actor_uid)
        else:
            logger.debug("Actor {} ignoring stop signal, already stopped".format(self._actor_uid))
        return self.stop_future

    @property
    def _frontend(self):
        return self.__frontend

    @property
    def start_future(self):
        return self.__create_future

    @property
    def stop_future(self):
        return self.__death_future

    def _backend_started(self):
        assert not self._started and not self._stopped and not self._died
        self._started = True

    def _backend_stopped(self):
        assert not self._stopped and not self._died
        self._stopped = True
        self.__frontend._kill_backend(self._actor_uid)

    def _backend_dead(self):
        self._die()

    def _request_complete(self, request_id, result):
        pass

    def _die(self):
        self._died = True
        return self.__frontend._actor_terminated(self._actor_uid)

    def _send_request(self, request_type, request_args, is_service=False):
        if self._died:
            raise ActorTerminatedException("Request sent to already dead actor")
        if not self._started:
            raise ActorNotReadyException("Actor was not started")
        if self._stopped:
            raise SessionClosedException("Session was already closed")
        if is_service:
            return self.__frontend._send_service_request(self._actor_uid, request_type, request_args)
        if self.__credentials_provider is not None:
            request_args['credentials_proto'] = self.__credentials_provider.protobuf
        return self.__frontend._send_request(self._actor_uid, request_type, request_args)

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
