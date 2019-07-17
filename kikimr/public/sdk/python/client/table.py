# -*- coding: utf-8 -*-
import abc
import logging
import time
import random
import enum
import six
from . import issues, convert, settings, scheme, types, _utilities, _apis, _sp_impl, _session_impl, _tx_ctx_impl

try:
    from . import interceptor
except ImportError:
    interceptor = None


logger = logging.getLogger(__name__)


##################################################################
# A deprecated aliases in case when direct import has been used  #
##################################################################
SessionPoolEmpty = issues.SessionPoolEmpty
DataQuery = types.DataQuery


class DescribeTableSettings(settings.BaseRequestSettings):
    def __init__(self):
        super(DescribeTableSettings, self).__init__()
        self.include_shard_key_bounds = False

    def with_include_shard_key_bounds(self, value):
        self.include_shard_key_bounds = value
        return self


class KeyBound(object):
    __slots__ = ('_equal', 'value', 'type')

    def __init__(self, key_value, key_type=None, inclusive=False):
        """
        Represents key bound.
        :param key_value: An iterable with key values
        :param key_type: A type of key
        :param inclusive: A flag that indicates bound includes key provided in the value.
        """

        try:
            iter(key_value)
        except TypeError:
            assert False, "value must be iterable!"

        if isinstance(key_type, types.TupleType):
            key_type = key_type.proto

        self._equal = inclusive
        self.value = key_value
        self.type = key_type

    def is_inclusive(self):
        return self._equal

    def is_exclusive(self):
        return not self._equal

    def __str__(self):
        if self._equal:
            return 'InclusiveKeyBound(Tuple%s)' % str(self.value)
        return 'ExclusiveKeyBound(Tuple%s)' % str(self.value)

    @classmethod
    def inclusive(cls, key_value, key_type):
        return cls(key_value, key_type, True)

    @classmethod
    def exclusive(cls, key_value, key_type):
        return cls(key_value, key_type, False)


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
        self._pb = _apis.ydb_table.CachingPolicy()
        self.preset_name = None

    def with_preset_name(self, preset_name):
        self._pb.preset_name = preset_name
        self.preset_name = preset_name
        return self

    def to_pb(self):
        return self._pb


class ExecutionPolicy(object):
    def __init__(self):
        self._pb = _apis.ydb_table.ExecutionPolicy()
        self.preset_name = None

    def with_preset_name(self, preset_name):
        self._pb.preset_name = preset_name
        self.preset_name = preset_name
        return self

    def to_pb(self):
        return self._pb


class CompactionPolicy(object):
    def __init__(self):
        self._pb = _apis.ydb_table.CompactionPolicy()
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
        self._pb = _apis.ydb_table.PartitioningPolicy()
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
            column_types = {}
            pk = set(table_description.primary_key)
            for column in table_description.columns:
                if column.name in pk:
                    column_types[column.name] = column.type

            for split_point in self.explicit_partitions.split_points:
                typed_value = self._pb.explicit_partitions.split_points.add()
                split_point_type = types.TupleType()
                prefix_size = len(split_point.value)
                for pl_el_id, pk_name in enumerate(table_description.primary_key):
                    if pl_el_id >= prefix_size:
                        break

                    split_point_type.add_element(column_types[pk_name])

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
        self._pb = _apis.ydb_table.ReplicationPolicy()
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
        return _apis.ydb_table.StorageSettings(storage_kind=self.storage_kind)


class StoragePolicy(object):
    def __init__(self):
        self._pb = _apis.ydb_table.StoragePolicy()
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
        pb = _apis.ydb_table.TableProfile()

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


@six.add_metaclass(abc.ABCMeta)
class AbstractTransactionModeBuilder(object):

    @property
    @abc.abstractmethod
    def name(self):
        pass

    @property
    @abc.abstractmethod
    def settings(self):
        pass


class SerializableReadWrite(AbstractTransactionModeBuilder):
    __slots__ = ('_pb', '_name')

    def __init__(self):
        self._name = 'serializable_read_write'
        self._pb = _apis.ydb_table.SerializableModeSettings()

    @property
    def settings(self):
        return self._pb

    @property
    def name(self):
        return self._name


