# -*- coding: utf-8 -*-
import abc
from concurrent import futures
import functools
import logging
import hashlib
import threading
import time
import collections
import random

import enum
import six
from six.moves import queue

from kikimr.public.api.protos import ydb_table_pb2
from kikimr.public.sdk.python.client import issues
from kikimr.public.sdk.python.client import convert
from kikimr.public.sdk.python.client import operation
from kikimr.public.sdk.python.client import settings
from kikimr.public.api.grpc import ydb_table_v1_pb2_grpc as ydb_table_pb2_grpc
from kikimr.public.sdk.python.client import scheme
from kikimr.public.sdk.python.client import types
from . import interceptor

_CreateTable = 'CreateTable'
_DropTable = 'DropTable'
_AlterTable = 'AlterTable'
_CopyTable = 'CopyTable'
_DescribeTable = 'DescribeTable'
_CreateSession = 'CreateSession'
_DeleteSession = 'DeleteSession'
_ExecuteSchemeQuery = 'ExecuteSchemeQuery'
_PrepareDataQuery = 'PrepareDataQuery'
_ExecuteDataQuery = 'ExecuteDataQuery'
_BeginTransaction = 'BeginTransaction'
_CommitTransaction = 'CommitTransaction'
_RollbackTransaction = 'RollbackTransaction'
_KeepAlive = 'KeepAlive'
_StreamReadTable = 'StreamReadTable'

logger = logging.getLogger(__name__)


class DescribeTableSettings(settings.BaseRequestSettings):
    def __init__(self):
        super(DescribeTableSettings, self).__init__()
        self.include_shard_key_bounds = False

    def with_include_shard_key_bounds(self, value):
        self.include_shard_key_bounds = value
        return self


class KeyBound(object):
    __slots__ = ('_equal', 'value', 'type')

    def __init__(self, value, inclusive=False, type=None):
        self._equal = inclusive
        self.value = value
        self.type = type

    def is_inclusive(self):
        return self._equal

    def __str__(self):
        if self._equal:
            return 'InclusiveKeyBound(Tuple%s)' % str(self.value)
        return 'ExclusiveKeyBound(Tuple%s)' % str(self.value)

    @classmethod
    def inclusive(cls, value, key_type):
        return cls(value, True, key_type)

    @classmethod
    def exclusive(cls, value, key_type):
        return cls(value, False, key_type)


class KeyRange(object):
    __slots__ = ('from_bound', 'to_bound')

    def __init__(self, from_bound, to_bound):
        self.from_bound = from_bound
        self.to_bound = to_bound

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return 'KeyRange(%s, %s)' % (
            str(self.from_bound), str(self.to_bound))


class Column(object):
    def __init__(self, name, type):
        self._name = name
        self._type = type

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._type

    @property
    def type_pb(self):
        try:
            return self._type.proto
        except Exception:
            return self._type


def _bad_session_handler(func):
    @functools.wraps(func)
    def decorator(response_pb, session_state, *args, **kwargs):
        try:
            return func(response_pb, session_state, *args, **kwargs)
        except (issues.BadSession, issues.SessionExpired):
            session_state.reset()
            raise
    return decorator


@enum.unique
class FeatureFlag(enum.IntEnum):
    ENABLED = 1
    DISABLED = 2


@enum.unique
class AutoPartitioningPolicy(enum.IntEnum):
    AUTO_PARTITIONING_POLICY_UNSPECIFIED = 0
    DISABLED = 1
    AUTO_SPLIT = 2
    AUTO_SPLIT_MERGE = 3


class CachingPolicy(object):
    def __init__(self):
        self._pb = ydb_table_pb2.CachingPolicy()
        self.preset_name = None

    def with_preset_name(self, preset_name):
        self._pb.preset_name = preset_name
        self.preset_name = preset_name
        return self

    def to_pb(self):
        return self._pb


class ExecutionPolicy(object):
    def __init__(self):
        self._pb = ydb_table_pb2.ExecutionPolicy()
        self.preset_name = None

    def with_preset_name(self, preset_name):
        self._pb.preset_name = preset_name
        self.preset_name = preset_name
        return self

    def to_pb(self):
        return self._pb


class CompactionPolicy(object):
    def __init__(self):
        self._pb = ydb_table_pb2.CompactionPolicy()
        self.preset_name = None

    def with_preset_name(self, preset_name):
        self._pb.preset_name = preset_name
        self.preset_name = preset_name
        return self

    def to_pb(self):
        return self._pb


class ExplicitPartitions(object):
    def __init__(self, split_points):
        self.split_points = split_points


class PartitioningPolicy(object):
    def __init__(self):
        self._pb = ydb_table_pb2.PartitioningPolicy()
        self.preset_name = None
        self.uniform_partitions = None
        self.auto_partitioning = None
        self.explicit_partitions = None

    def with_preset_name(self, preset_name):
        self._pb.preset_name = preset_name
        self.preset_name = preset_name
        return self

    def with_uniform_partitions(self, uniform_partitions):
        self._pb.uniform_partitions = uniform_partitions
        self.uniform_partitions = uniform_partitions
        return self

    def with_explicit_partitions(self, explicit_partitions):
        self.explicit_partitions = explicit_partitions
        return self

    def with_auto_partitioning(self, auto_partitioning):
        self._pb.auto_partitioning = auto_partitioning
        self.auto_partitioning = auto_partitioning
        return self

    def to_pb(self, table_description):
        if self.explicit_partitions is not None:
            split_point_type = types.TupleType()
            for column in table_description.columns:
                if column.name not in table_description.primary_key:
                    continue

                split_point_type.add_element(
                    column.type)
            for split_point in self.explicit_partitions.split_points:
                typed_value = self._pb.explicit_partitions.split_points.add()
                typed_value.type.MergeFrom(split_point_type.proto)
                typed_value.value.MergeFrom(
                    convert.from_native_value(
                        split_point_type.proto,
                        split_point.value
                    )
                )

        return self._pb


