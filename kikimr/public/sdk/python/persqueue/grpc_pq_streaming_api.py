#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections
import itertools
import logging
import threading

import enum
from concurrent import futures
from six.moves import queue

from kikimr.public.sdk.python.persqueue._events import CreateActorEvent, DestroyActorEvent, StopReactorEvent
from kikimr.public.sdk.python.persqueue._events import ActorStartedEvent, ActorStoppedEvent, ActorDeadEvent
from kikimr.public.sdk.python.persqueue._events import FutureRunningEvent, FutureSetResultEvent, SendRequestEvent
from kikimr.public.sdk.python.persqueue._events import RenewTicketRequest, RenewTicketResponse

from kikimr.public.sdk.python.persqueue._core import MultiSessionStreamClient, BackendReactor, AbstractActorFrontend
from kikimr.public.sdk.python.persqueue._protobuf import RequestTypes, READ_STREAM_METHOD
from kikimr.public.sdk.python.persqueue._util import RequestFutureTracker
from kikimr.public.sdk.python.persqueue.errors import ActorNotReadyException


logger = logging.getLogger(__name__)


class _Watcher(threading.Thread):
    def __init__(self, queue, event_processor, wakeup_timeouts=3.0, *args, **kwargs):
        super(_Watcher, self).__init__()
        self.name = "PQ lib watcher"
        self.__queue = queue
        self.__target = event_processor
        self.__timeout = wakeup_timeouts
        self.__args = args
        self.__kwargs = kwargs
        self.__finished = threading.Event()

    def cancel(self):
        """Stop the watcher"""
        self.__finished.set()

    def run(self):
        while not self.__finished.is_set():
            try:
                event = self.__queue.get(block=True, timeout=self.__timeout)
                # noinspection PyArgumentList
                self.__target(event, *self.__args, **self.__kwargs)
            except queue.Empty:
                continue


class WriterCodec(enum.IntEnum):
    RAW = 0
    GZIP = 1
    LZOP = 2

    @staticmethod
    def is_codec_valid(codec):
        if codec is not None and codec not in WriterCodec:
            raise ValueError("Unsupported Codec: {}. Must use one of grpc_pq_streaming_apy.py:WriterCodec".format(codec))


class PQStreamingProducer(AbstractActorFrontend):
    """
    Streaming writer class. Call start() before usage is necessary.
    """
    def write(self, seq_no, data, create_time_ms=None, codec=None):
        """
        Write data to session.
        :param seq_no: int. your SeqNo (RecId). Required
        :param data: data to write. Required.
        :param create_time_ms: optional
        :param codec: optional
        :return: concurrent.futures.Future.
        Future result will be protobuf kikimr/public/api/protos/draft/persqueue.proto::WriteResponse
        """
        WriterCodec.is_codec_valid(codec)
        args = {
            'seq_no': seq_no, 'data': data, 'create_time_ms': create_time_ms, 'codec': codec
        }
        return self._send_request(request_type=RequestTypes.WriteRequest, request_args=args)


