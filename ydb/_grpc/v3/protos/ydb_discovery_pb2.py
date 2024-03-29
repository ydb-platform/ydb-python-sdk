# -*- coding: utf-8 -*-
# flake8: noqa
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: protos/ydb_discovery.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from ydb._grpc.v3.protos import ydb_operation_pb2 as protos_dot_ydb__operation__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='protos/ydb_discovery.proto',
  package='Ydb.Discovery',
  syntax='proto3',
  serialized_options=b'\n\030tech.ydb.proto.discoveryB\017DiscoveryProtosZ<github.com/ydb-platform/ydb-go-genproto/protos/Ydb_Discovery\370\001\001',
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x1aprotos/ydb_discovery.proto\x12\rYdb.Discovery\x1a\x1aprotos/ydb_operation.proto\"9\n\x14ListEndpointsRequest\x12\x10\n\x08\x64\x61tabase\x18\x01 \x01(\t\x12\x0f\n\x07service\x18\x02 \x03(\t\"\xc3\x01\n\x0c\x45ndpointInfo\x12\x0f\n\x07\x61\x64\x64ress\x18\x01 \x01(\t\x12\x0c\n\x04port\x18\x02 \x01(\r\x12\x13\n\x0bload_factor\x18\x03 \x01(\x02\x12\x0b\n\x03ssl\x18\x04 \x01(\x08\x12\x0f\n\x07service\x18\x05 \x03(\t\x12\x10\n\x08location\x18\x06 \x01(\t\x12\x0f\n\x07node_id\x18\x07 \x01(\r\x12\r\n\x05ip_v4\x18\x08 \x03(\t\x12\r\n\x05ip_v6\x18\t \x03(\t\x12 \n\x18ssl_target_name_override\x18\n \x01(\t\"\\\n\x13ListEndpointsResult\x12.\n\tendpoints\x18\x01 \x03(\x0b\x32\x1b.Ydb.Discovery.EndpointInfo\x12\x15\n\rself_location\x18\x02 \x01(\t\"E\n\x15ListEndpointsResponse\x12,\n\toperation\x18\x01 \x01(\x0b\x32\x19.Ydb.Operations.Operation\"\'\n\rWhoAmIRequest\x12\x16\n\x0einclude_groups\x18\x01 \x01(\x08\",\n\x0cWhoAmIResult\x12\x0c\n\x04user\x18\x01 \x01(\t\x12\x0e\n\x06groups\x18\x02 \x03(\t\">\n\x0eWhoAmIResponse\x12,\n\toperation\x18\x01 \x01(\x0b\x32\x19.Ydb.Operations.Operation\"\xe0\x02\n\x0cNodeLocation\x12 \n\x0f\x64\x61ta_center_num\x18\x01 \x01(\rB\x02\x18\x01H\x00\x88\x01\x01\x12\x19\n\x08room_num\x18\x02 \x01(\rB\x02\x18\x01H\x01\x88\x01\x01\x12\x19\n\x08rack_num\x18\x03 \x01(\rB\x02\x18\x01H\x02\x88\x01\x01\x12\x19\n\x08\x62ody_num\x18\x04 \x01(\rB\x02\x18\x01H\x03\x88\x01\x01\x12\x17\n\x04\x62ody\x18\x94\x91\x06 \x01(\rB\x02\x18\x01H\x04\x88\x01\x01\x12\x18\n\x0b\x64\x61ta_center\x18\n \x01(\tH\x05\x88\x01\x01\x12\x13\n\x06module\x18\x14 \x01(\tH\x06\x88\x01\x01\x12\x11\n\x04rack\x18\x1e \x01(\tH\x07\x88\x01\x01\x12\x11\n\x04unit\x18( \x01(\tH\x08\x88\x01\x01\x42\x12\n\x10_data_center_numB\x0b\n\t_room_numB\x0b\n\t_rack_numB\x0b\n\t_body_numB\x07\n\x05_bodyB\x0e\n\x0c_data_centerB\t\n\x07_moduleB\x07\n\x05_rackB\x07\n\x05_unitBl\n\x18tech.ydb.proto.discoveryB\x0f\x44iscoveryProtosZ<github.com/ydb-platform/ydb-go-genproto/protos/Ydb_Discovery\xf8\x01\x01\x62\x06proto3'
  ,
  dependencies=[protos_dot_ydb__operation__pb2.DESCRIPTOR,])




_LISTENDPOINTSREQUEST = _descriptor.Descriptor(
  name='ListEndpointsRequest',
  full_name='Ydb.Discovery.ListEndpointsRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='database', full_name='Ydb.Discovery.ListEndpointsRequest.database', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='service', full_name='Ydb.Discovery.ListEndpointsRequest.service', index=1,
      number=2, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
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
  serialized_start=73,
  serialized_end=130,
)


