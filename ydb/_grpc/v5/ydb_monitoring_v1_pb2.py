# -*- coding: utf-8 -*-
# flake8: noqa
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: ydb_monitoring_v1.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from ydb._grpc.v5.protos import ydb_monitoring_pb2 as protos_dot_ydb__monitoring__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x17ydb_monitoring_v1.proto\x12\x11Ydb.Monitoring.V1\x1a\x1bprotos/ydb_monitoring.proto2\xb7\x01\n\x11MonitoringService\x12P\n\tSelfCheck\x12 .Ydb.Monitoring.SelfCheckRequest\x1a!.Ydb.Monitoring.SelfCheckResponse\x12P\n\tNodeCheck\x12 .Ydb.Monitoring.NodeCheckRequest\x1a!.Ydb.Monitoring.NodeCheckResponseBY\n\x1ctech.ydb.proto.monitoring.v1Z9github.com/ydb-platform/ydb-go-genproto/Ydb_Monitoring_V1b\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'ydb_monitoring_v1_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'\n\034tech.ydb.proto.monitoring.v1Z9github.com/ydb-platform/ydb-go-genproto/Ydb_Monitoring_V1'
  _MONITORINGSERVICE._serialized_start=76
  _MONITORINGSERVICE._serialized_end=259
# @@protoc_insertion_point(module_scope)
