# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: kikimr/public/api/protos/ydb_persqueue_cluster_discovery.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
from kikimr.public.api.protos import ydb_operation_pb2 as kikimr_dot_public_dot_api_dot_protos_dot_ydb__operation__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='kikimr/public/api/protos/ydb_persqueue_cluster_discovery.proto',
  package='Ydb.PersQueue.ClusterDiscovery',
  syntax='proto3',
  serialized_pb=_b('\n>kikimr/public/api/protos/ydb_persqueue_cluster_discovery.proto\x12\x1eYdb.PersQueue.ClusterDiscovery\x1a\x1bgoogle/protobuf/empty.proto\x1a,kikimr/public/api/protos/ydb_operation.proto\"o\n\x12WriteSessionParams\x12\r\n\x05topic\x18\x01 \x01(\t\x12\x11\n\tsource_id\x18\x02 \x01(\x0c\x12\x17\n\x0fpartition_group\x18\x03 \x01(\r\x12\x1e\n\x16preferred_cluster_name\x18\x04 \x01(\t\"@\n\x0b\x43lusterInfo\x12\x10\n\x08\x65ndpoint\x18\x01 \x01(\t\x12\x0c\n\x04name\x18\x02 \x01(\t\x12\x11\n\tavailable\x18\x03 \x01(\x08\"|\n\x11ReadSessionParams\x12\r\n\x05topic\x18\x01 \x01(\t\x12\x1b\n\x11mirror_to_cluster\x18\x02 \x01(\tH\x00\x12.\n\x0c\x61ll_original\x18\x03 \x01(\x0b\x32\x16.google.protobuf.EmptyH\x00\x42\x0b\n\tread_rule\"U\n\x14WriteSessionClusters\x12=\n\x08\x63lusters\x18\x01 \x03(\x0b\x32+.Ydb.PersQueue.ClusterDiscovery.ClusterInfo\"T\n\x13ReadSessionClusters\x12=\n\x08\x63lusters\x18\x01 \x03(\x0b\x32+.Ydb.PersQueue.ClusterDiscovery.ClusterInfo\"\x83\x02\n\x17\x44iscoverClustersRequest\x12\x39\n\x10operation_params\x18\x01 \x01(\x0b\x32\x1f.Ydb.Operations.OperationParams\x12J\n\x0ewrite_sessions\x18\x02 \x03(\x0b\x32\x32.Ydb.PersQueue.ClusterDiscovery.WriteSessionParams\x12H\n\rread_sessions\x18\x03 \x03(\x0b\x32\x31.Ydb.PersQueue.ClusterDiscovery.ReadSessionParams\x12\x17\n\x0fminimal_version\x18\x04 \x01(\x03\"H\n\x18\x44iscoverClustersResponse\x12,\n\toperation\x18\x01 \x01(\x0b\x32\x19.Ydb.Operations.Operation\"\xd5\x01\n\x16\x44iscoverClustersResult\x12U\n\x17write_sessions_clusters\x18\x01 \x03(\x0b\x32\x34.Ydb.PersQueue.ClusterDiscovery.WriteSessionClusters\x12S\n\x16read_sessions_clusters\x18\x02 \x03(\x0b\x32\x33.Ydb.PersQueue.ClusterDiscovery.ReadSessionClusters\x12\x0f\n\x07version\x18\x03 \x01(\x03\x42/\n*com.yandex.ydb.persqueue.cluster_discovery\xf8\x01\x01\x62\x06proto3')
  ,
  dependencies=[google_dot_protobuf_dot_empty__pb2.DESCRIPTOR,kikimr_dot_public_dot_api_dot_protos_dot_ydb__operation__pb2.DESCRIPTOR,])




