#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time

import enum

from kikimr.public.api.protos.draft.persqueue_pb2 import WriteRequest, ReadRequest
from kikimr.public.api.protos.draft.persqueue_pb2 import WriteResponse, ReadResponse
import kikimr.public.api.protos.draft.persqueue_error_codes_pb2 as pq_err_codes


class RequestTypes(enum.Enum):
    WriteRequest = 'WriteRequest'
    ReadRequest = 'ReadRequest'
    CommitRequest = 'CommitRequest'
    LockedAck = 'LockedAck'
    NextEventRequest = 'NextEvent'


READ_STREAM_METHOD = 'ReadSession'
WRITE_STREAM_METHOD = 'WriteSession'
CHOOSE_PROXY_METHOD = 'ChooseProxy'


response_class_mapping = {
    WRITE_STREAM_METHOD: WriteResponse,
    READ_STREAM_METHOD: ReadResponse,
}


def base_write_request(credentials_proto=None):
    request = WriteRequest()
    if credentials_proto is not None:
        request.credentials.MergeFrom(credentials_proto)
    return request


def write_init_request(configurator, proxy_cookie, credentials_proto=None):
    """
        message TInit {
            string Topic = 1;
            bytes SourceId = 2;
            // if true then waits completion of old session for this sourceId
            bytes Ip = 6;
            TMap ExtraFields = 7;

            uint64 ProxyCookie = 8; //cookie provided by ChooseProxy request

            string Version = 999; //must be filled by client lib
        }
    """
    request = base_write_request(credentials_proto)
    request.init.topic = configurator.topic
    request.init.source_id = configurator.source_id
    request.init.proxy_cookie = proxy_cookie

    if credentials_proto is not None:
        request.credentials.MergeFrom(credentials_proto)

    if configurator.partition_group is not None:
        request.init.partition_group = configurator.partition_group

    return request


def write_request(seq_no, data, create_time_ms=None, codec=None, credentials_proto=None):
    """
    message TData {
        uint64 SeqNo = 1;
        bytes Data = 2;
        uint64 CreateTimeMS = 3; //timestamp in ms
        ECodec Codec = 4;
    }
    """
    request = base_write_request(credentials_proto)
    request.data.seq_no = seq_no
    request.data.data = data
    if create_time_ms is not None:
        request.data.create_time_ms = create_time_ms
    else:
        request.data.create_time_ms = int(time.time() * 1000)
    if codec is not None:
        request.data.codec = codec
    if credentials_proto is not None:
        request.credentials.MergeFrom(credentials_proto)
    return request


def base_read_request(credentials_proto=None):
    request = ReadRequest()
    if credentials_proto is not None:
        request.credentials.MergeFrom(credentials_proto)
    return request


def read_init_request(configurator, proxy_cookie, credentials_proto=None):
    """
    message TInit {
        repeated string Topics = 1;
        bool ReadOnlyLocal = 2; // if DCs empty and ReadOnlyLocal=false - read all dcs
        string ClientId = 4;
        bool ClientsideLocksAllowed = 5; //if true then partitions Lock signal will be sended in PersQueueLockSession,
                                         //and reads from partitions will began only after Locked signal from client via PersQueueLockSession

        uint64 ProxyCookie = 6; //cookie provided by ChooseProxy request
        string Ticket = 7; // TVM ticket, if set check ACL

        bool BalancePartitionRightNow = 8; //if set then do not wait for commits from client on data from partition in case of balancing

        string Version = 999; //must be filled by client lib
    }
    """
    request = base_read_request(credentials_proto)
    request.init.proxy_cookie = proxy_cookie
    request.init.client_id = configurator.client_id
    request.init.topics.extend(configurator.topics)
    if configurator.read_only_local is not None:
        request.init.read_only_local = configurator.read_only_local
    if configurator.use_client_locks is not None:
        # noinspection SpellCheckingInspection
        request.init.clientside_locks_allowed = configurator.use_client_locks
    if configurator.balance_partition_now is not None:
        request.init.balance_partition_right_now = configurator.balance_partition_now
    if configurator.partition_groups is not None:
        request.init.partition_groups.extend(configurator.partition_groups)
    return request


def read_request(configurator, credentials_proto=None):
    """
    message TRead {
        uint32 MaxCount = 1;
        uint32 MaxSize = 2;
        uint32 PartitionsAtOnce = 3; //0 means not matters
        uint32 MaxTimeLagMs = 5;
    }
    """
    request = base_read_request(credentials_proto)
    if configurator.max_count is not None:
        request.read.max_count = configurator.max_count
    if configurator.max_size is not None:
        request.read.max_size = configurator.max_size
    if configurator.partitions_at_once is not None:
        request.read.partitions_at_once = configurator.partitions_at_once
    else:
        request.read.partitions_at_once = 0
    if configurator.max_time_lag_ms is not None:
        request.read.max_time_lag_ms = configurator.max_time_lag_ms
    return request


def commit_request(cookies, credentials_proto=None):
    request = base_read_request(credentials_proto)
    request.commit.cookie.extend(cookies)

    return request


def locked_request(
        topic, partition, generation, read_offset=None, commit_offset=None,
        verify_read_offset=None, credentials_proto=None
):
    """
    message StartRead {
        string Topic = 1;
        uint32 Partition = 2;
        uint64 ReadOffset = 3; //skip upto this position; if committed position is bigger, then do nothing
        bool VerifyReadOffset = 4; //if true then check that committed position is <= ReadOffset; otherwise it means error in client logic
    }
    :return:
    """

    request = base_read_request(credentials_proto)
    request.start_read.topic = topic
    request.start_read.partition = partition
    request.start_read.generation = generation
    if read_offset is not None:
        request.start_read.read_offset = read_offset
    if commit_offset is not None:
        request.start_read.commit_offset = read_offset
    if verify_read_offset is not None:
        request.start_read.verify_read_offset = verify_read_offset
    return request


def error_response(request_type, error_code=pq_err_codes.ERROR, description=""):
    # noinspection PyCallingNonCallable
    response = response_class_mapping[request_type]()
    response.error.code = error_code
    response.error.description = description
    return response
