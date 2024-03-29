# -*- coding: utf-8 -*-
# flake8: noqa
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: protos/ydb_common.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='protos/ydb_common.proto',
  package='Ydb',
  syntax='proto3',
  serialized_options=b'\n\025tech.ydb.proto.commonB\014CommonProtosZ2github.com/ydb-platform/ydb-go-genproto/protos/Ydb\370\001\001',
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x17protos/ydb_common.proto\x12\x03Ydb\"J\n\x0b\x46\x65\x61tureFlag\";\n\x06Status\x12\x16\n\x12STATUS_UNSPECIFIED\x10\x00\x12\x0b\n\x07\x45NABLED\x10\x01\x12\x0c\n\x08\x44ISABLED\x10\x02\"\"\n\x08\x43ostInfo\x12\x16\n\x0e\x63onsumed_units\x18\x01 \x01(\x01\"\x1d\n\rQuotaExceeded\x12\x0c\n\x04\x64isk\x18\x01 \x01(\x08\"4\n\x10VirtualTimestamp\x12\x11\n\tplan_step\x18\x01 \x01(\x04\x12\r\n\x05tx_id\x18\x02 \x01(\x04\x42\\\n\x15tech.ydb.proto.commonB\x0c\x43ommonProtosZ2github.com/ydb-platform/ydb-go-genproto/protos/Ydb\xf8\x01\x01\x62\x06proto3'
)



_FEATUREFLAG_STATUS = _descriptor.EnumDescriptor(
  name='Status',
  full_name='Ydb.FeatureFlag.Status',
  filename=None,
  file=DESCRIPTOR,
  create_key=_descriptor._internal_create_key,
  values=[
    _descriptor.EnumValueDescriptor(
      name='STATUS_UNSPECIFIED', index=0, number=0,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='ENABLED', index=1, number=1,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='DISABLED', index=2, number=2,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=47,
  serialized_end=106,
)
_sym_db.RegisterEnumDescriptor(_FEATUREFLAG_STATUS)


_FEATUREFLAG = _descriptor.Descriptor(
  name='FeatureFlag',
  full_name='Ydb.FeatureFlag',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
    _FEATUREFLAG_STATUS,
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=32,
  serialized_end=106,
)


_COSTINFO = _descriptor.Descriptor(
  name='CostInfo',
  full_name='Ydb.CostInfo',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='consumed_units', full_name='Ydb.CostInfo.consumed_units', index=0,
      number=1, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=108,
  serialized_end=142,
)


_QUOTAEXCEEDED = _descriptor.Descriptor(
  name='QuotaExceeded',
  full_name='Ydb.QuotaExceeded',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='disk', full_name='Ydb.QuotaExceeded.disk', index=0,
      number=1, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=144,
  serialized_end=173,
)


_VIRTUALTIMESTAMP = _descriptor.Descriptor(
  name='VirtualTimestamp',
  full_name='Ydb.VirtualTimestamp',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='plan_step', full_name='Ydb.VirtualTimestamp.plan_step', index=0,
      number=1, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='tx_id', full_name='Ydb.VirtualTimestamp.tx_id', index=1,
      number=2, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=175,
  serialized_end=227,
)

_FEATUREFLAG_STATUS.containing_type = _FEATUREFLAG
DESCRIPTOR.message_types_by_name['FeatureFlag'] = _FEATUREFLAG
DESCRIPTOR.message_types_by_name['CostInfo'] = _COSTINFO
DESCRIPTOR.message_types_by_name['QuotaExceeded'] = _QUOTAEXCEEDED
DESCRIPTOR.message_types_by_name['VirtualTimestamp'] = _VIRTUALTIMESTAMP
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

FeatureFlag = _reflection.GeneratedProtocolMessageType('FeatureFlag', (_message.Message,), {
  'DESCRIPTOR' : _FEATUREFLAG,
  '__module__' : 'protos.ydb_common_pb2'
  # @@protoc_insertion_point(class_scope:Ydb.FeatureFlag)
  })
_sym_db.RegisterMessage(FeatureFlag)

CostInfo = _reflection.GeneratedProtocolMessageType('CostInfo', (_message.Message,), {
  'DESCRIPTOR' : _COSTINFO,
  '__module__' : 'protos.ydb_common_pb2'
  # @@protoc_insertion_point(class_scope:Ydb.CostInfo)
  })
_sym_db.RegisterMessage(CostInfo)

QuotaExceeded = _reflection.GeneratedProtocolMessageType('QuotaExceeded', (_message.Message,), {
  'DESCRIPTOR' : _QUOTAEXCEEDED,
  '__module__' : 'protos.ydb_common_pb2'
  # @@protoc_insertion_point(class_scope:Ydb.QuotaExceeded)
  })
_sym_db.RegisterMessage(QuotaExceeded)

VirtualTimestamp = _reflection.GeneratedProtocolMessageType('VirtualTimestamp', (_message.Message,), {
  'DESCRIPTOR' : _VIRTUALTIMESTAMP,
  '__module__' : 'protos.ydb_common_pb2'
  # @@protoc_insertion_point(class_scope:Ydb.VirtualTimestamp)
  })
_sym_db.RegisterMessage(VirtualTimestamp)


DESCRIPTOR._options = None
# @@protoc_insertion_point(module_scope)
