import copy

import pytest

from unittest import mock
from . import issues, convert, types, _apis

from .retries import (
    retry_operation_impl,
    YdbRetryOperationFinalResult,
    YdbRetryOperationSleepOpt,
    RetrySettings,
)


def _build_int_result_set(n_rows, n_cols):
    result_set = _apis.ydb_value.ResultSet()
    for col_idx in range(n_cols):
        column = result_set.columns.add()
        column.name = "column_%d" % col_idx
        column.type.type_id = types.PrimitiveType.Int64._idn_
    for row_idx in range(n_rows):
        row = result_set.rows.add()
        for col_idx in range(n_cols):
            row.items.add().int64_value = row_idx * 1000 + col_idx
    return result_set


def test_result_set_row_access():
    message = _build_int_result_set(n_rows=1, n_cols=3)
    row = convert.ResultSet.from_message(message).rows[0]

    assert row["column_1"] == 1
    assert row.column_1 == 1
    assert row[1] == 1
    assert row[0:2] == (0, 1)
    assert dict(row) == {"column_0": 0, "column_1": 1, "column_2": 2}


def test_result_set_row_keeps_data_out_of_instance_dict():
    # Column values live in the dict base and `_columns` in a slot, never in a
    # per-instance __dict__ that would be multiplied across every row. The
    # __dict__ is lazy and stays empty until a caller attaches its own attribute.
    message = _build_int_result_set(n_rows=1, n_cols=3)
    row = convert.ResultSet.from_message(message).rows[0]
    assert row.__dict__ == {}


def test_result_set_row_allows_attribute_assignment():
    # Rows expose a __dict__ so callers can attach computed fields onto them
    # (ORM-style row.dt_created = ...); the memory optimization must keep that
    # working while leaving read-only rows unburdened.
    message = _build_int_result_set(n_rows=1, n_cols=3)
    row = convert.ResultSet.from_message(message).rows[0]

    row.dt_created = 123
    assert row.dt_created == 123
    assert row["column_0"] == 0


def test_result_set_row_attribute_shadows_column():
    # With a lazy __dict__, assigning an attribute that matches a column name
    # shadows the column for attribute access (normal lookup finds __dict__
    # before __getattr__ runs), while item access still reads the column value.
    message = _build_int_result_set(n_rows=1, n_cols=3)
    row = convert.ResultSet.from_message(message).rows[0]

    row.column_0 = "override"
    assert row.column_0 == "override"
    assert row["column_0"] == 0

    del row.column_0
    assert row.column_0 == 0


def test_lazy_result_set_row_allows_attribute_assignment():
    # _LazyRow inherits the lazy __dict__ from _DotDict too.
    message = _build_int_result_set(n_rows=1, n_cols=2)
    row = convert.ResultSet.lazy_from_message(message).rows.fetchone()

    row.dt_created = 123
    assert row.dt_created == 123
    assert row["column_0"] == 0


def test_struct_value_allows_attribute_assignment():
    # _Struct shares the lazy __dict__ from _DotDict.
    struct = convert._Struct()
    struct["a"] = 1

    struct.computed = 2
    assert struct.a == 1
    assert struct.computed == 2


def test_result_set_row_missing_attribute_raises_attribute_error():
    message = _build_int_result_set(n_rows=1, n_cols=1)
    row = convert.ResultSet.from_message(message).rows[0]

    assert not hasattr(row, "definitely_missing")
    with pytest.raises(AttributeError):
        row.definitely_missing


def test_result_set_row_is_copyable():
    message = _build_int_result_set(n_rows=1, n_cols=3)
    row = convert.ResultSet.from_message(message).rows[0]

    assert dict(copy.copy(row)) == dict(row)
    assert dict(copy.deepcopy(row)) == dict(row)
    # _columns must survive the copy so integer/slice indexing keeps working.
    assert copy.copy(row)[1] == 1
    assert copy.deepcopy(row)[0:2] == (0, 1)


def test_result_set_detached_from_source_message():
    # The converted result set must not hold a reference into the source
    # protobuf: otherwise the whole arena (raw rows included) stays alive for
    # the lifetime of the result, doubling memory usage on large reads.
    message = _build_int_result_set(n_rows=2, n_cols=2)
    result = convert.ResultSet.from_message(message)

    message.Clear()  # emulate the source proto being dropped/reused by the stream

    assert [column.name for column in result.columns] == ["column_0", "column_1"]
    # The DB-API cursor reads column.type on detached columns, so it must survive too.
    assert result.columns[0].type.type_id == types.PrimitiveType.Int64._idn_
    assert result.rows[0]["column_1"] == 1
    assert result.rows[1][0] == 1000
    assert result.rows[1][0:2] == (1000, 1001)