class ReplicationPolicy(object):
    def __init__(self):
        self._pb = ydb_table_pb2.ReplicationPolicy()
        self.preset_name = None
        self.replicas_count = None
        self.allow_promotion = None
        self.create_per_availability_zone = None

    def with_preset_name(self, preset_name):
        self._pb.preset_name = preset_name
        self.preset_name = preset_name
        return self

    def with_replicas_count(self, replicas_count):
        self._pb.replicas_count = replicas_count
        self.replicas_count = replicas_count
        return self

    def with_create_per_availability_zone(self, create_per_availability_zone):
        self._pb.create_per_availability_zone = create_per_availability_zone
        self.create_per_availability_zone = create_per_availability_zone
        return self

    def with_allow_promotion(self, allow_promotion):
        self._pb.allow_promotion = allow_promotion
        self.allow_promotion = allow_promotion
        return self

    def to_pb(self):
        return self._pb


class StorageSettings(object):
    def __init__(self, storage_kind):
        self.storage_kind = storage_kind

    def to_pb(self):
        return ydb_table_pb2.StorageSettings(storage_kind=self.storage_kind)


class StoragePolicy(object):
    def __init__(self):
        self._pb = ydb_table_pb2.StoragePolicy()
        self.preset_name = None
        self.syslog = None
        self.log = None
        self.data = None
        self.keep_in_memory = None
        self.external = None

    def with_preset_name(self, preset_name):
        self._pb.preset_name = preset_name
        self.preset_name = preset_name
        return self

    def with_syslog_storage_settings(self, syslog_settings):
        self._pb.syslog.MergeFrom(syslog_settings.to_pb())
        self.syslog = syslog_settings
        return self

    def with_log_storage_settings(self, log_settings):
        self._pb.log.MergeFrom(log_settings.to_pb())
        self.log = log_settings
        return self

    def with_data_storage_settings(self, data_settings):
        self._pb.data.MergeFrom(data_settings.to_pb())
        self.data = data_settings
        return self

    def with_external_storage_settings(self, external_settings):
        self._pb.external.MergeFrom(external_settings.to_pb())
        self.external = external_settings
        return self

    def with_keep_in_memory(self, keep_in_memory):
        self._pb.keep_in_memory = keep_in_memory
        self.keep_in_memory = keep_in_memory
        return self

    def to_pb(self):
        return self._pb


class TableProfile(object):
    def __init__(self):
        self.preset_name = None
        self.compaction_policy = None
        self.partitioning_policy = None
        self.storage_policy = None
        self.execution_policy = None
        self.replication_policy = None
        self.caching_policy = None

    def with_preset_name(self, preset_name):
        self.preset_name = preset_name
        return self

    def with_compaction_policy(self, compaction_policy):
        self.compaction_policy = compaction_policy
        return self

    def with_partitioning_policy(self, partitioning_policy):
        self.partitioning_policy = partitioning_policy
        return self

    def with_execution_policy(self, execution_policy):
        self.execution_policy = execution_policy
        return self

    def with_caching_policy(self, caching_policy):
        self.caching_policy = caching_policy
        return self

    def with_storage_policy(self, storage_policy):
        self.storage_policy = storage_policy
        return self

    def with_replication_policy(self, replication_policy):
        self.replication_policy = replication_policy
        return self

    def to_pb(self, table_description):
        pb = ydb_table_pb2.TableProfile()

        if self.preset_name is not None:
            pb.preset_name = self.preset_name

        if self.execution_policy is not None:
            pb.execution_policy.MergeFrom(
                self.execution_policy.to_pb())

        if self.storage_policy is not None:
            pb.storage_policy.MergeFrom(
                self.storage_policy.to_pb())

        if self.replication_policy is not None:
            pb.replication_policy.MergeFrom(
                self.replication_policy.to_pb())

        if self.caching_policy is not None:
            pb.caching_policy.MergeFrom(
                self.caching_policy.to_pb())

        if self.compaction_policy is not None:
            pb.compaction_policy.MergeFrom(
                self.compaction_policy.to_pb())

        if self.partitioning_policy is not None:
            pb.partitioning_policy.MergeFrom(
                self.partitioning_policy.to_pb(table_description))

        return pb


class TableDescription(object):
    def __init__(self):
        self.columns = []
        self.primary_key = []
        self.profile = None

    def with_column(self, column):
        self.columns.append(column)
        return self

    def with_columns(self, *columns):
        for column in columns:
            self.with_column(column)
        return self

    def with_primary_key(self, key):
        self.primary_key.append(key)
        return self

    def with_primary_keys(self, *keys):
        for pk in keys:
            self.with_primary_key(pk)
        return self

    def with_profile(self, profile):
        self.profile = profile
        return self


def _create_table_request_factory(path, table_description):
    request = ydb_table_pb2.CreateTableRequest()
    request.path = path
    request.primary_key.extend(list(table_description.primary_key))
    for column in table_description.columns:
        request.columns.add(name=column.name, type=column.type_pb)
    if table_description.profile is not None:
        request.profile.MergeFrom(table_description.profile.to_pb(table_description))
    return request


@six.add_metaclass(abc.ABCMeta)
class AbstractTransactionModeBuilder(object):

    @abc.abstractproperty
    def name(self):
        pass

    @abc.abstractproperty
    def settings(self):
        pass


class SerializableReadWrite(AbstractTransactionModeBuilder):
    __slots__ = ('_pb', '_name')

    def __init__(self):
        self._name = 'serializable_read_write'
        self._pb = ydb_table_pb2.SerializableModeSettings()

    @property
    def settings(self):
        return self._pb

    @property
    def name(self):
        return self._name


