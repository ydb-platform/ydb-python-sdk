#!/usr/bin/env python
# -*- coding: utf-8 -*-
import abc

import six

from kikimr.public.sdk.python.persqueue import errors
from kikimr.public.api.protos.draft import persqueue_pb2


@six.add_metaclass(abc.ABCMeta)
class CredentialsProvider(object):
    def __init__(self):
        self._cached_proto = persqueue_pb2.Credentials()

    @abc.abstractmethod
    def _build_protobuf(self):
        pass

    @property
    def protobuf(self):
        self._build_protobuf()
        return self._cached_proto


class OAuthTokenCredentialsProvider(CredentialsProvider):
    def __init__(self, oauth_token):
        super(OAuthTokenCredentialsProvider, self).__init__()
        self.__token = oauth_token

    def _build_protobuf(self):
        self._cached_proto.oauth_token = self.__token


class TVMCredentialsProvider(CredentialsProvider):
    def __init__(self, tvm_client, destination_client_id=None, destination_alias=None):
        super(TVMCredentialsProvider, self).__init__()
        self.__tvm_client = tvm_client

        if hasattr(tvm_client, 'get_service_ticket_for'):
            if destination_alias is None:
                raise errors.TVMError("destination_alias must be specified for this TVMClient type")
            self.__client_id = destination_alias
            self.__client_type_new = True
        elif hasattr(tvm_client, 'get_service_tickets'):
            if destination_client_id is None:
                raise errors.TVMError("destination_client_id must be specified for this TVMClient type")
            self.__client_id = str(destination_client_id)
            self.__client_type_new = False
        else:
            raise errors.TVMError("Unrecognized TVM client type")

    def __get_service_tickets(self):
        tickets = self.__tvm_client.get_service_tickets(self.__client_id)
        if not tickets or self.__client_id not in tickets:
            raise errors.TVMError("Unable to get TVM ticket")
        return tickets[self.__client_id]

    def __get_service_ticket_for(self):
        ticket = self.__tvm_client.get_service_ticket_for(self.__client_id)
        if not ticket:
            raise errors.TVMError("Unable to get TVM ticket")
        return ticket

    def _build_protobuf(self):
        if self.__client_type_new:
            self._cached_proto.tvm_service_ticket = str(self.__get_service_ticket_for()).encode('utf8')
        else:
            self._cached_proto.tvm_service_ticket = str(self.__get_service_tickets()).encode('utf8')
