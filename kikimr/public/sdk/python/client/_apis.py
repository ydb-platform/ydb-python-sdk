# -*- coding: utf-8 -*-
from kikimr.public.api.grpc import ydb_cms_v1_pb2_grpc, ydb_discovery_v1_pb2_grpc, ydb_scheme_v1_pb2_grpc, ydb_table_v1_pb2_grpc
from kikimr.public.api.protos import ydb_status_codes_pb2, ydb_discovery_pb2, ydb_scheme_pb2, ydb_table_pb2, ydb_value_pb2
from yql.public.types import yql_types_pb2


StatusIds = ydb_status_codes_pb2.StatusIds
yql_types = yql_types_pb2
ydb_value = ydb_value_pb2
ydb_scheme = ydb_scheme_pb2
ydb_table = ydb_table_pb2
ydb_discovery = ydb_discovery_pb2


class CmsService(object):
    Stub = ydb_cms_v1_pb2_grpc.CmsServiceStub


class DiscoveryService(object):
    Stub = ydb_discovery_v1_pb2_grpc.DiscoveryServiceStub
    ListEndpoints = 'ListEndpoints'


class SchemeService(object):
    Stub = ydb_scheme_v1_pb2_grpc.SchemeServiceStub
    MakeDirectory = 'MakeDirectory'
    RemoveDirectory = 'RemoveDirectory'
    ListDirectory = 'ListDirectory'
    DescribePath = 'DescribePath'
    ModifyPermissions = 'ModifyPermissions'


class TableService(object):
    Stub = ydb_table_v1_pb2_grpc.TableServiceStub

    CreateTable = 'CreateTable'
    DropTable = 'DropTable'
    AlterTable = 'AlterTable'
    CopyTable = 'CopyTable'
    DescribeTable = 'DescribeTable'
    CreateSession = 'CreateSession'
    DeleteSession = 'DeleteSession'
    ExecuteSchemeQuery = 'ExecuteSchemeQuery'
    PrepareDataQuery = 'PrepareDataQuery'
    ExecuteDataQuery = 'ExecuteDataQuery'
    BeginTransaction = 'BeginTransaction'
    CommitTransaction = 'CommitTransaction'
    RollbackTransaction = 'RollbackTransaction'
    KeepAlive = 'KeepAlive'
    StreamReadTable = 'StreamReadTable'