def test_retry_operation_impl(monkeypatch):
    monkeypatch.setattr("random.random", lambda: 0.5)
    monkeypatch.setattr(
        issues.Error,
        "__eq__",
        lambda self, other: type(self) is type(other) and self.message == other.message,
    )

    retry_once_settings = RetrySettings(
        max_retries=1,
        on_ydb_error_callback=mock.Mock(),
    )
    retry_once_settings.unknown_error_handler = mock.Mock()

    def get_results(callee):
        res_generator = retry_operation_impl(callee, retry_settings=retry_once_settings)
        results = []
        exc = None
        try:
            for res in res_generator:
                results.append(res)
                if isinstance(res, YdbRetryOperationFinalResult):
                    break
        except Exception as e:
            exc = e

        return results, exc

    class TestException(Exception):
        def __init__(self, message):
            super(TestException, self).__init__(message)
            self.message = message

        def __eq__(self, other):
            return type(self) is type(other) and self.message == other.message

    def check_unretriable_error(err_type, call_ydb_handler):
        retry_once_settings.on_ydb_error_callback.reset_mock()
        retry_once_settings.unknown_error_handler.reset_mock()

        results = get_results(mock.Mock(side_effect=[err_type("test1"), err_type("test2")]))
        yields = results[0]
        exc = results[1]

        assert yields == []
        assert exc == err_type("test1")

        if call_ydb_handler:
            assert retry_once_settings.on_ydb_error_callback.call_count == 1
            retry_once_settings.on_ydb_error_callback.assert_called_with(err_type("test1"))

            assert retry_once_settings.unknown_error_handler.call_count == 0
        else:
            assert retry_once_settings.on_ydb_error_callback.call_count == 0

            assert retry_once_settings.unknown_error_handler.call_count == 1
            retry_once_settings.unknown_error_handler.assert_called_with(err_type("test1"))

    def check_retriable_error(err_type, backoff):
        retry_once_settings.on_ydb_error_callback.reset_mock()

        results = get_results(mock.Mock(side_effect=[err_type("test1"), err_type("test2")]))
        yields = results[0]
        exc = results[1]

        if backoff:
            assert [
                YdbRetryOperationSleepOpt(backoff.calc_timeout(0)),
                YdbRetryOperationSleepOpt(backoff.calc_timeout(1)),
            ] == yields
        else:
            # Skip-yield error types (Aborted/BadSession/NotFound/InternalError): impl emits
            # SleepOpt(0.0) markers so consumers can rotate per-attempt bookkeeping
            # (e.g. ``ydb.Try`` spans get backoff_ms=0).
            assert [YdbRetryOperationSleepOpt(0.0), YdbRetryOperationSleepOpt(0.0)] == yields

        assert exc == err_type("test2")

        assert retry_once_settings.on_ydb_error_callback.call_count == 2
        retry_once_settings.on_ydb_error_callback.assert_any_call(err_type("test1"))
        retry_once_settings.on_ydb_error_callback.assert_called_with(err_type("test2"))

        assert retry_once_settings.unknown_error_handler.call_count == 0

    # check ok
    assert get_results(lambda: True) == ([YdbRetryOperationFinalResult(True)], None)

    # check retry error and return result
    assert get_results(mock.Mock(side_effect=[issues.Overloaded("test"), True])) == (
        [
            YdbRetryOperationSleepOpt(retry_once_settings.slow_backoff.calc_timeout(0)),
            YdbRetryOperationFinalResult(True),
        ],
        None,
    )

    # check errors
    check_retriable_error(issues.Aborted, None)
    check_retriable_error(issues.BadSession, None)

    check_retriable_error(issues.NotFound, None)
    with mock.patch.object(retry_once_settings, "retry_not_found", False):
        check_unretriable_error(issues.NotFound, True)

    check_retriable_error(issues.InternalError, None)
    with mock.patch.object(retry_once_settings, "retry_internal_error", False):
        check_unretriable_error(issues.InternalError, True)

    check_retriable_error(issues.Overloaded, retry_once_settings.slow_backoff)
    check_retriable_error(issues.SessionPoolEmpty, retry_once_settings.slow_backoff)
    check_retriable_error(issues.ConnectionError, retry_once_settings.slow_backoff)

    check_retriable_error(issues.Unavailable, retry_once_settings.fast_backoff)

    check_unretriable_error(issues.Undetermined, True)
    with mock.patch.object(retry_once_settings, "idempotent", True):
        check_retriable_error(issues.Unavailable, retry_once_settings.fast_backoff)

    check_unretriable_error(issues.Error, True)
    with mock.patch.object(retry_once_settings, "idempotent", True):
        check_unretriable_error(issues.Error, True)

    check_unretriable_error(TestException, False)
    with mock.patch.object(retry_once_settings, "idempotent", True):
        check_unretriable_error(TestException, False)
