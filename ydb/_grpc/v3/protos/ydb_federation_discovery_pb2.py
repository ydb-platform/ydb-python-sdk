# -*- coding: utf-8 -*-
# flake8: noqa
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: protos/ydb_federation_discovery.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from ydb._grpc.v3.protos import ydb_operation_pb2 as protos_dot_ydb__operation__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='protos/ydb_federation_discovery.proto',
  package='Ydb.FederationDiscovery',
  syntax='proto3',
  serialized_options=b'\n#tech.ydb.proto.federation.discoveryB\031FederationDiscoveryProtosZFgithub.com/ydb-platform/ydb-go-genproto/protos/Ydb_FederationDiscovery\370\001\001',
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n%protos/ydb_federation_discovery.proto\x12\x17Ydb.FederationDiscovery\x1a\x1aprotos/ydb_operation.proto\"\xf9\x01\n\x0c\x44\x61tabaseInfo\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0c\n\x04path\x18\x02 \x01(\t\x12\n\n\x02id\x18\x03 \x01(\t\x12\x10\n\x08\x65ndpoint\x18\x04 \x01(\t\x12\x10\n\x08location\x18\x05 \x01(\t\x12<\n\x06status\x18\x06 \x01(\x0e\x32,.Ydb.FederationDiscovery.DatabaseInfo.Status\x12\x0e\n\x06weight\x18\x07 \x01(\x03\"O\n\x06Status\x12\x16\n\x12STATUS_UNSPECIFIED\x10\x00\x12\r\n\tAVAILABLE\x10\x01\x12\r\n\tREAD_ONLY\x10\x02\x12\x0f\n\x0bUNAVAILABLE\x10\x03\" \n\x1eListFederationDatabasesRequest\"O\n\x1fListFederationDatabasesResponse\x12,\n\toperation\x18\x01 \x01(\x0b\x32\x19.Ydb.Operations.Operation\"\x9b\x01\n\x1dListFederationDatabasesResult\x12\x1e\n\x16\x63ontrol_plane_endpoint\x18\x01 \x01(\t\x12\x43\n\x14\x66\x65\x64\x65ration_databases\x18\x02 \x03(\x0b\x32%.Ydb.FederationDiscovery.DatabaseInfo\x12\x15\n\rself_location\x18\x03 \x01(\tB\x8b\x01\n#tech.ydb.proto.federation.discoveryB\x19\x46\x65\x64\x65rationDiscoveryProtosZFgithub.com/ydb-platform/ydb-go-genproto/protos/Ydb_FederationDiscovery\xf8\x01\x01\x62\x06proto3'
  ,
  dependencies=[protos_dot_ydb__operation__pb2.DESCRIPTOR,])



_DATABASEINFO_STATUS = _descriptor.EnumDescriptor(
  name='Status',
  full_name='Ydb.FederationDiscovery.DatabaseInfo.Status',
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
      name='AVAILABLE', index=1, number=1,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='READ_ONLY', index=2, number=2,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='UNAVAILABLE', index=3, number=3,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=265,
  serialized_end=344,
)
_sym_db.RegisterEnumDescriptor(_DATABASEINFO_STATUS)


_DATABASEINFO = _descriptor.Descriptor(
  name='DatabaseInfo',
  full_name='Ydb.FederationDiscovery.DatabaseInfo',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='name', full_name='Ydb.FederationDiscovery.DatabaseInfo.name', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='path', full_name='Ydb.FederationDiscovery.DatabaseInfo.path', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='id', full_name='Ydb.FederationDiscovery.DatabaseInfo.id', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='endpoint', full_name='Ydb.FederationDiscovery.DatabaseInfo.endpoint', index=3,
      number=4, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='location', full_name='Ydb.FederationDiscovery.DatabaseInfo.location', index=4,
      number=5, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='status', full_name='Ydb.FederationDiscovery.DatabaseInfo.status', index=5,
      number=6, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='weight', full_name='Ydb.FederationDiscovery.DatabaseInfo.weight', index=6,
      number=7, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
    _DATABASEINFO_STATUS,
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=95,
  serialized_end=344,
)


