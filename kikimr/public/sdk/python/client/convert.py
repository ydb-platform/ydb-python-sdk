# -*- coding: utf-8 -*-
import decimal
from google.protobuf import struct_pb2
import six

from . import issues, types, _apis


_SHIFT_BIT_COUNT = 64
_SHIFT = 2 ** 64
_SIGN_BIT = 2 ** 63
_DecimalNanRepr = 10 ** 35 + 1
_DecimalInfRepr = 10 ** 35
_DecimalSignedInfRepr = -(10**35)
_primitive_type_by_id = {}


def _initialize():
    for pt in types.PrimitiveType:
        _primitive_type_by_id[pt._idn_] = pt


_initialize()


class _DotDict(dict):
    def __init__(self, *args, **kwargs):
        super(_DotDict, self).__init__(*args, **kwargs)

    def __getattr__(self, item):
        return self[item]


def _is_decimal_signed(hi_value):
    return (hi_value & _SIGN_BIT) == _SIGN_BIT


def _pb_to_decimal(type_pb, value_pb, table_client_settings):
    hi = (value_pb.high_128 - (1 << _SHIFT_BIT_COUNT)) if _is_decimal_signed(value_pb.high_128) else value_pb.high_128
    int128_value = value_pb.low_128 + (hi << _SHIFT_BIT_COUNT)
    if int128_value == _DecimalNanRepr:
        return decimal.Decimal('Nan')
    elif int128_value == _DecimalInfRepr:
        return decimal.Decimal('Inf')
    elif int128_value == _DecimalSignedInfRepr:
        return decimal.Decimal('-Inf')
    return decimal.Decimal(int128_value) / decimal.Decimal(10 ** type_pb.decimal_type.scale)


def _pb_to_primitive(type_pb, value_pb, table_client_settings):
    return _primitive_type_by_id.get(type_pb.type_id).get_value(value_pb, table_client_settings)


def _pb_to_optional(type_pb, value_pb, table_client_settings):
    if value_pb.WhichOneof('value') == 'null_flag_value':
        return None
    if value_pb.WhichOneof('value') == 'nested_value':
        return _to_native_value(type_pb.optional_type.item, value_pb.nested_value, table_client_settings)
    return _to_native_value(type_pb.optional_type.item, value_pb, table_client_settings)


def _pb_to_list(type_pb, value_pb, table_client_settings):
    return [
        _to_native_value(type_pb.list_type.item, value_proto_item, table_client_settings)
        for value_proto_item in value_pb.items
    ]


def _pb_to_tuple(type_pb, value_pb, table_client_settings):
    return tuple(
        _to_native_value(item_type, item_value, table_client_settings)
        for item_type, item_value in six.moves.zip(type_pb.tuple_type.elements, value_pb.items)
    )


def _pb_to_dict(type_pb, value_pb, table_client_settings):
    result = {}
    for kv_pair in value_pb.pairs:
        key = _to_native_value(type_pb.dict_type.key, kv_pair.key, table_client_settings)
        payload = _to_native_value(type_pb.dict_type.payload, kv_pair.payload, table_client_settings)
        result[key] = payload
    return result


class _Struct(_DotDict):
    pass


def _pb_to_struct(type_pb, value_pb, table_client_settings):
    result = _Struct()
    for member, item in six.moves.zip(type_pb.struct_type.members, value_pb.items):
        result[member.name] = _to_native_value(member.type, item, table_client_settings)
    return result


def _pb_to_void(type_pb, value_pb, table_client_settings):
    return None


_to_native_map = {
    'type_id': _pb_to_primitive,
    'decimal_type': _pb_to_decimal,
    'optional_type': _pb_to_optional,
    'list_type': _pb_to_list,
    'tuple_type': _pb_to_tuple,
    'dict_type': _pb_to_dict,
    'struct_type': _pb_to_struct,
    'void_type': _pb_to_void,
}


def _to_native_value(type_pb, value_pb, table_client_settings=None):
    return _to_native_map.get(
        type_pb.WhichOneof("type"))(type_pb, value_pb, table_client_settings)


def _decimal_to_int128(value_type, value):
    if value.is_nan():
        return _DecimalNanRepr
    elif value.is_infinite():
        if value.is_signed():
            return _DecimalSignedInfRepr
        return _DecimalInfRepr

    sign, digits, exponent = value.as_tuple()
    int128_value = 0
    digits_count = 0
    for digit in digits:
        int128_value *= 10
        int128_value += digit
        digits_count += 1

    if value_type.decimal_type.scale + exponent < 0:
        raise issues.GenericError(
            "Couldn't parse decimal value, exponent is too large")

    for _ in range(value_type.decimal_type.scale + exponent):
        int128_value *= 10
        digits_count += 1

    if digits_count > value_type.decimal_type.precision + value_type.decimal_type.scale:
        raise issues.GenericError(
            "Couldn't parse decimal value, digits count > 35")

    if sign:
        int128_value *= -1

    return int128_value


def _decimal_to_pb(value_type, value):
    value_pb = _apis.ydb_value.Value()
    int128_value = _decimal_to_int128(value_type, value)
    if int128_value < 0:
        value_pb.high_128 = (int128_value >> _SHIFT_BIT_COUNT) + (1 << _SHIFT_BIT_COUNT)
        int128_value -= (int128_value >> _SHIFT_BIT_COUNT) << _SHIFT_BIT_COUNT
    else:
        value_pb.high_128 = int128_value >> _SHIFT_BIT_COUNT
        int128_value -= value_pb.high_128 << _SHIFT_BIT_COUNT
    value_pb.low_128 = int128_value
    return value_pb