_ENDPOINTINFO = _descriptor.Descriptor(
  name='EndpointInfo',
  full_name='Ydb.Discovery.EndpointInfo',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='address', full_name='Ydb.Discovery.EndpointInfo.address', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='port', full_name='Ydb.Discovery.EndpointInfo.port', index=1,
      number=2, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='load_factor', full_name='Ydb.Discovery.EndpointInfo.load_factor', index=2,
      number=3, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='ssl', full_name='Ydb.Discovery.EndpointInfo.ssl', index=3,
      number=4, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='service', full_name='Ydb.Discovery.EndpointInfo.service', index=4,
      number=5, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='location', full_name='Ydb.Discovery.EndpointInfo.location', index=5,
      number=6, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='node_id', full_name='Ydb.Discovery.EndpointInfo.node_id', index=6,
      number=7, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='ip_v4', full_name='Ydb.Discovery.EndpointInfo.ip_v4', index=7,
      number=8, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='ip_v6', full_name='Ydb.Discovery.EndpointInfo.ip_v6', index=8,
      number=9, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='ssl_target_name_override', full_name='Ydb.Discovery.EndpointInfo.ssl_target_name_override', index=9,
      number=10, type=9, cpp_type=9, label=1,
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
  serialized_start=133,
  serialized_end=328,
)


_LISTENDPOINTSRESULT = _descriptor.Descriptor(
  name='ListEndpointsResult',
  full_name='Ydb.Discovery.ListEndpointsResult',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='endpoints', full_name='Ydb.Discovery.ListEndpointsResult.endpoints', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='self_location', full_name='Ydb.Discovery.ListEndpointsResult.self_location', index=1,
      number=2, type=9, cpp_type=9, label=1,
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
  serialized_start=330,
  serialized_end=422,
)


_LISTENDPOINTSRESPONSE = _descriptor.Descriptor(
  name='ListEndpointsResponse',
  full_name='Ydb.Discovery.ListEndpointsResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='operation', full_name='Ydb.Discovery.ListEndpointsResponse.operation', index=0,
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
  serialized_start=424,
  serialized_end=493,
)


_WHOAMIREQUEST = _descriptor.Descriptor(
  name='WhoAmIRequest',
  full_name='Ydb.Discovery.WhoAmIRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='include_groups', full_name='Ydb.Discovery.WhoAmIRequest.include_groups', index=0,
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
  serialized_start=495,
  serialized_end=534,
)


_WHOAMIRESULT = _descriptor.Descriptor(
  name='WhoAmIResult',
  full_name='Ydb.Discovery.WhoAmIResult',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='user', full_name='Ydb.Discovery.WhoAmIResult.user', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='groups', full_name='Ydb.Discovery.WhoAmIResult.groups', index=1,
      number=2, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
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
  serialized_start=536,
  serialized_end=580,
)


_WHOAMIRESPONSE = _descriptor.Descriptor(
  name='WhoAmIResponse',
  full_name='Ydb.Discovery.WhoAmIResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='operation', full_name='Ydb.Discovery.WhoAmIResponse.operation', index=0,
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
  serialized_start=582,
  serialized_end=644,
)