class OnlineReadOnly(AbstractTransactionModeBuilder):
    __slots__ = ('_pb', '_name')

    def __init__(self):
        self._pb = ydb_table_pb2.OnlineModeSettings()
        self._pb.allow_inconsistent_reads = False
        self._name = 'online_read_only'

    def with_allow_inconsistent_reads(self):
        self._pb.allow_inconsistent_reads = True
        return self

    @property
    def settings(self):
        return self._pb

    @property
    def name(self):
        return self._name


class StaleReadOnly(AbstractTransactionModeBuilder):
    __slots__ = ('_pb', '_name')

    def __init__(self):
        self._pb = ydb_table_pb2.StaleModeSettings()
        self._name = 'stale_read_only'

    @property
    def settings(self):
        return self._pb

    @property
    def name(self):
        return self._name


def default_unknown_error_handler(e):
    raise e


class RetrySettings(object):
    def __init__(
            self, max_retries=10,
            max_session_acquire_timeout=3,
            on_ydb_error_callback=None, backoff_ceiling=6, backoff_slot_duration=1):
        self.max_retries = max_retries
        self.max_session_acquire_timeout = max_session_acquire_timeout
        self.on_ydb_error_callback = lambda e: None if on_ydb_error_callback is None else on_ydb_error_callback
        self.backoff_ceiling = backoff_ceiling
        self.backoff_slot_duration = backoff_slot_duration
        self.retry_not_found = True
        self.retry_internal_error = True
        self.unknown_error_handler = default_unknown_error_handler


def calc_backoff_timeout(settings, retry_number):
    slots_count = 1 << min(retry_number, settings.backoff_ceiling)
    max_duration = slots_count * settings.backoff_slot_duration
    return random.random() * max_duration


def retry_operation_sync(callee, retry_settings=None, *args, **kwargs):

    retry_settings = RetrySettings() if retry_settings is None else retry_settings
    status = None

    for attempt in six.moves.range(retry_settings.max_retries + 1):
        try:
            return callee(*args, **kwargs)
        except (
                issues.Unavailable, issues.Aborted, issues.BadSession,
                issues.NotFound, issues.InternalError) as e:
            status = e
            retry_settings.on_ydb_error_callback(e)

            if isinstance(e, issues.NotFound) and not retry_settings.retry_not_found:
                raise e

            if isinstance(e, issues.InternalError) and not retry_settings.retry_internal_error:
                raise e

        except (issues.Overloaded, SessionPoolEmpty, issues.ConnectionError) as e:
            status = e
            retry_settings.on_ydb_error_callback(e)
            time.sleep(
                calc_backoff_timeout(
                    retry_settings,
                    attempt
                )
            )

        except issues.Error as e:
            retry_settings.on_ydb_error_callback(e)
            raise

        except Exception as e:
            # you should provide your own handler you want
            retry_settings.unknown_error_handler(e)

    raise status


class TableClient(object):
    def __init__(self, driver):
        self._driver = driver

    def session(self):
        return Session(self._driver)


class DataQuery(object):
    __slots__ = ('yql_text', 'parameters_types', 'name')

    def __init__(self, query_id, parameters_types, name=None):
        self.yql_text = query_id
        self.parameters_types = parameters_types
        self.name = _get_query_hash(self.yql_text) if name is None else name


@_bad_session_handler
def _wrap_prepare_query_response(response_pb, session_state, yql_text):
    issues._process_response(response_pb)
    message = ydb_table_pb2.PrepareQueryResult()
    response_pb.result.Unpack(message)
    data_query = DataQuery(yql_text, message.parameters_types)
    session_state.keep(data_query, message.query_id)
    return data_query


def _get_query_hash(yql_text):
    try:
        return hashlib.sha256(six.text_type(yql_text, 'utf-8').encode('utf-8')).hexdigest()
    except TypeError:
        return hashlib.sha256(six.text_type(yql_text).encode('utf-8')).hexdigest()


class _LRU(object):
    def __init__(self, capacity=1000):
        self.items = collections.OrderedDict()
        self.capacity = capacity

    def put(self, key, value):
        self.items[key] = value
        while len(self.items) > self.capacity:
            self.items.popitem(last=False)

    def get(self, key, _default):
        if key not in self.items:
            return _default
        value = self.items.pop(key)
        self.items[key] = value
        return value

    def erase(self, key):
        self.items.pop(key)


class _SessionState(object):
    def __init__(self):
        self._session_id = None
        self._query_cache = _LRU(1000)
        self._default = (None, None)

    def __contains__(self, query):
        return self.lookup(query) != self._default

    def reset(self):
        self._query_cache = _LRU(1000)
        self._session_id = None

    @property
    def session_id(self):
        return self._session_id

    def set_id(self, session_id):
        self._session_id = session_id
        return self

    def keep(self, query, query_id):
        self._query_cache.put(query.name, (query, query_id))
        return self

    @staticmethod
    def _query_key(query):
        return query.name if isinstance(query, DataQuery) else _get_query_hash(query)

    def lookup(self, query):
        return self._query_cache.get(self._query_key(query), self._default)

    def erase(self, query):
        query, query_id = self.lookup(query)
        self._query_cache.erase(query.name)

    def attach_request(self, request):
        if self._session_id is None:
            raise issues.BadSession("Empty session_id")
        request.session_id = self._session_id
        return request


@_bad_session_handler
def _wrap_execute_scheme_result(response_pb, session_state):
    issues._process_response(response_pb)
    message = ydb_table_pb2.ExecuteQueryResult()
    response_pb.result.Unpack(message)
    return convert.ResultSets(message.result_sets)


