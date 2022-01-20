#!/usr/bin/env python
# -*- coding: utf-8 -*-
import abc

import six

import kikimr.public.sdk.python.iam.auth as iam_auth
from ydb.credentials import YDB_AUTH_TICKET_HEADER

from kikimr.public.sdk.python.persqueue import errors
from ydb.public.api.protos.draft import persqueue_common_pb2


@six.add_metaclass(abc.ABCMeta)
class CredentialsProvider(object):
    def __init__(self):
        self._cached_proto = persqueue_common_pb2.Credentials()

    @abc.abstractmethod
    def _build_protobuf(self):
        pass

    @abc.abstractmethod
    def auth_metadata(self):
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
        if isinstance(self.__token, str):
            self._cached_proto.oauth_token = self.__token.encode('utf8')
        else:
            self._cached_proto.oauth_token = self.__token

    def auth_metadata(self):
        return [
            (
                YDB_AUTH_TICKET_HEADER, self.__token
            )
        ]


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

    def __get_service_ticket_from_old_client(self):
        tickets = self.__tvm_client.get_service_tickets(self.__client_id)
        if not tickets or self.__client_id not in tickets:
            raise errors.TVMError("Unable to get TVM ticket")
        return tickets[self.__client_id]

    def __get_service_ticket_from_new_client(self):
        ticket = self.__tvm_client.get_service_ticket_for(self.__client_id)
        if not ticket:
            raise errors.TVMError("Unable to get TVM ticket")
        return ticket

    def __get_service_ticket(self):
        if self.__client_type_new:
            ticket = self.__get_service_ticket_from_new_client()
        else:
            ticket = self.__get_service_ticket_from_old_client()

        return str(ticket)

    def _build_protobuf(self):
        self._cached_proto.tvm_service_ticket = self.__get_service_ticket().encode('utf8')

    def auth_metadata(self):

        return [
            (
                YDB_AUTH_TICKET_HEADER, self.__get_service_ticket()
            )
        ]


class IamServiceAccountCredentialsProvider(CredentialsProvider):
    def __init__(self, key_file, iam_endpoint=None, iam_channel_credentials=None):
        """
        :param key_file: path to IAM key file
        :param iam_endpoint: specific user-defined endpoint to access IAM service
        :param iam_channel_credentials: params for channel credentials. Dict.
        See grpc.ssl_channel_credentials for supported parameters
        """
        super(IamServiceAccountCredentialsProvider, self).__init__()
        self.__provider = iam_auth.ServiceAccountCredentials.from_file(key_file, iam_endpoint, iam_channel_credentials)

    def _build_protobuf(self):
        ticket = self.__provider.auth_metadata()[0][1]

        if isinstance(ticket, str):
            self._cached_proto.oauth_token = ticket.encode('utf8')
        else:
            self._cached_proto.oauth_token = ticket

    def auth_metadata(self):
        return self.__provider.auth_metadata()


class IamMetadataUrlCredentialsProvider(CredentialsProvider):
    def __init__(self, metadata_url=None):
        super(IamMetadataUrlCredentialsProvider, self).__init__()
        if metadata_url is not None:
            self.__provider = iam_auth.MetadataUrlCredentials(metadata_url)
        else:
            self.__provider = iam_auth.MetadataUrlCredentials()

    def _build_protobuf(self):
        ticket = self.__provider.auth_metadata()[0][1]

        if isinstance(ticket, str):
            self._cached_proto.oauth_token = ticket.encode('utf8')
        else:
            self._cached_proto.oauth_token = ticket

    def auth_metadata(self):
        return self.__provider.auth_metadata()