# noinspection PyProtectedMember
class PQStreamingConsumer(AbstractActorFrontend):
    """
        Streaming consumer class.
        Performs reads in background keeping count of non-delivered to client reads = configurator.read_infly_count
        and put results into events queue.
        If client_locks are enabled, lock responses are also received in background and put to events queue.
        Client should only call start() once and then call next_event() to fetch next available event.

    """
    def __init__(self, actor_uid, my_frontend, create_future, death_future, configurator, credentials_provider):
        super(PQStreamingConsumer, self).__init__(
            actor_uid, my_frontend, create_future, death_future, credentials_provider
        )
        self.__configurator = configurator

        self.__future_tracker = RequestFutureTracker(self.__compose_event, request_type=READ_STREAM_METHOD)
        self.__client_futures = collections.deque()
        self.__locks_enabled = configurator.use_client_locks
        self.__lock_future = None
        self.__reads_infly = 0
        self.__results_ready = 0
        self.__do_reads = True
        self.__max_infly = configurator.read_infly_count
        if not isinstance(self.__max_infly, int) or self.__max_infly < 1:
            raise ValueError("Invalid consumer infly count! Must be positive integer")

    def _backend_started(self):
        super(PQStreamingConsumer, self)._backend_started()
        self.__read()

    def __read(self):
        if self._stopped or self._died or not self.__do_reads:
            return False
        while self.__reads_infly + self.__results_ready < self.__max_infly:
            self._send_request(
                request_type=RequestTypes.ReadRequest,
                request_args={'configurator': self.__configurator},
            )
            self.__reads_infly += 1

    def _locked(self, topic, partition, generation, read_offset=0, commit_offset=0, verify_read_offset=None):
        if not self.__configurator.use_client_locks:
            raise ValueError("Attempt to send locked ack to client with locks disabled")
        return self._send_request(
            request_type=RequestTypes.LockedAck,
            request_args={
                'topic': topic, 'partition': partition, 'generation': generation,
                'read_offset': read_offset, 'commit_offset': commit_offset, 'verify_read_offset': verify_read_offset
            },
        )

    def __compose_event(self, request_id, message):
        future = self.__client_futures.popleft()
        if message.HasField('data'):
            self.__results_ready -= 1
            self.__read()
            event_type = ConsumerMessageType.MSG_DATA
        elif message.HasField('commit'):
            event_type = ConsumerMessageType.MSG_COMMIT
        elif message.HasField('lock'):
            event_type = ConsumerMessageType.MSG_LOCK
        elif message.HasField('release'):
            event_type = ConsumerMessageType.MSG_RELEASE
        else:
            assert message.HasField('error')
            event_type = ConsumerMessageType.MSG_ERROR
        future.set_result(ConsumerMessage(event_type, message, self))

    def _request_complete(self, request_id, result):
        if result.HasField('commit'):
            logger.debug("Consumer got commit response: {}".format(result))
        elif result.HasField('data'):
            self.__reads_infly -= 1
            self.__results_ready += 1
        self.__future_tracker.add_result(result)

    def next_event(self):
        """
        Get next event from consumer. May be either read data or Lock/Release signal (if client locks enabled only) or
        Read result.
        When event of Lock-type is received, client should call event.ready_to_read method to start reading
        topic/partition specified in event.message.lock
        If client_locks are enabled and client don't call ready_to_ready, server will not perform any reads.

        :return: concurrent.futures.Future which will be signalized with next available event.
        If next event was already received by the moment of call, Future will be returned with result already set
        """
        f = futures.Future()
        f.set_running_or_notify_cancel()
        request_id = self._send_request(
            RequestTypes.NextEventRequest,
            request_args=None,
            is_service=True
        )
        self.__client_futures.append(f)
        self.__future_tracker.add_future(request_id)
        return f

    def commit(self, cookies_list):
        if not isinstance(cookies_list, list) and not isinstance(cookies_list, tuple):
            cookies_list = [cookies_list, ]
        self._send_request(
            request_type=RequestTypes.CommitRequest,
            request_args={'cookies': cookies_list}
        )

    def reads_done(self):
        self.__do_reads = False

    def _die(self):
        self.__future_tracker.spoil_all()
        super(PQStreamingConsumer, self)._die()


actor_frontend_classes = {'Writer': PQStreamingProducer, 'Reader': PQStreamingConsumer}