class TableSchemeEntry(scheme.SchemeEntry):
    def __init__(
            self, name, owner, type, effective_permissions, permissions, columns, primary_key, shard_key_bounds,
            *args, **kwargs):

        super(TableSchemeEntry, self).__init__(name, owner, type, effective_permissions, permissions, *args, **kwargs)
        self.primary_key = [pk for pk in primary_key]
        self.columns = [
            Column(column.name, convert.type_to_native(column.type))
            for column in columns
        ]
        self.shard_key_ranges = []
        left_key_bound = None
        for shard_key_bound in shard_key_bounds:
            # for next key range
            key_bound_type = shard_key_bound.type
            current_bound = convert.to_native_value(shard_key_bound)
            self.shard_key_ranges.append(
                KeyRange(
                    None if left_key_bound is None else KeyBound.inclusive(left_key_bound, key_bound_type),
                    KeyBound.exclusive(current_bound, key_bound_type)
                )
            )
            left_key_bound = current_bound

            assert isinstance(left_key_bound, tuple)

        if len(shard_key_bounds) > 0:
            self.shard_key_ranges.append(
                KeyRange(
                    KeyBound.inclusive(left_key_bound, shard_key_bounds[-1].type),
                    None,
                )
            )

        else:
            self.shard_key_ranges.append(
                KeyRange(None, None))


@_bad_session_handler
def _wrap_describe_table_response(response_pb, sesssion_state):
    issues._process_response(response_pb)
    message = ydb_table_pb2.DescribeTableResult()
    response_pb.result.Unpack(message)
    return scheme._wrap_scheme_entry(
        message.self,
        TableSchemeEntry,
        message.columns,
        message.primary_key,
        message.shard_key_bounds,
    )


@_bad_session_handler
def _cleanup_session(response_pb, session_state, session):
    issues._process_response(response_pb)
    session_state.reset()
    return session


@_bad_session_handler
def _initialize_session(response_pb, session_state, session):
    issues._process_response(response_pb)
    message = ydb_table_pb2.CreateSessionResult()
    response_pb.result.Unpack(message)
    session_state.set_id(message.session_id)
    return session


@_bad_session_handler
def _wrap_operation(response_pb, session_state):
    return operation.Operation(response_pb)


@_bad_session_handler
def _wrap_keep_alive_response(response_pb, session_state, session):
    issues._process_response(response_pb)
    return session


def _keep_alive_request_factory(session_state):
    request = ydb_table_pb2.KeepAliveRequest()
    return session_state.attach_request(request)


def _read_table_request_factory(session_state, path, key_range=None, columns=None, ordered=False, row_limit=None):
    request = ydb_table_pb2.ReadTableRequest()
    request.path = path
    request.ordered = ordered
    if key_range is not None and key_range.from_bound is not None:
        target_attribute = 'greater_or_equal' if key_range.from_bound.is_inclusive() else 'greater'
        getattr(request.key_range, target_attribute).MergeFrom(
            convert.to_typed_value_from_native(
                key_range.from_bound.type,
                key_range.from_bound.value
            )
        )

    if key_range is not None and key_range.to_bound is not None:
        target_attribute = 'less_or_equal' if key_range.to_bound.is_inclusive() else 'less'
        getattr(request.key_range, target_attribute).MergeFrom(
            convert.to_typed_value_from_native(
                key_range.to_bound.type,
                key_range.to_bound.value
            )
        )

    if columns is not None:
        for column in columns:
            request.columns.append(column)
    if row_limit:
        request.row_limit = row_limit
    return session_state.attach_request(request)


class WrappedSyncResponseIterator(object):
    def __init__(self, it, wrapper):
        self.it = it
        self.wrapper = wrapper

    def cancel(self):
        self.it.cancel()
        return self

    def __iter__(self):
        return self

    def next(self):
        return self.wrapper(next(self.it))

    def __next__(self):
        return self.wrapper(next(self.it))


def _wrap_read_table_response(response):
    issues._process_response(response)
    return convert.ResultSet.from_message(response.result.result_set)