_WRITESESSIONPARAMS = _descriptor.Descriptor(
  name='WriteSessionParams',
  full_name='Ydb.PersQueue.ClusterDiscovery.WriteSessionParams',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='topic', full_name='Ydb.PersQueue.ClusterDiscovery.WriteSessionParams.topic', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='source_id', full_name='Ydb.PersQueue.ClusterDiscovery.WriteSessionParams.source_id', index=1,
      number=2, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='partition_group', full_name='Ydb.PersQueue.ClusterDiscovery.WriteSessionParams.partition_group', index=2,
      number=3, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='preferred_cluster_name', full_name='Ydb.PersQueue.ClusterDiscovery.WriteSessionParams.preferred_cluster_name', index=3,
      number=4, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=173,
  serialized_end=284,
)


_CLUSTERINFO = _descriptor.Descriptor(
  name='ClusterInfo',
  full_name='Ydb.PersQueue.ClusterDiscovery.ClusterInfo',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='endpoint', full_name='Ydb.PersQueue.ClusterDiscovery.ClusterInfo.endpoint', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='name', full_name='Ydb.PersQueue.ClusterDiscovery.ClusterInfo.name', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='available', full_name='Ydb.PersQueue.ClusterDiscovery.ClusterInfo.available', index=2,
      number=3, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=286,
  serialized_end=350,
)


_READSESSIONPARAMS = _descriptor.Descriptor(
  name='ReadSessionParams',
  full_name='Ydb.PersQueue.ClusterDiscovery.ReadSessionParams',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='topic', full_name='Ydb.PersQueue.ClusterDiscovery.ReadSessionParams.topic', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='mirror_to_cluster', full_name='Ydb.PersQueue.ClusterDiscovery.ReadSessionParams.mirror_to_cluster', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='all_original', full_name='Ydb.PersQueue.ClusterDiscovery.ReadSessionParams.all_original', index=2,
      number=3, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
    _descriptor.OneofDescriptor(
      name='read_rule', full_name='Ydb.PersQueue.ClusterDiscovery.ReadSessionParams.read_rule',
      index=0, containing_type=None, fields=[]),
  ],
  serialized_start=352,
  serialized_end=476,
)


_WRITESESSIONCLUSTERS = _descriptor.Descriptor(
  name='WriteSessionClusters',
  full_name='Ydb.PersQueue.ClusterDiscovery.WriteSessionClusters',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='clusters', full_name='Ydb.PersQueue.ClusterDiscovery.WriteSessionClusters.clusters', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=478,
  serialized_end=563,
)


_READSESSIONCLUSTERS = _descriptor.Descriptor(
  name='ReadSessionClusters',
  full_name='Ydb.PersQueue.ClusterDiscovery.ReadSessionClusters',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='clusters', full_name='Ydb.PersQueue.ClusterDiscovery.ReadSessionClusters.clusters', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=565,
  serialized_end=649,
)


_DISCOVERCLUSTERSREQUEST = _descriptor.Descriptor(
  name='DiscoverClustersRequest',
  full_name='Ydb.PersQueue.ClusterDiscovery.DiscoverClustersRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='operation_params', full_name='Ydb.PersQueue.ClusterDiscovery.DiscoverClustersRequest.operation_params', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='write_sessions', full_name='Ydb.PersQueue.ClusterDiscovery.DiscoverClustersRequest.write_sessions', index=1,
      number=2, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='read_sessions', full_name='Ydb.PersQueue.ClusterDiscovery.DiscoverClustersRequest.read_sessions', index=2,
      number=3, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='minimal_version', full_name='Ydb.PersQueue.ClusterDiscovery.DiscoverClustersRequest.minimal_version', index=3,
      number=4, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=652,
  serialized_end=911,
)


_DISCOVERCLUSTERSRESPONSE = _descriptor.Descriptor(
  name='DiscoverClustersResponse',
  full_name='Ydb.PersQueue.ClusterDiscovery.DiscoverClustersResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='operation', full_name='Ydb.PersQueue.ClusterDiscovery.DiscoverClustersResponse.operation', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=913,
  serialized_end=985,
)


