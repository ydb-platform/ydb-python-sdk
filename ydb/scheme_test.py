from .scheme import (
    SchemeEntryType,
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


def test_wrap_list_directory_response():
    d = _wrap_list_directory_response(None, ydb_scheme.ListDirectoryResponse())
    assert d.type is SchemeEntryType.TYPE_UNSPECIFIED