class OnlineReadOnly(AbstractTransactionModeBuilder):
    __slots__ = ('_pb', '_name')

    def __init__(self):
        self._pb = _apis.ydb_table.OnlineModeSettings()
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
        self._pb = _apis.ydb_table.StaleModeSettings()
        self._name = 'stale_read_only'

    @property
    def settings(self):
        return self._pb

    @property
    def name(self):
        return self._name


class RetrySettings(object):
    def __init__(
            self, max_retries=10,
            max_session_acquire_timeout=3,
            on_ydb_error_callback=None, backoff_ceiling=6, backoff_slot_duration=1,
            get_session_client_timeout=5):
        self.max_retries = max_retries
        self.max_session_acquire_timeout = max_session_acquire_timeout
        self.on_ydb_error_callback = lambda e: None if on_ydb_error_callback is None else on_ydb_error_callback
        self.backoff_ceiling = backoff_ceiling
        self.backoff_slot_duration = backoff_slot_duration
        self.retry_not_found = True
        self.retry_internal_error = True
        self.unknown_error_handler = lambda e: None
        self.get_session_client_timeout = get_session_client_timeout


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

        except (issues.Overloaded, issues.SessionPoolEmpty, issues.ConnectionError) as e:
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
            raise

    raise status


class TableClient(object):
    def __init__(self, driver):
        self._driver = driver

    def session(self):
        return Session(self._driver)


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


class SyncResponseIterator(object):
    def __init__(self, it, wrapper):
        self.it = it
        self.wrapper = wrapper

    def cancel(self):
        self.it.cancel()
        return self

    def __iter__(self):
        return self

    def _next(self):
        return self.wrapper(next(self.it))

    def next(self):
        return self._next()

    def __next__(self):
        return self._next()


class AsyncResponseIterator(object):
    def __init__(self, it, wrapper):
        self.it = it
        self.wrapper = wrapper

    def cancel(self):
        self.it.cancel()
        return self

    def __iter__(self):
        return self

    def _next(self):
        return interceptor.operate_async_stream_call(self.it, self.wrapper)

    def next(self):
        return self._next()

    def __next__(self):
        return self._next()