_NODELOCATION = _descriptor.Descriptor(
  name='NodeLocation',
  full_name='Ydb.Discovery.NodeLocation',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='data_center_num', full_name='Ydb.Discovery.NodeLocation.data_center_num', index=0,
      number=1, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=b'\030\001', file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='room_num', full_name='Ydb.Discovery.NodeLocation.room_num', index=1,
      number=2, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=b'\030\001', file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='rack_num', full_name='Ydb.Discovery.NodeLocation.rack_num', index=2,
      number=3, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=b'\030\001', file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='body_num', full_name='Ydb.Discovery.NodeLocation.body_num', index=3,
      number=4, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=b'\030\001', file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='body', full_name='Ydb.Discovery.NodeLocation.body', index=4,
      number=100500, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=b'\030\001', file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='data_center', full_name='Ydb.Discovery.NodeLocation.data_center', index=5,
      number=10, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='module', full_name='Ydb.Discovery.NodeLocation.module', index=6,
      number=20, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='rack', full_name='Ydb.Discovery.NodeLocation.rack', index=7,
      number=30, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='unit', full_name='Ydb.Discovery.NodeLocation.unit', index=8,
      number=40, type=9, cpp_type=9, label=1,
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
    _descriptor.OneofDescriptor(
      name='_data_center_num', full_name='Ydb.Discovery.NodeLocation._data_center_num',
      index=0, containing_type=None,
      create_key=_descriptor._internal_create_key,
    fields=[]),
    _descriptor.OneofDescriptor(
      name='_room_num', full_name='Ydb.Discovery.NodeLocation._room_num',
      index=1, containing_type=None,
      create_key=_descriptor._internal_create_key,
    fields=[]),
    _descriptor.OneofDescriptor(
      name='_rack_num', full_name='Ydb.Discovery.NodeLocation._rack_num',
      index=2, containing_type=None,
      create_key=_descriptor._internal_create_key,
    fields=[]),
    _descriptor.OneofDescriptor(
      name='_body_num', full_name='Ydb.Discovery.NodeLocation._body_num',
      index=3, containing_type=None,
      create_key=_descriptor._internal_create_key,
    fields=[]),
    _descriptor.OneofDescriptor(
      name='_body', full_name='Ydb.Discovery.NodeLocation._body',
      index=4, containing_type=None,
      create_key=_descriptor._internal_create_key,
    fields=[]),
    _descriptor.OneofDescriptor(
      name='_data_center', full_name='Ydb.Discovery.NodeLocation._data_center',
      index=5, containing_type=None,
      create_key=_descriptor._internal_create_key,
    fields=[]),
    _descriptor.OneofDescriptor(
      name='_module', full_name='Ydb.Discovery.NodeLocation._module',
      index=6, containing_type=None,
      create_key=_descriptor._internal_create_key,
    fields=[]),
    _descriptor.OneofDescriptor(
      name='_rack', full_name='Ydb.Discovery.NodeLocation._rack',
      index=7, containing_type=None,
      create_key=_descriptor._internal_create_key,
    fields=[]),
    _descriptor.OneofDescriptor(
      name='_unit', full_name='Ydb.Discovery.NodeLocation._unit',
      index=8, containing_type=None,
      create_key=_descriptor._internal_create_key,
    fields=[]),
  ],
  serialized_start=647,
  serialized_end=999,
)

_LISTENDPOINTSRESULT.fields_by_name['endpoints'].message_type = _ENDPOINTINFO
_LISTENDPOINTSRESPONSE.fields_by_name['operation'].message_type = protos_dot_ydb__operation__pb2._OPERATION
_WHOAMIRESPONSE.fields_by_name['operation'].message_type = protos_dot_ydb__operation__pb2._OPERATION
_NODELOCATION.oneofs_by_name['_data_center_num'].fields.append(
  _NODELOCATION.fields_by_name['data_center_num'])
_NODELOCATION.fields_by_name['data_center_num'].containing_oneof = _NODELOCATION.oneofs_by_name['_data_center_num']
_NODELOCATION.oneofs_by_name['_room_num'].fields.append(
  _NODELOCATION.fields_by_name['room_num'])
_NODELOCATION.fields_by_name['room_num'].containing_oneof = _NODELOCATION.oneofs_by_name['_room_num']
_NODELOCATION.oneofs_by_name['_rack_num'].fields.append(
  _NODELOCATION.fields_by_name['rack_num'])
_NODELOCATION.fields_by_name['rack_num'].containing_oneof = _NODELOCATION.oneofs_by_name['_rack_num']
_NODELOCATION.oneofs_by_name['_body_num'].fields.append(
  _NODELOCATION.fields_by_name['body_num'])
_NODELOCATION.fields_by_name['body_num'].containing_oneof = _NODELOCATION.oneofs_by_name['_body_num']
_NODELOCATION.oneofs_by_name['_body'].fields.append(
  _NODELOCATION.fields_by_name['body'])
_NODELOCATION.fields_by_name['body'].containing_oneof = _NODELOCATION.oneofs_by_name['_body']
_NODELOCATION.oneofs_by_name['_data_center'].fields.append(
  _NODELOCATION.fields_by_name['data_center'])
_NODELOCATION.fields_by_name['data_center'].containing_oneof = _NODELOCATION.oneofs_by_name['_data_center']
_NODELOCATION.oneofs_by_name['_module'].fields.append(
  _NODELOCATION.fields_by_name['module'])
_NODELOCATION.fields_by_name['module'].containing_oneof = _NODELOCATION.oneofs_by_name['_module']
_NODELOCATION.oneofs_by_name['_rack'].fields.append(
  _NODELOCATION.fields_by_name['rack'])
_NODELOCATION.fields_by_name['rack'].containing_oneof = _NODELOCATION.oneofs_by_name['_rack']
_NODELOCATION.oneofs_by_name['_unit'].fields.append(
  _NODELOCATION.fields_by_name['unit'])