class Session(object):
    __slots__ = ('_state', '_driver', '__weakref__')

    def __init__(self, driver):
        self._driver = driver
        self._state = _SessionState()

    def __lt__(self, other):
        return self.session_id < other.session_id

    def __eq__(self, other):
        return self.session_id == other.session_id

    @property
    def session_id(self):
        return self._state.session_id

    def initialized(self):
        return self._state.session_id is not None

    def reset(self):
        return self._state.reset()

    def read_table(self, path, key_range=None, columns=(), ordered=False, row_limit=None):
        """
        Experimental api to read the table
        :param path:
        :param key_range:
        :param columns:
        :param ordered:
        :param row_limit:
        :return: WrappedSyncResponseIterator instance
        """
        request = _read_table_request_factory(self._state, path, key_range, columns, ordered, row_limit)
        stream_it = self._driver(request, ydb_table_pb2_grpc.TableServiceStub, _StreamReadTable)
        return WrappedSyncResponseIterator(stream_it, _wrap_read_table_response)

    def async_read_table(self, path, key_range=None, columns=None, ordered=False, row_limit=None):
        """
        Experimental api to read the table
        :param path:
        :param key_range:
        :param columns:
        :param ordered:
        :param row_limit:
        :return: async iterator instance
        """
        request = _read_table_request_factory(self._state, path, key_range, columns, ordered, row_limit)
        stream_it = self._driver(request, ydb_table_pb2_grpc.TableServiceStub, _StreamReadTable)
        return interceptor.patch_async_iterator(stream_it, _wrap_read_table_response)

    def keep_alive(self, settings=None):
        return self._driver(
            _keep_alive_request_factory(self._state),
            ydb_table_pb2_grpc.TableServiceStub,
            _KeepAlive,
            _wrap_keep_alive_response,
            settings,
            (
                self._state,
                self
            )
        )

    def async_keep_alive(self, settings=None):
        return self._driver(
            _keep_alive_request_factory(self._state),
            ydb_table_pb2_grpc.TableServiceStub,
            _KeepAlive,
            _wrap_keep_alive_response,
            settings,
            (
                self._state,
                self
            )
        )

    def async_create(self, settings=None):
        if self._state.session_id is not None:
            return _wrap_in_future(self)
        return self._driver.future(
            ydb_table_pb2.CreateSessionRequest(),
            ydb_table_pb2_grpc.TableServiceStub,
            _CreateSession,
            _initialize_session,
            settings,
            (
                self._state,
                self
            )
        )

    def create(self, settings=None):
        if self._state.session_id is not None:
            return self
        return self._driver(
            ydb_table_pb2.CreateSessionRequest(),
            ydb_table_pb2_grpc.TableServiceStub,
            _CreateSession,
            _initialize_session,
            settings,
            (
                self._state,
                self
            )
        )

    def async_delete(self, settings=None):
        return self._driver.future(
            self._state.attach_request(ydb_table_pb2.DeleteSessionRequest()),
            ydb_table_pb2_grpc.TableServiceStub,
            _DeleteSession,
            _cleanup_session,
            settings,
            (
                self._state,
                self
            )
        )

    def delete(self, settings=None):
        return self._driver(
            self._state.attach_request(ydb_table_pb2.DeleteSessionRequest()),
            ydb_table_pb2_grpc.TableServiceStub,
            _DeleteSession,
            _cleanup_session,
            settings,
            (
                self._state,
                self
            )
        )

    def _execute_scheme_request_factory(self, yql_text):
        request = self._state.attach_request(ydb_table_pb2.ExecuteSchemeQueryRequest())
        request.yql_text = yql_text
        return request

    def async_execute_scheme(self, yql_text, settings=None):
        return self._driver.future(
            self._execute_scheme_request_factory(yql_text),
            ydb_table_pb2_grpc.TableServiceStub,
            _ExecuteSchemeQuery,
            _wrap_execute_scheme_result,
            settings,
            (
                self._state,
            )
        )

    def execute_scheme(self, yql_text, settings=None):
        return self._driver(
            self._execute_scheme_request_factory(yql_text),
            ydb_table_pb2_grpc.TableServiceStub,
            _ExecuteSchemeQuery,
            _wrap_execute_scheme_result,
            settings,
            (
                self._state,
            )
        )

    def transaction(self, tx_mode=None):
        return TxContext(self._driver, self._state, self, tx_mode)

    def _prepare_request_factory(self, yql_text):
        request = self._state.attach_request(ydb_table_pb2.PrepareDataQueryRequest())
        request.yql_text = yql_text
        return request

    def has_prepared(self, query):
        return query in self._state

    def async_prepare(self, query, settings=None):
        data_query, _ = self._state.lookup(query)
        if data_query is not None:
            return _wrap_in_future(data_query)
        return self._driver.future(
            self._prepare_request_factory(query),
            ydb_table_pb2_grpc.TableServiceStub,
            _PrepareDataQuery,
            _wrap_prepare_query_response,
            settings,
            (
                self._state,
                query,
            )
        )

    def prepare(self, query, settings=None):
        data_query, _ = self._state.lookup(query)
        if data_query is not None:
            return data_query
        return self._driver(
            self._prepare_request_factory(query),
            ydb_table_pb2_grpc.TableServiceStub,
            _PrepareDataQuery,
            _wrap_prepare_query_response,
            settings,
            (
                self._state,
                query,
            )
        )

    def async_create_table(self, path, table_description, settings=None):
        return self._driver.future(
            self._state.attach_request(_create_table_request_factory(path, table_description)),
            ydb_table_pb2_grpc.TableServiceStub,
            _CreateTable,
            _wrap_operation,
            settings,
            (
                self._driver,
            )
        )

    def create_table(self, path, table_description, settings=None):
        return self._driver(
            self._state.attach_request(_create_table_request_factory(path, table_description)),
            ydb_table_pb2_grpc.TableServiceStub,
            _CreateTable,
            _wrap_operation,
            settings,
            (
                self._driver,
            )
        )

    def async_drop_table(self, path, settings=None):
        return self._driver.future(
            self._state.attach_request(ydb_table_pb2.DropTableRequest(path=path)),
            ydb_table_pb2_grpc.TableServiceStub,
            _DropTable,
            _wrap_operation,
            settings,
            (
                self._state,
            )
        )

    def drop_table(self, path, settings=None):
        return self._driver(
            self._state.attach_request(ydb_table_pb2.DropTableRequest(path=path)),
            ydb_table_pb2_grpc.TableServiceStub,
            _DropTable,
            _wrap_operation,
            settings,
            (
                self._state,
            )
        )

    def _async_alter_table(self, path, add_columns, drop_columns):
        request = self._state.attach_request(ydb_table_pb2.AlterTableRequest(path=path))
        for column in add_columns:
            request.add_columns.add(name=column.name, type=column.type_pb)
        request.drop_columns.extend(list(drop_columns))
        return request

    def async_alter_table(self, path, add_columns, drop_columns, settings=None):
        return self._driver.future(
            self._async_alter_table(path, add_columns, drop_columns),
            ydb_table_pb2_grpc.TableServiceStub,
            _AlterTable,
            _wrap_operation,
            settings,
            (
                self._state,
            )
        )

    def alter_table(self, path, add_columns, drop_columns, settings=None):
        return self._driver(
            self._async_alter_table(path, add_columns, drop_columns),
            ydb_table_pb2_grpc.TableServiceStub,
            _AlterTable,
            _wrap_operation,
            settings,
            (
                self._state,
            )
        )

    def _copy_table_request_factory(self, source_path, destination_path):
        request = self._state.attach_request(ydb_table_pb2.CopyTableRequest())
        request.source_path = source_path
        request.destination_path = destination_path
        return request

    def async_copy_table(self, source_path, destination_path, settings=None):
        return self._driver.future(
            self._copy_table_request_factory(source_path, destination_path),
            ydb_table_pb2_grpc.TableServiceStub,
            _CopyTable,
            _wrap_operation,
            settings,
            (
                self._state,
            )
        )

    def copy_table(self, source_path, destination_path, settings=None):
        return self._driver(
            self._copy_table_request_factory(source_path, destination_path),
            ydb_table_pb2_grpc.TableServiceStub,
            _CopyTable,
            _wrap_operation,
            settings,
            (
                self._state,
            )
        )

    def _describe_table_request_factory(self, path, settings=None):
        request = self._state.attach_request(ydb_table_pb2.DescribeTableRequest())
        request.path = path

        if settings is not None and hasattr(settings, 'include_shard_key_bounds') and settings.include_shard_key_bounds:
            request.include_shard_key_bounds = settings.include_shard_key_bounds

        return request

    def async_describe_table(self, path, settings=None):
        return self._driver.future(
            self._describe_table_request_factory(path),
            ydb_table_pb2_grpc.TableServiceStub,
            _DescribeTable,
            _wrap_describe_table_response,
            settings,
            (
                self._state,
            )
        )

    def describe_table(self, path, settings=None):
        """
        Returns a description of the table by provided path
        :param path: A table path
        :param settings: A request settings
        :return: Description of a table
        """
        return self._driver(
            self._describe_table_request_factory(path, settings),
            ydb_table_pb2_grpc.TableServiceStub,
            _DescribeTable,
            _wrap_describe_table_response,
            settings,
            (
                self._state,
            )
        )