_DISCOVERCLUSTERSRESULT = _descriptor.Descriptor(
  name='DiscoverClustersResult',
  full_name='Ydb.PersQueue.ClusterDiscovery.DiscoverClustersResult',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='write_sessions_clusters', full_name='Ydb.PersQueue.ClusterDiscovery.DiscoverClustersResult.write_sessions_clusters', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='read_sessions_clusters', full_name='Ydb.PersQueue.ClusterDiscovery.DiscoverClustersResult.read_sessions_clusters', index=1,
      number=2, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='version', full_name='Ydb.PersQueue.ClusterDiscovery.DiscoverClustersResult.version', index=2,
      number=3, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=988,
  serialized_end=1201,
)

_READSESSIONPARAMS.fields_by_name['all_original'].message_type = google_dot_protobuf_dot_empty__pb2._EMPTY
_READSESSIONPARAMS.oneofs_by_name['read_rule'].fields.append(
  _READSESSIONPARAMS.fields_by_name['mirror_to_cluster'])
_READSESSIONPARAMS.fields_by_name['mirror_to_cluster'].containing_oneof = _READSESSIONPARAMS.oneofs_by_name['read_rule']
_READSESSIONPARAMS.oneofs_by_name['read_rule'].fields.append(
  _READSESSIONPARAMS.fields_by_name['all_original'])
_READSESSIONPARAMS.fields_by_name['all_original'].containing_oneof = _READSESSIONPARAMS.oneofs_by_name['read_rule']
_WRITESESSIONCLUSTERS.fields_by_name['clusters'].message_type = _CLUSTERINFO
_READSESSIONCLUSTERS.fields_by_name['clusters'].message_type = _CLUSTERINFO
_DISCOVERCLUSTERSREQUEST.fields_by_name['operation_params'].message_type = kikimr_dot_public_dot_api_dot_protos_dot_ydb__operation__pb2._OPERATIONPARAMS
_DISCOVERCLUSTERSREQUEST.fields_by_name['write_sessions'].message_type = _WRITESESSIONPARAMS
_DISCOVERCLUSTERSREQUEST.fields_by_name['read_sessions'].message_type = _READSESSIONPARAMS
_DISCOVERCLUSTERSRESPONSE.fields_by_name['operation'].message_type = kikimr_dot_public_dot_api_dot_protos_dot_ydb__operation__pb2._OPERATION
_DISCOVERCLUSTERSRESULT.fields_by_name['write_sessions_clusters'].message_type = _WRITESESSIONCLUSTERS
_DISCOVERCLUSTERSRESULT.fields_by_name['read_sessions_clusters'].message_type = _READSESSIONCLUSTERS
DESCRIPTOR.message_types_by_name['WriteSessionParams'] = _WRITESESSIONPARAMS
DESCRIPTOR.message_types_by_name['ClusterInfo'] = _CLUSTERINFO
DESCRIPTOR.message_types_by_name['ReadSessionParams'] = _READSESSIONPARAMS
DESCRIPTOR.message_types_by_name['WriteSessionClusters'] = _WRITESESSIONCLUSTERS
DESCRIPTOR.message_types_by_name['ReadSessionClusters'] = _READSESSIONCLUSTERS
DESCRIPTOR.message_types_by_name['DiscoverClustersRequest'] = _DISCOVERCLUSTERSREQUEST
DESCRIPTOR.message_types_by_name['DiscoverClustersResponse'] = _DISCOVERCLUSTERSRESPONSE
DESCRIPTOR.message_types_by_name['DiscoverClustersResult'] = _DISCOVERCLUSTERSRESULT
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

WriteSessionParams = _reflection.GeneratedProtocolMessageType('WriteSessionParams', (_message.Message,), dict(
  DESCRIPTOR = _WRITESESSIONPARAMS,
  __module__ = 'kikimr.public.api.protos.ydb_persqueue_cluster_discovery_pb2'
  # @@protoc_insertion_point(class_scope:Ydb.PersQueue.ClusterDiscovery.WriteSessionParams)
  ))
