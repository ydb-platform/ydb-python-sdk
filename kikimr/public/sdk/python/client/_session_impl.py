import functools
from . import issues, types, _apis, convert, scheme, operation, _utilities


def bad_session_handler(func):
    @functools.wraps(func)
    def decorator(rpc_state, response_pb, session_state, *args, **kwargs):
        try:
            return func(rpc_state, response_pb, session_state, *args, **kwargs)
        except issues.BadSession:
            session_state.reset()
            raise
    return decorator


@bad_session_handler
def wrap_prepare_query_response(rpc_state, response_pb, session_state, yql_text):
    session_state.complete_query()
    issues._process_response(response_pb)
    message = _apis.ydb_table.PrepareQueryResult()
    response_pb.result.Unpack(message)
    data_query = types.DataQuery(yql_text, message.parameters_types)
    session_state.keep(data_query, message.query_id)
    return data_query


def prepare_request_factory(session_state, yql_text):
    request = session_state.start_query().attach_request(_apis.ydb_table.PrepareDataQueryRequest())
    request.yql_text = yql_text
    return request


def copy_table_request_factory(session_state, source_path, destination_path):
    request = session_state.attach_request(_apis.ydb_table.CopyTableRequest())
    request.source_path = source_path
    request.destination_path = destination_path
    return request


@bad_session_handler
def wrap_execute_scheme_result(rpc_state, response_pb, session_state):
    session_state.complete_query()
    issues._process_response(response_pb)
    message = _apis.ydb_table.ExecuteQueryResult()
    response_pb.result.Unpack(message)
    return convert.ResultSets(message.result_sets)


def execute_scheme_request_factory(session_state, yql_text):
    request = session_state.start_query().attach_request(_apis.ydb_table.ExecuteSchemeQueryRequest())
    request.yql_text = yql_text
    return request


@bad_session_handler
def wrap_describe_table_response(rpc_state, response_pb, sesssion_state, scheme_entry_cls):
    issues._process_response(response_pb)
    message = _apis.ydb_table.DescribeTableResult()
    response_pb.result.Unpack(message)
    return scheme._wrap_scheme_entry(
        message.self,
        scheme_entry_cls,
        message.columns,
        message.primary_key,
        message.shard_key_bounds,
    )


def create_table_request_factory(session_state, path, table_description):
    request = _apis.ydb_table.CreateTableRequest()
    request.path = path
    request.primary_key.extend(list(table_description.primary_key))
    for column in table_description.columns:
        request.columns.add(name=column.name, type=column.type_pb)
    if table_description.profile is not None:
        request.profile.MergeFrom(table_description.profile.to_pb(table_description))
    return session_state.attach_request(request)


def keep_alive_request_factory(session_state):
    request = _apis.ydb_table.KeepAliveRequest()
    return session_state.attach_request(request)


@bad_session_handler
def cleanup_session(rpc_state, response_pb, session_state, session):
    issues._process_response(response_pb)
    session_state.reset()
    return session


@bad_session_handler
def initialize_session(rpc_state, response_pb, session_state, session):
    issues._process_response(response_pb)
    message = _apis.ydb_table.CreateSessionResult()
    response_pb.result.Unpack(message)
    session_state.set_id(message.session_id).attach_endpoint(rpc_state.endpoint)
    return session


@bad_session_handler
def wrap_operation(rpc_state, response_pb, session_state):
    return operation.Operation(rpc_state, response_pb)


@bad_session_handler
def wrap_keep_alive_response(rpc_state, response_pb, session_state, session):
    issues._process_response(response_pb)
    return session


def describe_table_request_factory(session_state, path, settings=None):
    request = session_state.attach_request(_apis.ydb_table.DescribeTableRequest())
    request.path = path

    if settings is not None and hasattr(settings, 'include_shard_key_bounds') and settings.include_shard_key_bounds:
        request.include_shard_key_bounds = settings.include_shard_key_bounds

    return request


def alter_table_request_factory(session_state, path, add_columns, drop_columns):
    request = session_state.attach_request(_apis.ydb_table.AlterTableRequest(path=path))
    for column in add_columns:
        request.add_columns.add(name=column.name, type=column.type_pb)
    request.drop_columns.extend(list(drop_columns))
    return request


def read_table_request_factory(session_state, path, key_range=None, columns=None, ordered=False, row_limit=None):
    request = _apis.ydb_table.ReadTableRequest()
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


def wrap_read_table_response(response):
    issues._process_response(response)
    return convert.ResultSet.from_message(response.result.result_set)


class SessionState(object):
    def __init__(self):
        self._session_id = None
        self._query_cache = _utilities.LRUCache(1000)
        self._default = (None, None)
        self._pending_query = False
        self._endpoint = None

    def __contains__(self, query):
        return self.lookup(query) != self._default

    def reset(self):
        self._query_cache = _utilities.LRUCache(1000)
        self._session_id = None
        self._pending_query = False
        self._endpoint = None

    def attach_endpoint(self, endpoint):
        self._endpoint = endpoint
        return self

    @property
    def endpoint(self):
        return self._endpoint

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
        return query.name if isinstance(query, types.DataQuery) else _utilities.get_query_hash(query)

    def lookup(self, query):
        return self._query_cache.get(self._query_key(query), self._default)

    def erase(self, query):
        query, query_id = self.lookup(query)
        self._query_cache.erase(query.name)

    def complete_query(self):
        self._pending_query = False
        return self

    def start_query(self):
        if self._pending_query:
            # don't invalidate session at this point
            self.reset()
            raise issues.BadSession("Pending previous query completion!")
        self._pending_query = True
        return self

    def attach_request(self, request):
        if self._session_id is None:
            raise issues.BadSession("Empty session_id")
        request.session_id = self._session_id
        return request