_NODELOCATION.fields_by_name['unit'].containing_oneof = _NODELOCATION.oneofs_by_name['_unit']
DESCRIPTOR.message_types_by_name['ListEndpointsRequest'] = _LISTENDPOINTSREQUEST
DESCRIPTOR.message_types_by_name['EndpointInfo'] = _ENDPOINTINFO
DESCRIPTOR.message_types_by_name['ListEndpointsResult'] = _LISTENDPOINTSRESULT
DESCRIPTOR.message_types_by_name['ListEndpointsResponse'] = _LISTENDPOINTSRESPONSE
DESCRIPTOR.message_types_by_name['WhoAmIRequest'] = _WHOAMIREQUEST
DESCRIPTOR.message_types_by_name['WhoAmIResult'] = _WHOAMIRESULT
DESCRIPTOR.message_types_by_name['WhoAmIResponse'] = _WHOAMIRESPONSE
DESCRIPTOR.message_types_by_name['NodeLocation'] = _NODELOCATION
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

ListEndpointsRequest = _reflection.GeneratedProtocolMessageType('ListEndpointsRequest', (_message.Message,), {
  'DESCRIPTOR' : _LISTENDPOINTSREQUEST,
  '__module__' : 'protos.ydb_discovery_pb2'
  # @@protoc_insertion_point(class_scope:Ydb.Discovery.ListEndpointsRequest)
  })
_sym_db.RegisterMessage(ListEndpointsRequest)

EndpointInfo = _reflection.GeneratedProtocolMessageType('EndpointInfo', (_message.Message,), {
  'DESCRIPTOR' : _ENDPOINTINFO,
  '__module__' : 'protos.ydb_discovery_pb2'
  # @@protoc_insertion_point(class_scope:Ydb.Discovery.EndpointInfo)
  })
_sym_db.RegisterMessage(EndpointInfo)

ListEndpointsResult = _reflection.GeneratedProtocolMessageType('ListEndpointsResult', (_message.Message,), {
  'DESCRIPTOR' : _LISTENDPOINTSRESULT,
  '__module__' : 'protos.ydb_discovery_pb2'
  # @@protoc_insertion_point(class_scope:Ydb.Discovery.ListEndpointsResult)
  })
_sym_db.RegisterMessage(ListEndpointsResult)

ListEndpointsResponse = _reflection.GeneratedProtocolMessageType('ListEndpointsResponse', (_message.Message,), {
  'DESCRIPTOR' : _LISTENDPOINTSRESPONSE,
  '__module__' : 'protos.ydb_discovery_pb2'
  # @@protoc_insertion_point(class_scope:Ydb.Discovery.ListEndpointsResponse)
  })
_sym_db.RegisterMessage(ListEndpointsResponse)

WhoAmIRequest = _reflection.GeneratedProtocolMessageType('WhoAmIRequest', (_message.Message,), {
  'DESCRIPTOR' : _WHOAMIREQUEST,
  '__module__' : 'protos.ydb_discovery_pb2'
  # @@protoc_insertion_point(class_scope:Ydb.Discovery.WhoAmIRequest)
  })
_sym_db.RegisterMessage(WhoAmIRequest)

WhoAmIResult = _reflection.GeneratedProtocolMessageType('WhoAmIResult', (_message.Message,), {
  'DESCRIPTOR' : _WHOAMIRESULT,
  '__module__' : 'protos.ydb_discovery_pb2'
  # @@protoc_insertion_point(class_scope:Ydb.Discovery.WhoAmIResult)
  })
_sym_db.RegisterMessage(WhoAmIResult)

WhoAmIResponse = _reflection.GeneratedProtocolMessageType('WhoAmIResponse', (_message.Message,), {
  'DESCRIPTOR' : _WHOAMIRESPONSE,
  '__module__' : 'protos.ydb_discovery_pb2'
  # @@protoc_insertion_point(class_scope:Ydb.Discovery.WhoAmIResponse)
  })
_sym_db.RegisterMessage(WhoAmIResponse)

NodeLocation = _reflection.GeneratedProtocolMessageType('NodeLocation', (_message.Message,), {
  'DESCRIPTOR' : _NODELOCATION,
  '__module__' : 'protos.ydb_discovery_pb2'
  # @@protoc_insertion_point(class_scope:Ydb.Discovery.NodeLocation)
  })
_sym_db.RegisterMessage(NodeLocation)


DESCRIPTOR._options = None
_NODELOCATION.fields_by_name['data_center_num']._options = None
_NODELOCATION.fields_by_name['room_num']._options = None
_NODELOCATION.fields_by_name['rack_num']._options = None
_NODELOCATION.fields_by_name['body_num']._options = None
_NODELOCATION.fields_by_name['body']._options = None
# @@protoc_insertion_point(module_scope)