_sym_db.RegisterMessage(WriteSessionParams)

ClusterInfo = _reflection.GeneratedProtocolMessageType('ClusterInfo', (_message.Message,), dict(
  DESCRIPTOR = _CLUSTERINFO,
  __module__ = 'kikimr.public.api.protos.ydb_persqueue_cluster_discovery_pb2'
  # @@protoc_insertion_point(class_scope:Ydb.PersQueue.ClusterDiscovery.ClusterInfo)
  ))
_sym_db.RegisterMessage(ClusterInfo)

ReadSessionParams = _reflection.GeneratedProtocolMessageType('ReadSessionParams', (_message.Message,), dict(
  DESCRIPTOR = _READSESSIONPARAMS,
  __module__ = 'kikimr.public.api.protos.ydb_persqueue_cluster_discovery_pb2'
  # @@protoc_insertion_point(class_scope:Ydb.PersQueue.ClusterDiscovery.ReadSessionParams)
  ))
_sym_db.RegisterMessage(ReadSessionParams)

WriteSessionClusters = _reflection.GeneratedProtocolMessageType('WriteSessionClusters', (_message.Message,), dict(
  DESCRIPTOR = _WRITESESSIONCLUSTERS,
  __module__ = 'kikimr.public.api.protos.ydb_persqueue_cluster_discovery_pb2'
  # @@protoc_insertion_point(class_scope:Ydb.PersQueue.ClusterDiscovery.WriteSessionClusters)
  ))
_sym_db.RegisterMessage(WriteSessionClusters)

ReadSessionClusters = _reflection.GeneratedProtocolMessageType('ReadSessionClusters', (_message.Message,), dict(
  DESCRIPTOR = _READSESSIONCLUSTERS,
  __module__ = 'kikimr.public.api.protos.ydb_persqueue_cluster_discovery_pb2'
  # @@protoc_insertion_point(class_scope:Ydb.PersQueue.ClusterDiscovery.ReadSessionClusters)
  ))
_sym_db.RegisterMessage(ReadSessionClusters)

DiscoverClustersRequest = _reflection.GeneratedProtocolMessageType('DiscoverClustersRequest', (_message.Message,), dict(
  DESCRIPTOR = _DISCOVERCLUSTERSREQUEST,
  __module__ = 'kikimr.public.api.protos.ydb_persqueue_cluster_discovery_pb2'
  # @@protoc_insertion_point(class_scope:Ydb.PersQueue.ClusterDiscovery.DiscoverClustersRequest)
  ))
_sym_db.RegisterMessage(DiscoverClustersRequest)

DiscoverClustersResponse = _reflection.GeneratedProtocolMessageType('DiscoverClustersResponse', (_message.Message,), dict(
  DESCRIPTOR = _DISCOVERCLUSTERSRESPONSE,
  __module__ = 'kikimr.public.api.protos.ydb_persqueue_cluster_discovery_pb2'
  # @@protoc_insertion_point(class_scope:Ydb.PersQueue.ClusterDiscovery.DiscoverClustersResponse)
  ))
_sym_db.RegisterMessage(DiscoverClustersResponse)

DiscoverClustersResult = _reflection.GeneratedProtocolMessageType('DiscoverClustersResult', (_message.Message,), dict(
  DESCRIPTOR = _DISCOVERCLUSTERSRESULT,
  __module__ = 'kikimr.public.api.protos.ydb_persqueue_cluster_discovery_pb2'
  # @@protoc_insertion_point(class_scope:Ydb.PersQueue.ClusterDiscovery.DiscoverClustersResult)
  ))
_sym_db.RegisterMessage(DiscoverClustersResult)


DESCRIPTOR.has_options = True
DESCRIPTOR._options = _descriptor._ParseOptions(descriptor_pb2.FileOptions(), _b('\n*com.yandex.ydb.persqueue.cluster_discovery\370\001\001'))
# @@protoc_insertion_point(module_scope)
