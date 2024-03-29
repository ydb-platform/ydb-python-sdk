# -*- coding: utf-8 -*-
# flake8: noqa
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: ydb_coordination_v1.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from ydb._grpc.v3.protos import ydb_coordination_pb2 as protos_dot_ydb__coordination__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='ydb_coordination_v1.proto',
  package='Ydb.Coordination.V1',
  syntax='proto3',
  serialized_options=b'\n\036tech.ydb.proto.coordination.v1B\020CoordinationGrpcP\001Z;github.com/ydb-platform/ydb-go-genproto/Ydb_Coordination_V1',
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x19ydb_coordination_v1.proto\x12\x13Ydb.Coordination.V1\x1a\x1dprotos/ydb_coordination.proto2\xca\x03\n\x13\x43oordinationService\x12R\n\x07Session\x12 .Ydb.Coordination.SessionRequest\x1a!.Ydb.Coordination.SessionResponse(\x01\x30\x01\x12W\n\nCreateNode\x12#.Ydb.Coordination.CreateNodeRequest\x1a$.Ydb.Coordination.CreateNodeResponse\x12T\n\tAlterNode\x12\".Ydb.Coordination.AlterNodeRequest\x1a#.Ydb.Coordination.AlterNodeResponse\x12Q\n\x08\x44ropNode\x12!.Ydb.Coordination.DropNodeRequest\x1a\".Ydb.Coordination.DropNodeResponse\x12]\n\x0c\x44\x65scribeNode\x12%.Ydb.Coordination.DescribeNodeRequest\x1a&.Ydb.Coordination.DescribeNodeResponseBq\n\x1etech.ydb.proto.coordination.v1B\x10\x43oordinationGrpcP\x01Z;github.com/ydb-platform/ydb-go-genproto/Ydb_Coordination_V1b\x06proto3'
  ,
  dependencies=[protos_dot_ydb__coordination__pb2.DESCRIPTOR,])



_sym_db.RegisterFileDescriptor(DESCRIPTOR)


DESCRIPTOR._options = None

_COORDINATIONSERVICE = _descriptor.ServiceDescriptor(
  name='CoordinationService',
  full_name='Ydb.Coordination.V1.CoordinationService',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_start=82,
  serialized_end=540,
  methods=[
  _descriptor.MethodDescriptor(
    name='Session',
    full_name='Ydb.Coordination.V1.CoordinationService.Session',
    index=0,
    containing_service=None,
    input_type=protos_dot_ydb__coordination__pb2._SESSIONREQUEST,
    output_type=protos_dot_ydb__coordination__pb2._SESSIONRESPONSE,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='CreateNode',
    full_name='Ydb.Coordination.V1.CoordinationService.CreateNode',
    index=1,
    containing_service=None,
    input_type=protos_dot_ydb__coordination__pb2._CREATENODEREQUEST,
    output_type=protos_dot_ydb__coordination__pb2._CREATENODERESPONSE,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='AlterNode',
    full_name='Ydb.Coordination.V1.CoordinationService.AlterNode',
    index=2,
    containing_service=None,
    input_type=protos_dot_ydb__coordination__pb2._ALTERNODEREQUEST,
    output_type=protos_dot_ydb__coordination__pb2._ALTERNODERESPONSE,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='DropNode',
    full_name='Ydb.Coordination.V1.CoordinationService.DropNode',
    index=3,
    containing_service=None,
    input_type=protos_dot_ydb__coordination__pb2._DROPNODEREQUEST,
    output_type=protos_dot_ydb__coordination__pb2._DROPNODERESPONSE,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='DescribeNode',
    full_name='Ydb.Coordination.V1.CoordinationService.DescribeNode',
    index=4,
    containing_service=None,
    input_type=protos_dot_ydb__coordination__pb2._DESCRIBENODEREQUEST,
    output_type=protos_dot_ydb__coordination__pb2._DESCRIBENODERESPONSE,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
])
_sym_db.RegisterServiceDescriptor(_COORDINATIONSERVICE)

DESCRIPTOR.services_by_name['CoordinationService'] = _COORDINATIONSERVICE

# @@protoc_insertion_point(module_scope)