_LISTFEDERATIONDATABASESREQUEST = _descriptor.Descriptor(
  name='ListFederationDatabasesRequest',
  full_name='Ydb.FederationDiscovery.ListFederationDatabasesRequest',
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
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=346,
  serialized_end=378,
)


_LISTFEDERATIONDATABASESRESPONSE = _descriptor.Descriptor(
  name='ListFederationDatabasesResponse',
  full_name='Ydb.FederationDiscovery.ListFederationDatabasesResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='operation', full_name='Ydb.FederationDiscovery.ListFederationDatabasesResponse.operation', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
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
  serialized_start=380,
  serialized_end=459,
)


_LISTFEDERATIONDATABASESRESULT = _descriptor.Descriptor(
  name='ListFederationDatabasesResult',
  full_name='Ydb.FederationDiscovery.ListFederationDatabasesResult',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='control_plane_endpoint', full_name='Ydb.FederationDiscovery.ListFederationDatabasesResult.control_plane_endpoint', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='federation_databases', full_name='Ydb.FederationDiscovery.ListFederationDatabasesResult.federation_databases', index=1,
      number=2, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='self_location', full_name='Ydb.FederationDiscovery.ListFederationDatabasesResult.self_location', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
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
  serialized_start=462,
  serialized_end=617,
)

_DATABASEINFO.fields_by_name['status'].enum_type = _DATABASEINFO_STATUS
_DATABASEINFO_STATUS.containing_type = _DATABASEINFO
_LISTFEDERATIONDATABASESRESPONSE.fields_by_name['operation'].message_type = protos_dot_ydb__operation__pb2._OPERATION
_LISTFEDERATIONDATABASESRESULT.fields_by_name['federation_databases'].message_type = _DATABASEINFO
DESCRIPTOR.message_types_by_name['DatabaseInfo'] = _DATABASEINFO
DESCRIPTOR.message_types_by_name['ListFederationDatabasesRequest'] = _LISTFEDERATIONDATABASESREQUEST
DESCRIPTOR.message_types_by_name['ListFederationDatabasesResponse'] = _LISTFEDERATIONDATABASESRESPONSE
DESCRIPTOR.message_types_by_name['ListFederationDatabasesResult'] = _LISTFEDERATIONDATABASESRESULT
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

DatabaseInfo = _reflection.GeneratedProtocolMessageType('DatabaseInfo', (_message.Message,), {
  'DESCRIPTOR' : _DATABASEINFO,
  '__module__' : 'protos.ydb_federation_discovery_pb2'
  # @@protoc_insertion_point(class_scope:Ydb.FederationDiscovery.DatabaseInfo)
  })
_sym_db.RegisterMessage(DatabaseInfo)

ListFederationDatabasesRequest = _reflection.GeneratedProtocolMessageType('ListFederationDatabasesRequest', (_message.Message,), {
  'DESCRIPTOR' : _LISTFEDERATIONDATABASESREQUEST,
  '__module__' : 'protos.ydb_federation_discovery_pb2'
  # @@protoc_insertion_point(class_scope:Ydb.FederationDiscovery.ListFederationDatabasesRequest)
  })
_sym_db.RegisterMessage(ListFederationDatabasesRequest)

ListFederationDatabasesResponse = _reflection.GeneratedProtocolMessageType('ListFederationDatabasesResponse', (_message.Message,), {
  'DESCRIPTOR' : _LISTFEDERATIONDATABASESRESPONSE,
  '__module__' : 'protos.ydb_federation_discovery_pb2'
  # @@protoc_insertion_point(class_scope:Ydb.FederationDiscovery.ListFederationDatabasesResponse)
  })
_sym_db.RegisterMessage(ListFederationDatabasesResponse)

ListFederationDatabasesResult = _reflection.GeneratedProtocolMessageType('ListFederationDatabasesResult', (_message.Message,), {
  'DESCRIPTOR' : _LISTFEDERATIONDATABASESRESULT,
  '__module__' : 'protos.ydb_federation_discovery_pb2'
  # @@protoc_insertion_point(class_scope:Ydb.FederationDiscovery.ListFederationDatabasesResult)
  })
_sym_db.RegisterMessage(ListFederationDatabasesResult)


DESCRIPTOR._options = None
# @@protoc_insertion_point(module_scope)
