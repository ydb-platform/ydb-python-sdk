from .scheme import (
    SchemeEntryType,
    _wrap_describe_path_response,
    _wrap_scheme_entry,
    _wrap_list_directory_response,
)
from ._apis import ydb_scheme


def test_wrap_scheme_entry():
    assert _wrap_scheme_entry(ydb_scheme.Entry(type=1)).type is SchemeEntryType.DIRECTORY
    assert _wrap_scheme_entry(ydb_scheme.Entry(type=17)).type is SchemeEntryType.TOPIC
    assert _wrap_scheme_entry(ydb_scheme.Entry(type=25)).type is SchemeEntryType.SECRET

    assert _wrap_scheme_entry(ydb_scheme.Entry()).type is SchemeEntryType.TYPE_UNSPECIFIED
    assert _wrap_scheme_entry(ydb_scheme.Entry(type=10)).type is SchemeEntryType.TYPE_UNSPECIFIED
    assert _wrap_scheme_entry(ydb_scheme.Entry(type=1001)).type is SchemeEntryType.TYPE_UNSPECIFIED


def test_wrap_scheme_entry_is_secret():
    secret = _wrap_scheme_entry(ydb_scheme.Entry(type=25))
    assert secret.is_secret()
    assert SchemeEntryType.is_secret(secret.type)

    not_secret = _wrap_scheme_entry(ydb_scheme.Entry(type=1))
    assert not not_secret.is_secret()
    assert not SchemeEntryType.is_secret(not_secret.type)


def test_wrap_scheme_entry_interrupt_permission_inheritance():
    assert not _wrap_scheme_entry(ydb_scheme.Entry()).interrupt_permission_inheritance
    assert _wrap_scheme_entry(ydb_scheme.Entry(interrupt_permission_inheritance=True)).interrupt_permission_inheritance


def test_wrap_list_directory_response():
    d = _wrap_list_directory_response(None, ydb_scheme.ListDirectoryResponse())
    assert d.type is SchemeEntryType.TYPE_UNSPECIFIED
    assert not d.interrupt_permission_inheritance


def test_wrap_list_directory_response_interrupt_permission_inheritance():
    result = ydb_scheme.ListDirectoryResult()
    result.self.interrupt_permission_inheritance = True
    result.children.add(type=1, interrupt_permission_inheritance=True)
    result.children.add(type=1)

    response = ydb_scheme.ListDirectoryResponse()
    response.operation.result.Pack(result)

    d = _wrap_list_directory_response(None, response)
    assert d.interrupt_permission_inheritance
    assert [child.interrupt_permission_inheritance for child in d.children] == [True, False]


def test_streaming_query_directory_and_description():
    result = ydb_scheme.ListDirectoryResult()
    result.children.add(name="stream", type=26)
    result.children.add(name="table", type=2)
    result.children.add(name="unknown", type=1001)
    response = ydb_scheme.ListDirectoryResponse()
    response.operation.result.Pack(result)

    directory = _wrap_list_directory_response(None, response)
    assert [child.name for child in directory.children] == ["stream", "table"]
    stream, table = directory.children
    assert stream.type is SchemeEntryType.STREAMING_QUERY
    assert stream.is_streaming_query()
    assert SchemeEntryType.is_streaming_query(stream.type)
    assert not table.is_streaming_query()

    description = ydb_scheme.DescribePathResult()
    description.self.name = "stream"
    description.self.type = 26
    describe_response = ydb_scheme.DescribePathResponse()
    describe_response.operation.result.Pack(description)
    assert _wrap_describe_path_response(None, describe_response).type is SchemeEntryType.STREAMING_QUERY

    description.self.type = 1001
    describe_response.operation.result.Pack(description)
    assert _wrap_describe_path_response(None, describe_response).type is SchemeEntryType.TYPE_UNSPECIFIED