_DefaultTxMode = SerializableReadWrite()


class _TxState(object):
    __slots__ = ('tx_id', 'tx_mode', 'dead', 'initialized')

    def __init__(self, tx_mode=None):
        """
        Holds transaction context manager info
        :param tx_mode: A mode of transaction
        """
        self.tx_id = None
        self.tx_mode = _DefaultTxMode if tx_mode is None else tx_mode
        self.dead = False
        self.initialized = False


def _construct_tx_settings(tx_state):
    tx_settings = ydb_table_pb2.TransactionSettings()
    mode_property = getattr(tx_settings, tx_state.tx_mode.name)
    mode_property.MergeFrom(tx_state.tx_mode.settings)
    return tx_settings


def _wrap_tx_factory_handler(func):
    @functools.wraps(func)
    def decorator(session_state, tx_state, *args, **kwargs):
        if tx_state.dead:
            raise issues.PreconditionFailed('Failed to perform action on broken transaction context!')
        return func(session_state, tx_state, *args, **kwargs)
    return decorator


@_wrap_tx_factory_handler
def _execute_request_factory(session_state, tx_state, query, parameters, commit_tx):
    data_query, query_id = session_state.lookup(query)
    parameters_types = {}
    if query_id is not None:
        query_pb = ydb_table_pb2.Query(id=query_id)
        parameters_types = data_query.parameters_types
    else:
        if isinstance(query, DataQuery):
            yql_text = query.yql_text
            parameters_types = query.parameters_types
        else:
            yql_text = query
        query_pb = ydb_table_pb2.Query(yql_text=yql_text)
    request = ydb_table_pb2.ExecuteDataQueryRequest(
        parameters=convert.parameters_to_pb(parameters_types, parameters))
    request.query.MergeFrom(query_pb)
    tx_control = ydb_table_pb2.TransactionControl()
    tx_control.commit_tx = commit_tx
    if tx_state.tx_id is not None:
        tx_control.tx_id = tx_state.tx_id
    else:
        tx_control.begin_tx.MergeFrom(_construct_tx_settings(tx_state))
    request.tx_control.MergeFrom(tx_control)
    request = session_state.attach_request(request)
    return request


def _reset_tx_id_handler(func):
    @functools.wraps(func)
    def decorator(response_pb, session_state, tx_state, *args, **kwargs):
        try:
            return func(response_pb, session_state, tx_state, *args, **kwargs)
        except issues.ConnectionError:
            raise
        except issues.Error:
            tx_state.tx_id = None
            tx_state.dead = True
            raise
    return decorator


def _not_found_handler(func):
    @functools.wraps(func)
    def decorator(response_pb, session_state, tx_state, query, *args, **kwargs):
        try:
            return func(response_pb, session_state, tx_state, query, *args, **kwargs)
        except issues.NotFound:
            session_state.erase(query)
            raise
    return decorator


@_bad_session_handler
@_reset_tx_id_handler
@_not_found_handler
def _wrap_result_and_tx_id(response_pb, session_state, tx_state, query):
    issues._process_response(response_pb)
    message = ydb_table_pb2.ExecuteQueryResult()
    response_pb.result.Unpack(message)
    tx_state.tx_id = None if not message.tx_meta.id else message.tx_meta.id
    return convert.ResultSets(message.result_sets)


@_bad_session_handler
@_reset_tx_id_handler
def _wrap_result_on_rollback_or_commit_tx(response_pb, session_state, tx_state, tx):
    issues._process_response(response_pb)
    # transaction successfully committed or rolled back
    tx_state.tx_id = None
    return tx


@_bad_session_handler
def _wrap_tx_begin_response(response_pb, session_state, tx_state, tx):
    issues._process_response(response_pb)
    message = ydb_table_pb2.BeginTransactionResult()
    response_pb.result.Unpack(message)
    tx_state.tx_id = message.tx_meta.id
    return tx


def _wrap_in_future(result):
    f = futures.Future()
    f.set_result(result)
    return f


@_wrap_tx_factory_handler
def _rollback_request_factory(session_state, tx_state):
    request = ydb_table_pb2.RollbackTransactionRequest()
    request.tx_id = tx_state.tx_id
    request = session_state.attach_request(request)
    return request


@_wrap_tx_factory_handler
def _begin_request_factory(session_state, tx_state):
    request = ydb_table_pb2.BeginTransactionRequest()
    request = session_state.attach_request(request)
    request.tx_settings.MergeFrom(_construct_tx_settings(tx_state))
    return request


@_wrap_tx_factory_handler
def _commit_request_factory(session_state, tx_state):
    """
    Constructs commit request
    """
    request = ydb_table_pb2.CommitTransactionRequest()
    request.tx_id = tx_state.tx_id
    request = session_state.attach_request(request)
    return request


