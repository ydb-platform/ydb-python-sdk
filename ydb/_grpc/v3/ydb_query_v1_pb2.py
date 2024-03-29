# -*- coding: utf-8 -*-
# flake8: noqa
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: ydb_query_v1.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from ydb._grpc.v3.protos import ydb_operation_pb2 as protos_dot_ydb__operation__pb2
from ydb._grpc.v3.protos import ydb_query_pb2 as protos_dot_ydb__query__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='ydb_query_v1.proto',
  package='Ydb.Query.V1',
  syntax='proto3',
  serialized_options=b'\n\027tech.ydb.proto.query.v1Z4github.com/ydb-platform/ydb-go-genproto/Ydb_Query_V1',
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x12ydb_query_v1.proto\x12\x0cYdb.Query.V1\x1a\x1aprotos/ydb_operation.proto\x1a\x16protos/ydb_query.proto2\xad\x06\n\x0cQueryService\x12R\n\rCreateSession\x12\x1f.Ydb.Query.CreateSessionRequest\x1a .Ydb.Query.CreateSessionResponse\x12R\n\rDeleteSession\x12\x1f.Ydb.Query.DeleteSessionRequest\x1a .Ydb.Query.DeleteSessionResponse\x12K\n\rAttachSession\x12\x1f.Ydb.Query.AttachSessionRequest\x1a\x17.Ydb.Query.SessionState0\x01\x12[\n\x10\x42\x65ginTransaction\x12\".Ydb.Query.BeginTransactionRequest\x1a#.Ydb.Query.BeginTransactionResponse\x12^\n\x11\x43ommitTransaction\x12#.Ydb.Query.CommitTransactionRequest\x1a$.Ydb.Query.CommitTransactionResponse\x12\x64\n\x13RollbackTransaction\x12%.Ydb.Query.RollbackTransactionRequest\x1a&.Ydb.Query.RollbackTransactionResponse\x12U\n\x0c\x45xecuteQuery\x12\x1e.Ydb.Query.ExecuteQueryRequest\x1a#.Ydb.Query.ExecuteQueryResponsePart0\x01\x12K\n\rExecuteScript\x12\x1f.Ydb.Query.ExecuteScriptRequest\x1a\x19.Ydb.Operations.Operation\x12\x61\n\x12\x46\x65tchScriptResults\x12$.Ydb.Query.FetchScriptResultsRequest\x1a%.Ydb.Query.FetchScriptResultsResponseBO\n\x17tech.ydb.proto.query.v1Z4github.com/ydb-platform/ydb-go-genproto/Ydb_Query_V1b\x06proto3'
  ,
  dependencies=[protos_dot_ydb__operation__pb2.DESCRIPTOR,protos_dot_ydb__query__pb2.DESCRIPTOR,])



_sym_db.RegisterFileDescriptor(DESCRIPTOR)


DESCRIPTOR._options = None

_QUERYSERVICE = _descriptor.ServiceDescriptor(
  name='QueryService',
  full_name='Ydb.Query.V1.QueryService',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_start=89,
  serialized_end=902,
  methods=[
  _descriptor.MethodDescriptor(
    name='CreateSession',
    full_name='Ydb.Query.V1.QueryService.CreateSession',
    index=0,
    containing_service=None,
    input_type=protos_dot_ydb__query__pb2._CREATESESSIONREQUEST,
    output_type=protos_dot_ydb__query__pb2._CREATESESSIONRESPONSE,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='DeleteSession',
    full_name='Ydb.Query.V1.QueryService.DeleteSession',
    index=1,
    containing_service=None,
    input_type=protos_dot_ydb__query__pb2._DELETESESSIONREQUEST,
    output_type=protos_dot_ydb__query__pb2._DELETESESSIONRESPONSE,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='AttachSession',
    full_name='Ydb.Query.V1.QueryService.AttachSession',
    index=2,
    containing_service=None,
    input_type=protos_dot_ydb__query__pb2._ATTACHSESSIONREQUEST,
    output_type=protos_dot_ydb__query__pb2._SESSIONSTATE,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='BeginTransaction',
    full_name='Ydb.Query.V1.QueryService.BeginTransaction',
    index=3,
    containing_service=None,
    input_type=protos_dot_ydb__query__pb2._BEGINTRANSACTIONREQUEST,
    output_type=protos_dot_ydb__query__pb2._BEGINTRANSACTIONRESPONSE,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='CommitTransaction',
    full_name='Ydb.Query.V1.QueryService.CommitTransaction',
    index=4,
    containing_service=None,
    input_type=protos_dot_ydb__query__pb2._COMMITTRANSACTIONREQUEST,
    output_type=protos_dot_ydb__query__pb2._COMMITTRANSACTIONRESPONSE,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='RollbackTransaction',
    full_name='Ydb.Query.V1.QueryService.RollbackTransaction',
    index=5,
    containing_service=None,
    input_type=protos_dot_ydb__query__pb2._ROLLBACKTRANSACTIONREQUEST,
    output_type=protos_dot_ydb__query__pb2._ROLLBACKTRANSACTIONRESPONSE,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='ExecuteQuery',
    full_name='Ydb.Query.V1.QueryService.ExecuteQuery',
    index=6,
    containing_service=None,
    input_type=protos_dot_ydb__query__pb2._EXECUTEQUERYREQUEST,
    output_type=protos_dot_ydb__query__pb2._EXECUTEQUERYRESPONSEPART,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='ExecuteScript',
    full_name='Ydb.Query.V1.QueryService.ExecuteScript',
    index=7,
    containing_service=None,
    input_type=protos_dot_ydb__query__pb2._EXECUTESCRIPTREQUEST,
    output_type=protos_dot_ydb__operation__pb2._OPERATION,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='FetchScriptResults',
    full_name='Ydb.Query.V1.QueryService.FetchScriptResults',
    index=8,
    containing_service=None,
    input_type=protos_dot_ydb__query__pb2._FETCHSCRIPTRESULTSREQUEST,
    output_type=protos_dot_ydb__query__pb2._FETCHSCRIPTRESULTSRESPONSE,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
])
_sym_db.RegisterServiceDescriptor(_QUERYSERVICE)

DESCRIPTOR.services_by_name['QueryService'] = _QUERYSERVICE

# @@protoc_insertion_point(module_scope)