# noinspection PyArgumentList
class ProducerConfigurator(collections.namedtuple(
    'ProducerConfigurator', ['topic', 'source_id', 'partition_group']
)):
    """
    Configurator class for PQStreaming writers. Keeps all WriteSession parameters and used for Producer initialization.
    See kikimr/core/protos/grpc_pq.proto:TWriteRequest:TInit to learn more about parameters.
    """
    def __new__(cls, topic, source_id, partition_group=None):
        """
        :param topic: PQ Topic to write, required
        :param source_id: Producer SourceId, required
        :param partition_group: specific partition groups to write into. Integers >= 1.
        Note: safe to use for NEW SourceId only. If you ever used the same SourceId to write into different
        partition group (or with out specifying part. group), it can be impossible to switch to another group.
        :return: Configurator object user for Producer init.
        """
        return super(ProducerConfigurator, cls).__new__(
            cls, topic, source_id, partition_group
        )


# noinspection PyArgumentList
class ConsumerConfigurator(collections.namedtuple(
    'ConsumerConfigurator', [
        'topics', 'client_id', 'read_only_local', 'use_client_locks',
        'balance_partition_now', 'max_count', 'max_size', 'partitions_at_once', 'max_time_lag_ms',
        'read_infly_count', 'partition_groups'
    ]
)):
    """
    Configurator class for PQStreaming readers. Keeps all ReadSession parameters and used for Consumer initialization.
    See kikimr/core/protos/grpc_pq.proto:ReadRequest to learn more about parameters.

    Note: unlike ProducerConfigurator, who's parameter are only used for session init,
    parameters from ConsumerConfigurator will be also used in further read requests (max_count, max_size, etc.)
    """
    def __new__(
            cls, topics, client_id, read_only_local=True, use_client_locks=None,
            balance_partition_now=False, max_count=None, max_size=None, partitions_at_once=None, max_time_lag_ms=None,
            read_infly_count=1, credentials_provider=None, partition_groups=None
    ):
        """

        :param topics: List of PQ Topics to read, required
        :param client_id: Consumer ClientId, required
        :param read_only_local: True=read only topics from current DC. False=read also mirrored topics.
        :param use_client_locks: used for partition locks.
        :param balance_partition_now: see docs or protobuf
        :param max_count: maximum count of messages to read at one request
        :param max_size: maximum total size of data to read at one request
        :param partitions_at_once: data from how many maximum partitions may be read at one request
        :param max_time_lag_ms: skip messages on read with time lag greater than specified
        :param read_infly_count: max unprocessed reads infly
        :param partition_groups: list of specific partition groups to read. List of integers >= 1
        :return: Configurator object user for Consumer init and in read requests.
        """
        if not isinstance(topics, list) and not isinstance(topics, tuple):
            topics = [topics, ]
        return super(ConsumerConfigurator, cls).__new__(
            cls, topics, client_id, read_only_local, use_client_locks,
            balance_partition_now, max_count, max_size, partitions_at_once, max_time_lag_ms,
            read_infly_count, partition_groups
        )


class ConsumerMessageType(enum.IntEnum):
    MSG_LOCK = 1
    MSG_RELEASE = 2
    MSG_DATA = 3
    MSG_COMMIT = 4
    MSG_ERROR = 5


class ConsumerMessage(object):
    def __init__(self, message_type, message_body, frontend):
        self.__msg_type = message_type
        self.__message = message_body
        self.__front = frontend

    @property
    def type(self):
        return self.__msg_type

    @property
    def message(self):
        return self.__message

    def ready_to_read(self, read_offset=None, commit_offset=None, verify_read_offset=None):
        if self.__msg_type != ConsumerMessageType.MSG_LOCK:
            raise TypeError("ready_to_ready may be called for Lock messages only")
        lock = self.__message.lock
        # noinspection PyProtectedMember
        self.__front._locked(
            lock.topic, lock.partition, lock.generation,
            read_offset=read_offset, commit_offset=commit_offset, verify_read_offset=verify_read_offset
        )


