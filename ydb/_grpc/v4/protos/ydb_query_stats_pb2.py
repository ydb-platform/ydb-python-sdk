# -*- coding: utf-8 -*-
# flake8: noqa
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: protos/ydb_query_stats.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1cprotos/ydb_query_stats.proto\x12\x0eYdb.TableStats\"-\n\x0eOperationStats\x12\x0c\n\x04rows\x18\x01 \x01(\x04\x12\r\n\x05\x62ytes\x18\x02 \x01(\x04\"\xd1\x01\n\x10TableAccessStats\x12\x0c\n\x04name\x18\x01 \x01(\t\x12-\n\x05reads\x18\x03 \x01(\x0b\x32\x1e.Ydb.TableStats.OperationStats\x12/\n\x07updates\x18\x04 \x01(\x0b\x32\x1e.Ydb.TableStats.OperationStats\x12/\n\x07\x64\x65letes\x18\x05 \x01(\x0b\x32\x1e.Ydb.TableStats.OperationStats\x12\x18\n\x10partitions_count\x18\x06 \x01(\x04J\x04\x08\x02\x10\x03\"\xa3\x01\n\x0fQueryPhaseStats\x12\x13\n\x0b\x64uration_us\x18\x01 \x01(\x04\x12\x36\n\x0ctable_access\x18\x02 \x03(\x0b\x32 .Ydb.TableStats.TableAccessStats\x12\x13\n\x0b\x63pu_time_us\x18\x03 \x01(\x04\x12\x17\n\x0f\x61\x66\x66\x65\x63ted_shards\x18\x04 \x01(\x04\x12\x15\n\rliteral_phase\x18\x05 \x01(\x08\"P\n\x10\x43ompilationStats\x12\x12\n\nfrom_cache\x18\x01 \x01(\x08\x12\x13\n\x0b\x64uration_us\x18\x02 \x01(\x04\x12\x13\n\x0b\x63pu_time_us\x18\x03 \x01(\x04\"\xf4\x01\n\nQueryStats\x12\x35\n\x0cquery_phases\x18\x01 \x03(\x0b\x32\x1f.Ydb.TableStats.QueryPhaseStats\x12\x35\n\x0b\x63ompilation\x18\x02 \x01(\x0b\x32 .Ydb.TableStats.CompilationStats\x12\x1b\n\x13process_cpu_time_us\x18\x03 \x01(\x04\x12\x12\n\nquery_plan\x18\x04 \x01(\t\x12\x11\n\tquery_ast\x18\x05 \x01(\t\x12\x19\n\x11total_duration_us\x18\x06 \x01(\x04\x12\x19\n\x11total_cpu_time_us\x18\x07 \x01(\x04\x42R\n\x0etech.ydb.protoZ=github.com/ydb-platform/ydb-go-genproto/protos/Ydb_TableStats\xf8\x01\x01\x62\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'protos.ydb_query_stats_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'\n\016tech.ydb.protoZ=github.com/ydb-platform/ydb-go-genproto/protos/Ydb_TableStats\370\001\001'
  _OPERATIONSTATS._serialized_start=48
  _OPERATIONSTATS._serialized_end=93
  _TABLEACCESSSTATS._serialized_start=96
  _TABLEACCESSSTATS._serialized_end=305
  _QUERYPHASESTATS._serialized_start=308
  _QUERYPHASESTATS._serialized_end=471
  _COMPILATIONSTATS._serialized_start=473
  _COMPILATIONSTATS._serialized_end=553
  _QUERYSTATS._serialized_start=556
  _QUERYSTATS._serialized_end=800
# @@protoc_insertion_point(module_scope)
