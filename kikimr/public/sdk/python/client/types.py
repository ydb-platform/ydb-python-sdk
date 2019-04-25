# -*- coding: utf-8 -*-
import abc
import codecs

import enum

from yql.public.types import yql_types_pb2 as yql_types
from kikimr.public.api.protos import ydb_value_pb2 as ydb_value


def from_bytes(val):
    """
    Translates value into valid utf8 string
    :param val: A value to translate
    :return: A valid utf8 string
    """
    try:
        return codecs.decode(val, 'utf8')
    except (UnicodeEncodeError, TypeError):
        return val


@enum.unique
class PrimitiveType(enum.Enum):
    """
    Enumerates all available primitive types that can be used
    in computations.
    """
    Int32 = yql_types.Int32, 'int32_value'
    Uint32 = yql_types.Uint32, 'uint32_value'
    Int64 = yql_types.Int64, 'int64_value'
    Uint64 = yql_types.Uint64, 'uint64_value'
    Int8 = yql_types.Int8, 'int32_value'
    Uint8 = yql_types.Uint8, 'uint32_value'
    Int16 = yql_types.Int16, 'int32_value'
    Uint16 = yql_types.Uint16, 'uint32_value'
    Bool = yql_types.Bool, 'bool_value'
    Double = yql_types.Double, 'double_value'
    Float = yql_types.Float, 'float_value'

    String = yql_types.String, 'bytes_value'
    Utf8 = yql_types.Utf8, 'text_value', from_bytes

    Yson = yql_types.Yson, 'bytes_value'
    Json = yql_types.Json, 'text_value', from_bytes

    Date = yql_types.Date, 'uint32_value'
    Datetime = yql_types.Datetime, 'uint32_value'
    Timestamp = yql_types.Timestamp, 'uint64_value'
    Interval = yql_types.Interval, 'int64_value'

    def __init__(self, idn, proto_field, to_obj=None):
        self._idn_ = idn
        self._to_obj = to_obj
        self._proto_field = proto_field

    def get_value(self, value_pb):
        """
        Extracts value from protocol buffer
        :param value_pb: A protocol buffer
        :return: A valid value of primitive type
        """
        if self._to_obj is not None:
            return self._to_obj(getattr(value_pb, self._proto_field))
        return getattr(value_pb, self._proto_field)

    def set_value(self, pb, value):
        """
        Sets value in a protocol buffer
        :param pb: A protocol buffer
        :param value: A valid value to set
        :return: None
        """
        setattr(pb, self._proto_field, value)

    def __str__(self):
        return self._name_

    @property
    def proto(self):
        """
        Returns protocol buffer representation of a primitive type
        :return: A protocol buffer representation
        """
        return ydb_value.Type(type_id=self._idn_)


#######################
# A deprecated alias  #
#######################
DataType = PrimitiveType


class AbstractTypeBuilder(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def proto(self):
        """
        Returns protocol buffer representation of a type
        :return: A protocol buffer representation
        """
        pass


class DecimalType(AbstractTypeBuilder):
    __slots__ = ('_proto', '_precision', '_scale')

    def __init__(self, precision=22, scale=9):
        """
        Represents a decimal type
        :param precision: A precision value
        :param scale: A scale value
        """
        self._precision = precision
        self._scale = scale
        self._proto = ydb_value.Type()
        self._proto.decimal_type.MergeFrom(
            ydb_value.DecimalType(precision=self._precision, scale=self._scale))

    @property
    def precision(self):
        return self._precision

    @property
    def scale(self):
        return self._scale

    @property
    def proto(self):
        """
        Returns protocol buffer representation of a type
        :return: A protocol buffer representation
        """
        return self._proto

    def __str__(self):
        """
        Returns string representation of a type
        :return: A string representation
        """
        return 'Decimal(%d,%d)' % (self._precision, self._scale)


class OptionalType(AbstractTypeBuilder):
    __slots__ = ('_repr', '_proto', '_item')

    def __init__(self, optional_type):
        """
        Represents optional type that wraps inner type
        :param optional_type: An instance of an inner type
        """
        self._repr = "%s?" % str(optional_type)
        self._proto = ydb_value.Type()
        self._item = optional_type
        self._proto.optional_type.MergeFrom(
            ydb_value.OptionalType(item=optional_type.proto))

    @property
    def item(self):
        return self._item

    @property
    def proto(self):
        """
        Returns protocol buffer representation of a type
        :return: A protocol buffer representation
        """
        return self._proto

    def __str__(self):
        return self._repr


class ListType(AbstractTypeBuilder):
    __slots__ = ('_repr', '_proto')

    def __init__(self, list_type):
        """
        :param list_type: List item type builder
        """
        self._repr = "List<%s>" % str(list_type)
        self._proto = ydb_value.Type(
            list_type=ydb_value.ListType(
                item=list_type.proto
            )
        )

    @property
    def proto(self):
        """
        Returns protocol buffer representation of type
        :return: A protocol buffer representation
        """
        return self._proto

    def __str__(self):
        return self._repr


class DictType(AbstractTypeBuilder):
    __slots__ = ('__repr', '__proto')

    def __init__(self, key_type, payload_type):
        """
        :param key_type: Key type builder
        :param payload_type: Payload type builder
        """
        self._repr = "Dict<%s,%s>" % (str(key_type), str(payload_type))
        self._proto = ydb_value.Type(
            dict_type=ydb_value.DictType(
                key=key_type.proto,
                payload=payload_type.proto,
            )
        )

    @property
    def proto(self):
        return self._proto

    def __str__(self):
        return self._repr


class TupleType(AbstractTypeBuilder):
    __slots__ = ('__elements_repr', '__proto')

    def __init__(self):
        self.__elements_repr = []
        self.__proto = ydb_value.Type(tuple_type=ydb_value.TupleType())

    def add_element(self, element_type):
        """
        :param element_type: Adds additional element of tuple
        :return: self
        """
        self.__elements_repr.append(str(element_type))
        element = self.__proto.tuple_type.elements.add()
        element.MergeFrom(element_type.proto)
        return self

    @property
    def proto(self):
        return self.__proto

    def __str__(self):
        return "Tuple<%s>" % ",".join(self.__elements_repr)


class StructType(AbstractTypeBuilder):
    __slots__ = ('__members_repr', '__proto')

    def __init__(self):
        self.__members_repr = []
        self.__proto = ydb_value.Type(struct_type=ydb_value.StructType())

    def add_member(self, name, member_type):
        """
        :param name:
        :param member_type:
        :return:
        """
        self.__members_repr.append("%s:%s" % (name, str(member_type)))
        member = self.__proto.struct_type.members.add()
        member.name = name
        member.type.MergeFrom(member_type.proto)
        return self

    @property
    def proto(self):
        return self.__proto

    def __str__(self):
        return "Struct<%s>" % ",".join(self.__members_repr)
