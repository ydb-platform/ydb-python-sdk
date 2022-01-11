#!/usr/bin/env python
# -*- coding: utf-8 -*-

from kikimr.public.sdk.python.persqueue._protobuf import make_create_topic_request, make_remove_topic_request, make_alter_topic_request
import kikimr.public.api.grpc.draft.ydb_persqueue_v1_pb2_grpc as pqv1_server


class PQControlPlaneClient(object):
    def __init__(self, ydb_driver, legacy_style_topics=True):
        self.__legacy_path = legacy_style_topics
        self.__driver = ydb_driver

    def async_create_topic(self, path, partitions_count, retention_sec=129600, max_partition_write_speed=1048576):
        if self.__legacy_path:
            path = "/Root/PQ/" + path
        request = make_create_topic_request(path, partitions_count, retention_sec, max_partition_write_speed)
        return self.__driver.future(request, pqv1_server.PersQueueServiceStub, "CreateTopic")

    def create_topic(self, path, partitions_count, retention_sec=129600, max_partition_write_speed=1048576):
        if self.__legacy_path:
            path = "/Root/PQ/" + path
        request = make_create_topic_request(path, partitions_count, retention_sec, max_partition_write_speed)
        return self.__driver(request, pqv1_server.PersQueueServiceStub, "CreateTopic")

    def async_alter_topic(self, path, partitions_count, retention_sec=129600, max_partition_write_speed=1048576):
        if self.__legacy_path:
            path = "/Root/PQ/" + path
        request = make_alter_topic_request(path, partitions_count, retention_sec, max_partition_write_speed)
        return self.__driver.future(request, pqv1_server.PersQueueServiceStub, "AlterTopic")

    def alter_topic(self, path, partitions_count, retention_sec=129600, max_partition_write_speed=1048576):
        if self.__legacy_path:
            path = "/Root/PQ/" + path
        request = make_alter_topic_request(path, partitions_count, retention_sec, max_partition_write_speed)
        return self.__driver(request, pqv1_server.PersQueueServiceStub, "AlterTopic")

    def async_remove_topic(self, path):
        if self.__legacy_path:
            path = "/Root/PQ/" + path
        request = make_remove_topic_request(path)
        return self.__driver.future(request, pqv1_server.PersQueueServiceStub, "DropTopic")

    def remove_topic(self, path):
        if self.__legacy_path:
            path = "/Root/PQ/" + path
        request = make_remove_topic_request(path)
        return self.__driver(request, pqv1_server.PersQueueServiceStub, "DropTopic")