class Session(object):
    __slots__ = ('_state', '_driver', '__weakref__')

    def __init__(self, driver):
        self._driver = driver
        self._state = _session_impl.SessionState()

    def __lt__(self, other):
        return self.session_id < other.session_id

    def __eq__(self, other):
        return self.session_id == other.session_id

    @property
    def session_id(self):
        """
        Return session_id.
        """
        return self._state.session_id

    def initialized(self):
        """
        Return True if session is successfully initialized with a session_id and False otherwise.
        """
        return self._state.session_id is not None

    def reset(self):
        """
        Perform session state reset (that includes cleanup of the session_id, query cache, and etc.)
        """
        return self._state.reset()

    def read_table(self, path, key_range=None, columns=(), ordered=False, row_limit=None):
        """
        Perform an read table request.

        from kikimr.public.sdk.python import client as ydb

        .... initialize driver and session ....

        key_prefix_type = ydb.TupleType().add_element(
            ydb.OptionalType(ydb.PrimitiveType.Uint64).add_element(
            ydb.OptionalType(ydb.PrimitiveType.Utf8))
        table_iterator = session.read_table(
            '/my/table',
            columns=('KeyColumn0', 'KeyColumn1', 'ValueColumn'),
            ydb.KeyRange(
                ydb.KeyBound((100, 'hundred'), key_prefix_type)
                ydb.KeyBound((200, 'two-hundreds'), key_prefix_type)
            )
        )

        while True:
            try:
                chunk = next(table_iterator)
                ... additional data processing ...
            except StopIteration:
                break

        :param path: A path to the table
        :param key_range: (optional) A KeyRange instance that describes a range to read. The KeyRange instance
        should include from_bound and/or to_bound. Each of the bounds (if provided) should specify a value of the
        key bound, and type of the key prefix. See an example above.
        :param columns: (optional) An iterable with table columns to read.
        :param ordered: (optional) A flag that indicates that result should be ordered.
        :param row_limit: (optional) A number of rows to read.
        :return: SyncResponseIterator instance
        """
        request = _session_impl.read_table_request_factory(self._state, path, key_range, columns, ordered, row_limit)
        stream_it = self._driver(request, _apis.TableService.Stub, _apis.TableService.StreamReadTable)
        return SyncResponseIterator(stream_it, _session_impl.wrap_read_table_response)

    def async_read_table(self, path, key_range=None, columns=(), ordered=False, row_limit=None):
        """
        Perform an read table request.

        from kikimr.public.sdk.python import client as ydb

        .... initialize driver and session ....

        key_prefix_type = ydb.TupleType().add_element(
            ydb.OptionalType(ydb.PrimitiveType.Uint64).add_element(
            ydb.OptionalType(ydb.PrimitiveType.Utf8))
        async_table_iterator = session.read_table(
            '/my/table',
            columns=('KeyColumn0', 'KeyColumn1', 'ValueColumn'),
            ydb.KeyRange(
                ydb.KeyBound((100, 'hundred'), key_prefix_type)
                ydb.KeyBound((200, 'two-hundreds'), key_prefix_type)
            )
        )

        while True:
            try:
                chunk_future = next(table_iterator)
                chunk = chunk_future.result()  # or any other way to await
                ... additional data processing ...
            except StopIteration:
                break

        :param path: A path to the table
        :param key_range: (optional) A KeyRange instance that describes a range to read. The KeyRange instance
        should include from_bound and/or to_bound. Each of the bounds (if provided) should specify a value of the
        key bound, and type of the key prefix. See an example above.
        :param columns: (optional) An iterable with table columns to read.
        :param ordered: (optional) A flag that indicates that result should be ordered.
        :param row_limit: (optional) A number of rows to read.
        :return: AsyncResponseIterator instance
        """
        if interceptor is None:
            raise RuntimeError("Async read table is not available due to import issues")
        request = _session_impl.read_table_request_factory(self._state, path, key_range, columns, ordered, row_limit)
        stream_it = self._driver(request, _apis.TableService.Stub, _apis.TableService.StreamReadTable)
        return AsyncResponseIterator(stream_it, _session_impl.wrap_read_table_response)

    def keep_alive(self, settings=None):
        return self._driver(
            _session_impl.keep_alive_request_factory(self._state),
            _apis.TableService.Stub,
            _apis.TableService.KeepAlive,
            _session_impl.wrap_keep_alive_response,
            settings,
            (self._state, self),
            self._state.endpoint,
        )

    @_utilities.wrap_async_call_exceptions
    def async_keep_alive(self, settings=None):
        return self._driver.future(
            _session_impl.keep_alive_request_factory(self._state),
            _apis.TableService.Stub,
            _apis.TableService.KeepAlive,
            _session_impl.wrap_keep_alive_response,
            settings,
            (self._state, self),
            self._state.endpoint,
        )

    @_utilities.wrap_async_call_exceptions
    def async_create(self, settings=None):
        if self._state.session_id is not None:
            return _utilities.wrap_result_in_future(self)
        return self._driver.future(
            _apis.ydb_table.CreateSessionRequest(),
            _apis.TableService.Stub,
            _apis.TableService.CreateSession,
            _session_impl.initialize_session,
            settings,
            (self._state, self),
            self._state.endpoint,
        )

    def create(self, settings=None):
        if self._state.session_id is not None:
            return self
        return self._driver(
            _apis.ydb_table.CreateSessionRequest(),
            _apis.TableService.Stub,
            _apis.TableService.CreateSession,
            _session_impl.initialize_session,
            settings,
            (self._state, self),
            self._state.endpoint,
        )

    @_utilities.wrap_async_call_exceptions
    def async_delete(self, settings=None):
        return self._driver.future(
            self._state.attach_request(_apis.ydb_table.DeleteSessionRequest()),
            _apis.TableService.Stub,
            _apis.TableService.DeleteSession,
            _session_impl.cleanup_session,
            settings,
            (self._state, self),
            self._state.endpoint,
        )

    def delete(self, settings=None):
        return self._driver(
            self._state.attach_request(_apis.ydb_table.DeleteSessionRequest()),
            _apis.TableService.Stub,
            _apis.TableService.DeleteSession,
            _session_impl.cleanup_session,
            settings,
            (self._state, self),
            self._state.endpoint,
        )

    @_utilities.wrap_async_call_exceptions
    def async_execute_scheme(self, yql_text, settings=None):
        return self._driver.future(
            _session_impl.execute_scheme_request_factory(self._state, yql_text),
            _apis.TableService.Stub,
            _apis.TableService.ExecuteSchemeQuery,
            _session_impl.wrap_execute_scheme_result,
            settings,
            (self._state,),
            self._state.endpoint,
        )

    def execute_scheme(self, yql_text, settings=None):
        return self._driver(
            _session_impl.execute_scheme_request_factory(self._state, yql_text),
            _apis.TableService.Stub,
            _apis.TableService.ExecuteSchemeQuery,
            _session_impl.wrap_execute_scheme_result,
            settings,
            (self._state,),
            self._state.endpoint,
        )

    def transaction(self, tx_mode=None):
        return TxContext(self._driver, self._state, self, tx_mode)

    def has_prepared(self, query):
        return query in self._state

    @_utilities.wrap_async_call_exceptions
    def async_prepare(self, query, settings=None):
        data_query, _ = self._state.lookup(query)
        if data_query is not None:
            return _utilities.wrap_result_in_future(data_query)
        return self._driver.future(
            _session_impl.prepare_request_factory(self._state, query),
            _apis.TableService.Stub,
            _apis.TableService.PrepareDataQuery,
            _session_impl.wrap_prepare_query_response,
            settings,
            (self._state, query,),
            self._state.endpoint,
        )

    def prepare(self, query, settings=None):
        data_query, _ = self._state.lookup(query)
        if data_query is not None:
            return data_query
        return self._driver(
            _session_impl.prepare_request_factory(self._state, query),
            _apis.TableService.Stub,
            _apis.TableService.PrepareDataQuery,
            _session_impl.wrap_prepare_query_response,
            settings,
            (self._state, query),
            self._state.endpoint,
        )

    @_utilities.wrap_async_call_exceptions
    def async_create_table(self, path, table_description, settings=None):
        return self._driver.future(
            _session_impl.create_table_request_factory(self._state, path, table_description),
            _apis.TableService.Stub,
            _apis.TableService.CreateTable,
            _session_impl.wrap_operation,
            settings,
            (self._driver, ),
            self._state.endpoint,
        )

    def create_table(self, path, table_description, settings=None):
        """
        Create a YDB table.

        from kikimr.public.sdk.python import client as ydb

        ... create an instance of Driver ...

        description = (
            ydb.TableDescription()
            .with_primary_keys('key1', 'key2')
            .with_columns(
                ydb.Column('key1', ydb.OptionalType(ydb.PrimitiveType.Uint64)),
                ydb.Column('key2', ydb.OptionalType(ydb.PrimitiveType.Uint64)),
                ydb.Column('value', ydb.OptionalType(ydb.PrimitiveType.Utf8))
            )
            .with_profile(
                ydb.TableProfile()
                .with_partitioning_policy(
                    ydb.PartitioningPolicy()
                    .with_explicit_partitions(
                        ydb.ExplicitPartitions(
                            (
                                ydb.KeyBound((100, )),
                                ydb.KeyBound((300, 100)),
                                ydb.KeyBound((400, )),
                            )
                        )
                    )
                )
            )
        )

        session = driver.table_client.session().create()
        session.create_table('/my/table/', description)

        :param path: A table path
        :param table_description: A description of table to create. An instance TableDescription
        :param settings: An instance of BaseRequestSettings that describes how rpc should invoked.
        :return: A description of created scheme entry or error otherwise.
        """
        return self._driver(
            _session_impl.create_table_request_factory(self._state, path, table_description),
            _apis.TableService.Stub,
            _apis.TableService.CreateTable,
            _session_impl.wrap_operation,
            settings,
            (self._driver,),
            self._state.endpoint,
        )

    @_utilities.wrap_async_call_exceptions
    def async_drop_table(self, path, settings=None):
        return self._driver.future(
            self._state.attach_request(_apis.ydb_table.DropTableRequest(path=path)),
            _apis.TableService.Stub,
            _apis.TableService.DropTable,
            _session_impl.wrap_operation,
            settings,
            (self._state,),
            self._state.endpoint,
        )

    def drop_table(self, path, settings=None):
        return self._driver(
            self._state.attach_request(_apis.ydb_table.DropTableRequest(path=path)),
            _apis.TableService.Stub,
            _apis.TableService.DropTable,
            _session_impl.wrap_operation,
            settings,
            (self._state,),
            self._state.endpoint,
        )

    @_utilities.wrap_async_call_exceptions
    def async_alter_table(self, path, add_columns, drop_columns, settings=None):
        return self._driver.future(
            _session_impl.alter_table_request_factory(self._state, path, add_columns, drop_columns),
            _apis.TableService.Stub,
            _apis.TableService.AlterTable,
            _session_impl.wrap_operation,
            settings,
            (self._state,),
            self._state.endpoint,
        )

    def alter_table(self, path, add_columns, drop_columns, settings=None):
        return self._driver(
            _session_impl.alter_table_request_factory(self._state, path, add_columns, drop_columns),
            _apis.TableService.Stub,
            _apis.TableService.AlterTable,
            _session_impl.wrap_operation,
            settings,
            (self._state,),
            self._state.endpoint,
        )

    @_utilities.wrap_async_call_exceptions
    def async_copy_table(self, source_path, destination_path, settings=None):
        return self._driver.future(
            _session_impl.copy_table_request_factory(self._state, source_path, destination_path),
            _apis.TableService.Stub,
            _apis.TableService.CopyTable,
            _session_impl.wrap_operation,
            settings,
            (self._state,),
            self._state.endpoint,
        )

    def copy_table(self, source_path, destination_path, settings=None):
        return self._driver(
            _session_impl.copy_table_request_factory(self._state, source_path, destination_path),
            _apis.TableService.Stub,
            _apis.TableService.CopyTable,
            _session_impl.wrap_operation,
            settings,
            (self._state,),
            self._state.endpoint,
        )

    @_utilities.wrap_async_call_exceptions
    def async_describe_table(self, path, settings=None):
        return self._driver.future(
            _session_impl.describe_table_request_factory(self._state, path, settings),
            _apis.TableService.Stub,
            _apis.TableService.DescribeTable,
            _session_impl.wrap_describe_table_response,
            settings,
            (self._state, TableSchemeEntry),
            self._state.endpoint,
        )

    def describe_table(self, path, settings=None):
        """
        Returns a description of the table by provided path
        :param path: A table path
        :param settings: A request settings
        :return: Description of a table
        """
        return self._driver(
            _session_impl.describe_table_request_factory(self._state, path, settings),
            _apis.TableService.Stub,
            _apis.TableService.DescribeTable,
            _session_impl.wrap_describe_table_response,
            settings,
            (self._state, TableSchemeEntry),
            self._state.endpoint,
        )


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
        tx_mode = SerializableReadWrite() if tx_mode is None else tx_mode
        self._tx_state = _tx_ctx_impl.TxState(tx_mode)
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

    @_utilities.wrap_async_call_exceptions
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
            _tx_ctx_impl.execute_request_factory(self._session_state, self._tx_state, query, parameters, commit_tx),
            _apis.TableService.Stub,
            _apis.TableService.ExecuteDataQuery,
            _tx_ctx_impl.wrap_result_and_tx_id,
            settings,
            (self._session_state, self._tx_state, query,),
            self._session_state.endpoint,
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
            _tx_ctx_impl.execute_request_factory(self._session_state, self._tx_state, query, parameters, commit_tx),
            _apis.TableService.Stub,
            _apis.TableService.ExecuteDataQuery,
            _tx_ctx_impl.wrap_result_and_tx_id,
            settings,
            (self._session_state, self._tx_state, query),
            self._session_state.endpoint,
        )

    def _explicit_tcl_call_future(self, request_factory, response_wrapper, stub_method):
        return self._driver.future(
            request_factory(self._session_state, self._tx_state),
            _apis.TableService.Stub,
            stub_method,
            response_wrapper,
            settings,
            (self._session_state, self._tx_state, self),
            self._session_state.endpoint,
        )

    @_utilities.wrap_async_call_exceptions
    def async_commit(self, settings=None):
        """
        Calls commit on a transaction if it is open otherwise is no-op. If transaction execution
        failed then this method raises PreconditionFailed.

        :param settings: A request settings (an instance of BaseRequestSettings)
        :return: A future of commit call
        """
        if self._tx_state.tx_id is None and not self._tx_state.dead:
            return _utilities.wrap_result_in_future(self)
        return self._driver.future(
            _tx_ctx_impl.commit_request_factory(self._session_state, self._tx_state),
            _apis.TableService.Stub,
            _apis.TableService.CommitTransaction,
            _tx_ctx_impl.wrap_result_on_rollback_or_commit_tx,
            settings,
            (self._session_state, self._tx_state, self),
            self._session_state.endpoint,
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
            _tx_ctx_impl.commit_request_factory(self._session_state, self._tx_state),
            _apis.TableService.Stub,
            _apis.TableService.CommitTransaction,
            _tx_ctx_impl.wrap_result_on_rollback_or_commit_tx,
            settings,
            (self._session_state, self._tx_state, self),
            self._session_state.endpoint,
        )

    @_utilities.wrap_async_call_exceptions
    def async_rollback(self, settings=None):
        """
        Calls rollback on a transaction if it is open otherwise is no-op. If transaction execution
        failed then this method raises PreconditionFailed.

        :param settings: A request settings
        :return: A future of rollback call
        """
        if self._tx_state.tx_id is None and not self._tx_state.dead:
            return _utilities.wrap_result_in_future(self)
        return self._driver.future(
            _tx_ctx_impl.rollback_request_factory(self._session_state, self._tx_state),
            _apis.TableService.Stub,
            _apis.TableService.RollbackTransaction,
            _tx_ctx_impl.wrap_result_on_rollback_or_commit_tx,
            settings,
            (self._session_state, self._tx_state, self),
            self._session_state.endpoint,
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
            _tx_ctx_impl.rollback_request_factory(self._session_state, self._tx_state),
            _apis.TableService.Stub,
            _apis.TableService.RollbackTransaction,
            _tx_ctx_impl.wrap_result_on_rollback_or_commit_tx,
            settings,
            (self._session_state, self._tx_state, self),
            self._session_state.endpoint
        )

    @_utilities.wrap_async_call_exceptions
    def async_begin(self, settings=None):
        """
        Explicitly begins a transaction
        :param settings: A request settings
        :return: A future of begin call
        """
        if self._tx_state.tx_id is not None:
            return _utilities.wrap_result_in_future(self)
        return self._driver.future(
            _tx_ctx_impl.begin_request_factory(self._session_state, self._tx_state),
            _apis.TableService.Stub,
            _apis.TableService.BeginTransaction,
            _tx_ctx_impl.wrap_tx_begin_response,
            settings,
            (self._session_state, self._tx_state, self),
            self._session_state.endpoint,
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
            _tx_ctx_impl.begin_request_factory(self._session_state, self._tx_state),
            _apis.TableService.Stub,
            _apis.TableService.BeginTransaction,
            _tx_ctx_impl.wrap_tx_begin_response,
            settings,
            (self._session_state, self._tx_state, self),
            self._session_state.endpoint,
        )


