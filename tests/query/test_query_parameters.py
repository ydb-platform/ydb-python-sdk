import pytest
import ydb


query = """SELECT $a AS value"""


def test_select_implicit_int(pool: ydb.QuerySessionPool):
    expected_value = 111
    res = pool.execute_with_retries(query, parameters={"$a": expected_value})
    actual_value = res[0].rows[0]["value"]
    assert expected_value == actual_value


def test_select_implicit_float(pool: ydb.QuerySessionPool):
    expected_value = 11.1
    res = pool.execute_with_retries(query, parameters={"$a": expected_value})
    actual_value = res[0].rows[0]["value"]
    assert expected_value == pytest.approx(actual_value)


def test_select_implicit_bool(pool: ydb.QuerySessionPool):
    expected_value = False
    res = pool.execute_with_retries(query, parameters={"$a": expected_value})
    actual_value = res[0].rows[0]["value"]
    assert expected_value == actual_value


def test_select_implicit_str(pool: ydb.QuerySessionPool):
    expected_value = "text"
    res = pool.execute_with_retries(query, parameters={"$a": expected_value})
    actual_value = res[0].rows[0]["value"]
    assert expected_value == actual_value


def test_select_implicit_list(pool: ydb.QuerySessionPool):
    expected_value = [1, 2, 3]
    res = pool.execute_with_retries(query, parameters={"$a": expected_value})
    actual_value = res[0].rows[0]["value"]
    assert expected_value == actual_value


def test_select_implicit_dict(pool: ydb.QuerySessionPool):
    expected_value = {"a": 1, "b": 2}
    res = pool.execute_with_retries(query, parameters={"$a": expected_value})
    actual_value = res[0].rows[0]["value"]
    assert expected_value == actual_value


def test_select_implicit_list_nested(pool: ydb.QuerySessionPool):
    expected_value = [{"a": 1}, {"b": 2}]
    res = pool.execute_with_retries(query, parameters={"$a": expected_value})
    actual_value = res[0].rows[0]["value"]
    assert expected_value == actual_value


def test_select_implicit_dict_nested(pool: ydb.QuerySessionPool):
    expected_value = {"a": [1, 2, 3], "b": [4, 5]}
    res = pool.execute_with_retries(query, parameters={"$a": expected_value})
    actual_value = res[0].rows[0]["value"]
    assert expected_value == actual_value


def test_select_explicit_primitive(pool: ydb.QuerySessionPool):
    expected_value = 111
    res = pool.execute_with_retries(query, parameters={"$a": (expected_value, ydb.PrimitiveType.Int64)})
    actual_value = res[0].rows[0]["value"]
    assert expected_value == actual_value


def test_select_explicit_list(pool: ydb.QuerySessionPool):
    expected_value = [1, 2, 3]
    type_ = ydb.ListType(ydb.PrimitiveType.Int64)
    res = pool.execute_with_retries(query, parameters={"$a": (expected_value, type_)})
    actual_value = res[0].rows[0]["value"]
    assert expected_value == actual_value


def test_select_explicit_dict(pool: ydb.QuerySessionPool):
    expected_value = {"key": "value"}
    type_ = ydb.DictType(ydb.PrimitiveType.Utf8, ydb.PrimitiveType.Utf8)
    res = pool.execute_with_retries(query, parameters={"$a": (expected_value, type_)})
    actual_value = res[0].rows[0]["value"]
    assert expected_value == actual_value
