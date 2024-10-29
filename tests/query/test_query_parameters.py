import uuid

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


def test_select_implicit_bytes(pool: ydb.QuerySessionPool):
    expected_value = b"text"
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


def test_select_implicit_custom_type_raises(pool: ydb.QuerySessionPool):
    class CustomClass:
        pass

    expected_value = CustomClass()
    with pytest.raises(ValueError):
        pool.execute_with_retries(query, parameters={"$a": expected_value})


def test_select_implicit_empty_list_raises(pool: ydb.QuerySessionPool):
    expected_value = []
    with pytest.raises(ValueError):
        pool.execute_with_retries(query, parameters={"$a": expected_value})


def test_select_implicit_empty_dict_raises(pool: ydb.QuerySessionPool):
    expected_value = {}
    with pytest.raises(ValueError):
        pool.execute_with_retries(query, parameters={"$a": expected_value})


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


def test_select_explicit_empty_list_not_raises(pool: ydb.QuerySessionPool):
    expected_value = []
    type_ = ydb.ListType(ydb.PrimitiveType.Int64)
    res = pool.execute_with_retries(query, parameters={"$a": (expected_value, type_)})
    actual_value = res[0].rows[0]["value"]
    assert expected_value == actual_value


def test_select_explicit_empty_dict_not_raises(pool: ydb.QuerySessionPool):
    expected_value = {}
    type_ = ydb.DictType(ydb.PrimitiveType.Utf8, ydb.PrimitiveType.Utf8)
    res = pool.execute_with_retries(query, parameters={"$a": (expected_value, type_)})
    actual_value = res[0].rows[0]["value"]
    assert expected_value == actual_value


def test_select_typedvalue_full_primitive(pool: ydb.QuerySessionPool):
    expected_value = 111
    typed_value = ydb.TypedValue(expected_value, ydb.PrimitiveType.Int64)
    res = pool.execute_with_retries(query, parameters={"$a": typed_value})
    actual_value = res[0].rows[0]["value"]
    assert expected_value == actual_value


def test_select_typedvalue_implicit_primitive(pool: ydb.QuerySessionPool):
    expected_value = 111
    typed_value = ydb.TypedValue(expected_value)
    res = pool.execute_with_retries(query, parameters={"$a": typed_value})
    actual_value = res[0].rows[0]["value"]
    assert expected_value == actual_value


def test_select_typevalue_custom_type_raises(pool: ydb.QuerySessionPool):
    class CustomClass:
        pass

    expected_value = CustomClass()
    typed_value = ydb.TypedValue(expected_value)
    with pytest.raises(ValueError):
        pool.execute_with_retries(query, parameters={"$a": typed_value})


def test_uuid_send(pool: ydb.QuerySessionPool):
    val = uuid.UUID("6E73B41C-4EDE-4D08-9CFB-B7462D9E498B")
    query = """
DECLARE $val AS UUID;

SELECT CAST($val AS Utf8) AS value
"""
    res = pool.execute_with_retries(query, parameters={"$val": ydb.TypedValue(val, ydb.PrimitiveType.UUID)})
    actual_value = res[0].rows[0]["value"]
    assert actual_value.upper() == str(val).upper()


def test_uuid_read(pool: ydb.QuerySessionPool):
    val = uuid.UUID("6E73B41C-4EDE-4D08-9CFB-B7462D9E498B")
    query = """
DECLARE $val AS Utf8;

SELECT CAST($val AS UUID) AS value
"""
    res = pool.execute_with_retries(query, parameters={"$val": ydb.TypedValue(str(val), ydb.PrimitiveType.Utf8)})
    actual_value = res[0].rows[0]["value"]
    assert actual_value.hex.upper() == val.hex.upper()