class SessionPool(object):
    def __init__(self, driver, size=100, workers_threads_count=4, initializer=None):
        """
        An object that encapsulates session creation, deletion and etc. and maintains
        a pool of active sessions of specified size
        :param driver: A Driver instance
        :param size: A maximum number of sessions to maintain in the pool
        """
        if initializer is not None:
            import warnings
            if initializer is not None:
                warnings.warn(
                    "Using initializer API in YDB SessionPool is deprecated and "
                    "will be removed in future releases! Please, don't use it in new code. "
                    "To prepare statements in session use keep in cache feature."
                )

        self._pool_impl = _sp_impl.SessionPoolImpl(driver, size, workers_threads_count, initializer)

    def retry_operation_sync(self, callee, retry_settings=None, *args, **kwargs):

        retry_settings = RetrySettings() if retry_settings is None else retry_settings

        def wrapped_callee():
            with self.checkout(blocking=False, timeout=retry_settings.get_session_client_timeout) as session:
                return callee(session, *args, **kwargs)

        return retry_operation_sync(wrapped_callee, retry_settings)

    def subscribe(self):
        return self._pool_impl.subscribe()

    def unsubscribe(self, waiter):
        return self._pool_impl.unsubscribe(waiter)

    def acquire(self, blocking=True, timeout=None):
        return self._pool_impl.acquire(blocking, timeout)

    def release(self, session):
        return self._pool_impl.put(session)

    def checkout(self, blocking=True, timeout=None):
        return SessionCheckout(self, blocking, timeout)

    def stop(self, timeout=None):
        self._pool_impl.stop(timeout)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


class SessionCheckout(object):
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