def _primitive_to_pb(type_pb, value):
    value_pb = _apis.ydb_value.Value()
    data_type = _primitive_type_by_id.get(type_pb.type_id)
    data_type.set_value(value_pb, value)
    return value_pb


def _optional_to_pb(type_pb, value):
    if value is None:
        return _apis.ydb_value.Value(null_flag_value=struct_pb2.NULL_VALUE)
    return _from_native_value(type_pb.optional_type.item, value)


def _list_to_pb(type_pb, value):
    value_pb = _apis.ydb_value.Value()
    for element in value:
        value_item_proto = value_pb.items.add()
        value_item_proto.MergeFrom(_from_native_value(type_pb.list_type.item, element))
    return value_pb


def _tuple_to_pb(type_pb, value):
    value_pb = _apis.ydb_value.Value()
    for element_type, element_value in six.moves.zip(type_pb.tuple_type.elements, value):
        value_item_proto = value_pb.items.add()
        value_item_proto.MergeFrom(_from_native_value(element_type, element_value))
    return value_pb


def _dict_to_pb(type_pb, value):
    value_pb = _apis.ydb_value.Value()
    for key, payload in value.items():
        kv_pair = value_pb.pairs.add()
        kv_pair.key.MergeFrom(_from_native_value(type_pb.dict_type.key, key))
        kv_pair.payload.MergeFrom(_from_native_value(type_pb.dict_type.payload, payload))
    return value_pb


def _struct_to_pb(type_pb, value):
    value_pb = _apis.ydb_value.Value()
    for member in type_pb.struct_type.members:
        value_item_proto = value_pb.items.add()
        value_item = value[member.name] if isinstance(value, dict) else getattr(value, member.name)
        value_item_proto.MergeFrom(_from_native_value(member.type, value_item))
    return value_pb


_from_native_map = {
    'type_id': _primitive_to_pb,
    'decimal_type': _decimal_to_pb,
    'optional_type': _optional_to_pb,
    'list_type': _list_to_pb,
    'tuple_type': _tuple_to_pb,
    'dict_type': _dict_to_pb,
    'struct_type': _struct_to_pb,
}


def _decimal_type_to_native(type_pb):
    return types.DecimalType(type_pb.decimal_type.precision, type_pb.decimal_type.scale)


def _optional_type_to_native(type_pb):
    return types.OptionalType(
        type_to_native(type_pb.optional_type.item))


def _primitive_type_to_native(type_pb):
    return _primitive_type_by_id.get(type_pb.type_id)


_type_to_native_map = {
    'optional_type': _optional_type_to_native,
    'type_id': _primitive_type_to_native,
    'decimal_type': _decimal_type_to_native,
}


def type_to_native(type_pb):
    return _type_to_native_map.get(
        type_pb.WhichOneof('type'))(type_pb)


def _from_native_value(type_pb, value):
    return _from_native_map.get(
        type_pb.WhichOneof('type'))(type_pb, value)


def to_typed_value_from_native(type_pb, value):
    typed_value = _apis.ydb_value.TypedValue()
    typed_value.type.MergeFrom(type_pb)
    typed_value.value.MergeFrom(from_native_value(type_pb, value))
    return typed_value


def parameters_to_pb(parameters_types, parameters_values):
    if parameters_values is None or not parameters_values:
        return {}

    param_values_pb = {}
    for name, type_pb in six.iteritems(parameters_types):
        result = _apis.ydb_value.TypedValue()
        ttype = type_pb
        if isinstance(type_pb, types.AbstractTypeBuilder):
            ttype = type_pb.proto
        elif isinstance(type_pb, types.PrimitiveType):
            ttype = type_pb.proto
        result.type.MergeFrom(ttype)
        result.value.MergeFrom(_from_native_value(ttype, parameters_values[name]))
        param_values_pb[name] = result
    return param_values_pb


class _ResultSet(object):
    __slots__ = ('columns', 'rows', 'truncated')

    def __init__(self, columns, rows, truncated):
        self.columns = columns
        self.rows = rows
        self.truncated = truncated

    @classmethod
    def from_message(cls, message, table_client_settings=None):
        rows = []
        for row_proto in message.rows:
            row = _Row(message.columns)
            for column, value in six.moves.zip(message.columns, row_proto.items):
                row[column.name] = _to_native_value(column.type, value, table_client_settings)
            rows.append(row)
        return cls(message.columns, rows, message.truncated)


ResultSet = _ResultSet


class _Row(_DotDict):
    def __init__(self, columns):
        super(_Row, self).__init__()
        self._columns = columns

    def __getitem__(self, key):
        if isinstance(key, int):
            return self[self._columns[key].name]
        elif isinstance(key, slice):
            return tuple(map(lambda x: self[x.name], self._columns[key]))
        else:
            return super(_Row, self).__getitem__(key)


def from_native_value(type_pb, value):
    return _from_native_value(
        type_pb, value)


def to_native_value(typed_value):
    return _to_native_value(
        typed_value.type, typed_value.value)


class ResultSets(list):
    def __init__(self, result_sets_pb, table_client_settings=None):
        result_sets = []
        for result_set in result_sets_pb:
            result_sets.append(
                _ResultSet.from_message(
                    result_set,
                    table_client_settings,
                )
            )
        super(ResultSets, self).__init__(result_sets)