class TxContext(object):
    __slots__ = ('_tx_state', '_session_state', '_driver', 'session')

    def __init__(self, driver, session_state, session, tx_mode=None):
        """
        An object that provides a simple transaction context manager that allows statements execution
        in a transaction. You don't have to open transaction explicitly, because context manager encapsulates
        transaction control logic, and opens new transaction if:
         1) By explicit .begin() and .async_begin() methods;
         2) On execution of a first statement, which is strictly recommended method, because that avoids
         useless round trip

        This context manager is not thread-safe, so you should not manipulate on it concurrently.

        :param driver: A driver instance
        :param session_state: A state of session
        :param tx_mode: A transaction mode, which is a one from the following choices:
         1) SerializableReadWrite() which is default mode;
         2) OnlineReadOnly();
         3) StaleReadOnly().
        """
        self._driver = driver
        self._tx_state = _TxState(tx_mode)
        self._session_state = session_state
        self.session = session

    def __enter__(self):
        """
        Enters a context manager and returns a session
        :return: A session instance
        """
        return self

    def __exit__(self, *args, **kwargs):
        """
        Closes a transaction context manager and rollbacks transaction if
        it is not rolled back explicitly
        """
        if self._tx_state.tx_id is not None:
            # It's strictly recommended to close transactions directly
            # by using commit_tx=True flag while executing statement or by
            # .commit() or .rollback() methods, but here we trying to do best
            # effort to avoid useless open transactions
            logger.warning("Potentially leaked tx: %s", self._tx_state.tx_id)
            try:
                self.rollback()
            except issues.Error:
                logger.warning(
                    "Failed to rollback leaked tx: %s", self._tx_state.tx_id)

            self._tx_state.tx_id = None

    @property
    def session_id(self):
        """
        A transaction's session id
        :return: A transaction's session id
        """
        return self._session_state.session_id

    @property
    def tx_id(self):
        """
        Returns a id of open transaction or None otherwise
        :return: A id of open transaction or None otherwise
        """
        return self._tx_state.tx_id

    def async_execute(self, query, parameters=None, commit_tx=False, settings=None):
        """
        Sends a query (yql text or an instance of DataQuery) to be executed with parameters.
        Execution with parameters supported only for DataQuery instances and not supported for YQL text.

        :param query: A query: YQL text or DataQuery instance. E
        :param parameters: A dictionary with parameters values.
        :param commit_tx: A special flag that allows transaction commit
        :param settings: An additional request settings
        :return: A future of query execution
        """
        return self._driver.future(
            _execute_request_factory(self._session_state, self._tx_state, query, parameters, commit_tx),
            ydb_table_pb2_grpc.TableServiceStub,
            _ExecuteDataQuery,
            _wrap_result_and_tx_id,
            settings,
            (
                self._session_state,
                self._tx_state,
                query,
            )
        )

    def execute(self, query, parameters=None, commit_tx=False, settings=None):
        """
        Sends a query (yql text or an instance of DataQuery) to be executed with parameters.
        Execution with parameters supported only for DataQuery instances and is not supported yql text queries.

        :param query: A query, yql text or DataQuery instance.
        :param parameters: A dictionary with parameters values.
        :param commit_tx: A special flag that allows transaction commit
        :param settings: An additional request settings
        :return: A result sets or exception in case of execution errors
        """
        return self._driver(
            _execute_request_factory(self._session_state, self._tx_state, query, parameters, commit_tx),
            ydb_table_pb2_grpc.TableServiceStub,
            _ExecuteDataQuery,
            _wrap_result_and_tx_id,
            settings,
            (
                self._session_state,
                self._tx_state,
                query,
            )
        )

    def async_commit(self, settings=None):
        """
        Calls commit on a transaction if it is open otherwise is no-op. If transaction execution
        failed then this method raises PreconditionFailed.

        :param settings: A request settings
        :return: A future of commit call
        """
        if self._tx_state.tx_id is None and not self._tx_state.dead:
            return _wrap_in_future(self)
        return self._driver.future(
            _commit_request_factory(self._session_state, self._tx_state),
            ydb_table_pb2_grpc.TableServiceStub,
            _CommitTransaction,
            _wrap_result_on_rollback_or_commit_tx,
            settings,
            (
                self._session_state,
                self._tx_state,
                self
            )
        )

    def commit(self, settings=None):
        """
        Calls commit on a transaction if it is open otherwise is no-op. If transaction execution
        failed then this method raises PreconditionFailed.

        :param settings: A request settings
        :return: A committed transaction or exception if commit is failed
        """
        if self._tx_state.tx_id is None and not self._tx_state.dead:
            return self
        return self._driver(
            _commit_request_factory(self._session_state, self._tx_state),
            ydb_table_pb2_grpc.TableServiceStub,
            _CommitTransaction,
            _wrap_result_on_rollback_or_commit_tx,
            settings,
            (
                self._session_state,
                self._tx_state,
                self
            )
        )

    def async_rollback(self, settings=None):
        """
        Calls rollback on a transaction if it is open otherwise is no-op. If transaction execution
        failed then this method raises PreconditionFailed.

        :param settings: A request settings
        :return: A future of rollback call
        """
        if self._tx_state.tx_id is None and not self._tx_state.dead:
            return _wrap_in_future(self)
        return self._driver.future(
            _rollback_request_factory(self._session_state, self._tx_state),
            ydb_table_pb2_grpc.TableServiceStub,
            _RollbackTransaction,
            _wrap_result_on_rollback_or_commit_tx,
            settings,
            (
                self._session_state,
                self._tx_state,
                self
            )
        )

    def rollback(self, settings=None):
        """
        Calls rollback on a transaction if it is open otherwise is no-op. If transaction execution
        failed then this method raises PreconditionFailed.

        :param settings: A request settings
        :return: A rolled back transaction or exception if rollback is failed
        """
        if self._tx_state.tx_id is None and not self._tx_state.dead:
            return self
        return self._driver(
            _rollback_request_factory(self._session_state, self._tx_state),
            ydb_table_pb2_grpc.TableServiceStub,
            _RollbackTransaction,
            _wrap_result_on_rollback_or_commit_tx,
            settings,
            (
                self._session_state,
                self._tx_state,
                self
            )
        )

    def async_begin(self, settings=None):
        """
        Explicitly begins a transaction
        :param settings: A request settings
        :return: A future of begin call
        """
        if self._tx_state.tx_id is not None:
            return _wrap_in_future(self)
        return self._driver.future(
            _begin_request_factory(self._session_state, self._tx_state),
            ydb_table_pb2_grpc.TableServiceStub,
            _BeginTransaction,
            _wrap_tx_begin_response,
            settings,
            (
                self._session_state,
                self._tx_state,
                self
            )
        )

    def begin(self, settings=None):
        """
        Explicitly begins a transaction
        :param settings: A request settings
        :return: An open transaction
        """
        if self._tx_state.tx_id is not None:
            return self
        return self._driver(
            _begin_request_factory(self._session_state, self._tx_state),
            ydb_table_pb2_grpc.TableServiceStub,
            _BeginTransaction,
            _wrap_tx_begin_response,
            settings,
            (
                self._session_state,
                self._tx_state,
                self
            )
        )