# noinspection PyProtectedMember
class PQStreamingAPI(object):
    """
    Main API class.
    Creates worker objects (Producer, Consumer, etc.) via corresponding methods.
    Call start() method before further usage and highly recommend to call stop() afterwards
    (better even wrap into try/finally block to ensure that stop() is always called)

    """
    def __init__(self, host, port):
        stream_client_factory = MultiSessionStreamClient.factory(host, port)
        self.__reactor_input_queue = queue.Queue()
        self.__reactor_output_queue = queue.Queue()

        self.__actors = {}
        self.__futures = {}
        self.__requests = {}
        self.__actor_uid_counter = itertools.count()
        self.__start_backend_future_id = 0
        self.__future_uid_counter = itertools.count(self.__start_backend_future_id + 1)

        self.__backend_reactor = BackendReactor(
            self.__reactor_input_queue, self.__reactor_output_queue, stream_client_factory,
            start_future=self.__start_backend_future_id
        )

        self.__watcher_lock = threading.RLock()
        self.__watcher = _Watcher(self.__reactor_output_queue, self.__process_event)
        self.__watcher.daemon = True

        self.__started = False
        self.__alive = False
        self.__stopped = False

    def start(self):
        if self.__started:
            raise RuntimeError("start() must be called exactly once!")
        self.__backend_reactor.start()
        self.__started = True
        f = futures.Future()
        self.__futures[self.__start_backend_future_id] = f
        self.__watcher.start()
        return f

    # noinspection PyTypeChecker
    def __process_event(self, event):
        if not self.__started:
            return
        if isinstance(event, FutureRunningEvent):
            with self.__watcher_lock:
                future = self.__futures.get(event.future_id, None)
            if future is not None:
                future.set_running_or_notify_cancel()
            return

        if isinstance(event, FutureSetResultEvent):
            future_id = event.future_id
            if future_id == self.__start_backend_future_id:
                self.__alive = True
            with self.__watcher_lock:
                future = self.__futures.get(future_id, None)
                if future is not None:
                    future.set_result(event.result)
                    del self.__futures[event.future_id]
                    return
                actor_id = self.__requests[future_id]
                actor = self.__actors[actor_id]
            actor._request_complete(future_id, event.result)
            return

        actor_id = event.actor_uid
        with self.__watcher_lock:
            actor = self.__actors[actor_id]
        assert actor_id is not None, "Internal state error. This is a BUG!"
        if isinstance(event, RenewTicketRequest):
            return self.__reactor_input_queue.put(
                RenewTicketResponse(actor_id, actor._get_credentials_proto())
            )
        if isinstance(event, ActorStartedEvent):
            return actor._backend_started()
        if isinstance(event, ActorStoppedEvent):
            return actor._backend_stopped()
        if isinstance(event, ActorDeadEvent):
            return actor._backend_dead()
        raise NotImplementedError("Unknown event type: {}".format(type(event)))

    def __validate_started(self):
        if not self.__started:
            self.stop()
            raise ActorNotReadyException("Must call start() before sending any commands!")
        if not self.__alive:
            self.stop()
            raise ActorNotReadyException("start() must complete before sending any commands!")

    def __create_backend(
            self, actor_type, create_future, death_future, backend_configurator, credentials_provider
    ):
        with self.__watcher_lock:
            create_future_id = next(self.__future_uid_counter)
            death_future_id = next(self.__future_uid_counter)
            self.__futures[create_future_id] = create_future
            self.__futures[death_future_id] = death_future
            actor_id = next(self.__actor_uid_counter)
        if credentials_provider is not None:
            credentials_proto = credentials_provider.protobuf
        else:
            credentials_proto = None
        self.__reactor_input_queue.put(
            CreateActorEvent(
                actor_type, actor_id, configurator=backend_configurator,
                create_future_id=create_future_id, death_future_id=death_future_id, credentials_proto=credentials_proto
            )
        )
        return actor_id

    def __create_writer_by_type(self, configurator, credentials_provider, retrying=False):
        self.__validate_started()
        if not isinstance(configurator, ProducerConfigurator):
            raise TypeError("configurator must have ProducerConfigurator type")

        create_future = futures.Future()
        death_future = futures.Future()
        if retrying:
            actor_type = 'RetryingWriter'
        else:
            actor_type = 'Writer'

        actor_id = self.__create_backend(
            actor_type=actor_type, create_future=create_future, death_future=death_future,
            backend_configurator=configurator, credentials_provider=credentials_provider
        )
        frontend = PQStreamingProducer(
            actor_id, self, create_future=create_future, death_future=death_future,
            credentials_provider=credentials_provider
        )
        with self.__watcher_lock:
            self.__actors[actor_id] = frontend
        return frontend

    def create_producer(self, producer_configurator, credentials_provider=None):
        """
        Creates PQStreamingProducer
        :param producer_configurator: ProducerConfigurator class with parameters
        :param credentials_provider: Credentials provider class for authorized writes. See auth.py
        :return: PQStreamingProducer class
        """
        return self.__create_writer_by_type(producer_configurator, credentials_provider, retrying=False)

    def create_retrying_producer(self, producer_configurator, credentials_provider=None):
        """
        Creates PQStreamingProducer with auto-retry enabled for failing requests.
        In case of any error, disconnect or other failures, writer will NOT signalize any result,
        but will try to restart session and resend all failed requests in their order.

        Only successful responses will be signalized unless you manually stop the actor.
        This writer does not care what the failure reason was, so it's user responsibility to monitor the progress
        (e.g. via responses received).

        :param producer_configurator: ProducerConfigurator class with parameters
        :param credentials_provider: Credentials provider class for authorized writes. See auth.py
        :return: PQStreamingProducer class
        """
        return self.__create_writer_by_type(producer_configurator, credentials_provider, retrying=True)

    def create_consumer(self, consumer_configurator, credentials_provider=None):
        """
        Creates PQStreamingConsumer
        :param consumer_configurator: ConsumerConfigurator class with parameters
        :param credentials_provider: Credentials provider class for authorized reads. See auth.py
        :return: PQStreamingConsumer class
        """
        self.__validate_started()
        if not isinstance(consumer_configurator, ConsumerConfigurator):
            raise TypeError("configurator must have ConsumerConfigurator type")
        create_future = futures.Future()
        death_future = futures.Future()
        actor_id = self.__create_backend(
            actor_type='Reader', create_future=create_future, death_future=death_future,
            backend_configurator=consumer_configurator, credentials_provider=credentials_provider
        )
        # noinspection PyTypeChecker
        frontend = PQStreamingConsumer(
            actor_id, self, create_future=create_future, death_future=death_future, configurator=consumer_configurator,
            credentials_provider=credentials_provider
        )
        with self.__watcher_lock:
            self.__actors[actor_id] = frontend
        return frontend

    def _start_actor(self, actor_uid):
        pass

    def _kill_backend(self, actor_uid):
        self.__reactor_input_queue.put(DestroyActorEvent(actor_uid))

    def _send_request(self, actor_uid, request_type, request_args):
        response_ready_future = futures.Future()
        with self.__watcher_lock:
            response_future_id = next(self.__future_uid_counter)
            self.__futures[response_future_id] = response_ready_future
        self.__reactor_input_queue.put(SendRequestEvent(actor_uid, request_type, request_args, response_future_id))
        return response_ready_future

    def _send_service_request(self, actor_uid, request_type, request_args):
        with self.__watcher_lock:
            request_id = next(self.__future_uid_counter)
            self.__requests[request_id] = actor_uid
        self.__reactor_input_queue.put(SendRequestEvent(actor_uid, request_type, request_args, request_id))
        return request_id

    def _actor_terminated(self, actor_uid):
        with self.__watcher_lock:
            del self.__actors[actor_uid]

    def stop(self):
        self.__started = False
        self.__watcher.cancel()
        self.__reactor_input_queue.put(StopReactorEvent())
        self.__backend_reactor.join()
        for actor in list(self.__actors.values()):
            actor._die()
        self.__stopped = True
        self.__watcher.join()

    def __del__(self):
        self.stop()