class SessionPoolEmpty(queue.Empty):
    pass


class _SessionPoolState(object):
    def __init__(self):
        self._active_queue = queue.PriorityQueue()
        self._not_initialized = queue.Queue()

    def pick(self):
        try:
            return self._not_initialized.get_nowait()
        except queue.Empty:
            pass

        try:
            priority, session = self._active_queue.get_nowait()
        except queue.Empty:
            return None

        till_expire = priority - time.time()
        if till_expire < 4 * 60:
            if till_expire < 0:
                session.reset()

                return session

            return session
        self._active_queue.put((priority, session))
        return None

    def acquire(self, blocking=True, timeout=None):
        try:
            _, session = self._active_queue.get(blocking, timeout)
            return session
        except queue.Empty:
            raise SessionPoolEmpty

    def release(self, session):
        if session.session_id is None:
            self._not_initialized.put(session)
        else:
            priority = time.time() + 10 * 60
            self._active_queue.put((priority, session))


def _process_session(session, pool_state, initializer=None):
    if not session.initialized():
        try:
            session.create()
            if initializer is not None:
                initializer(session)
        except Exception as e:
            logger.debug("Failed to process session, %s", str(e))
            session.reset()
    else:
        try:
            session.keep_alive(settings.BaseRequestSettings().with_timeout(1))
        except issues.Error:
            session.reset()

    pool_state.release(session)


class _PoolThread(threading.Thread):
    def __init__(self, exec_pool, pool_state, initializer=None):
        super(_PoolThread, self).__init__()
        self.daemon = True
        self._exec_pool = exec_pool
        self._pool_state = pool_state
        self._condition = threading.Condition()
        self._spin_timeout = 3
        self._should_terminate = threading.Event()
        self._initializer = initializer

    def should_terminate(self):
        self._should_terminate.set()

    def run(self):
        with self._condition:
            while not self._should_terminate.is_set():
                self._condition.wait(self._spin_timeout)

                while not self._should_terminate.is_set():
                    session = self._pool_state.pick()

                    if session is None:
                        break

                    try:
                        self._exec_pool.submit(
                            _process_session, session, self._pool_state, self._initializer)
                    except RuntimeError as e:
                        logger.error("Failed to submit task, %s", str(e))
                        break


class SessionPool(object):
    def __init__(self, driver, size=100, workers_threads_count=4, initializer=None):
        """
        An object that encapsulates session creation, deletion, bad session handlers and maintains
        a pool of active sessions of specified size
        :param driver: A Driver instance
        :param size: A number of sessions to maintain in the pool
        :param workers_threads_count: A number of threads in execution pool
        :param initializer: A initializer callable that initializes created session
        """
        assert size >= 10

        self._driver = driver
        self._stop_guard = threading.Lock()
        self._stopped = False
        self._pool_state = _SessionPoolState()
        self._exec_pool = futures.ThreadPoolExecutor(workers_threads_count)
        self._pool_thread = _PoolThread(self._exec_pool, self._pool_state, initializer)
        self._pool_thread.start()
        for _ in range(size):
            self._pool_state.release(driver.table_client.session())

    def acquire(self, blocking=True, timeout=None):
        return self._pool_state.acquire(blocking, timeout)

    def release(self, session):
        self._pool_state.release(session)

    def checkout(self, blocking=True, timeout=None):
        return _SessionCheckout(self, blocking, timeout)

    def stop(self, timeout=None):
        """
        Experimental method
        :param timeout:
        """
        with self._stop_guard:
            if self._stopped:
                return

            self._stopped = True

        self._pool_thread.should_terminate()
        self._pool_thread.join(timeout)
        self._exec_pool.shutdown(wait=False)

    def __del__(self):

        self.stop()


class _SessionCheckout(object):
    __slots__ = ('_acquired', '_pool', '_blocking', '_timeout')

    def __init__(self, pool, blocking, timeout):
        """
        A context manager that checkouts a session from the specified pool and
        returns it on manager exit.
        :param pool: A SessionPool instance
        :param blocking: A flag that specifies that session acquire method should blocks
        :param timeout: A timeout in seconds for session acquire
        """
        self._pool = pool
        self._acquired = None
        self._blocking = blocking
        self._timeout = timeout

    def __enter__(self):
        self._acquired = self._pool.acquire(self._blocking, self._timeout)
        return self._acquired

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._acquired is not None:
            self._pool.release(self._acquired)
