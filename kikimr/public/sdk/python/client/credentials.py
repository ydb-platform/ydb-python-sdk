# -*- coding: utf-8 -*-
import abc
import six

YDB_AUTH_TICKET_HEADER = "x-ydb-auth-ticket"


@six.add_metaclass(abc.ABCMeta)
class AbstractCredentials(object):
    """
    An abstract class that provides auth metadata
    """


@six.add_metaclass(abc.ABCMeta)
class Credentials(object):
    @abc.abstractmethod
    def auth_metadata(self):
        """
        :return: An iterable with auth metadata
        """
        pass


class AnonymousCredentials(Credentials):
    @staticmethod
    def auth_metadata():
        return []


class AuthTokenCredentials(Credentials):
    def __init__(self, token):
        self._token = token

    def auth_metadata(self):
        return [
            (YDB_AUTH_TICKET_HEADER, self._token)
        ]


class AccessTokenCredentials(Credentials):
    def __init__(self, token):
        self._token = token

    def auth_metadata(self):
        return [
            (YDB_AUTH_TICKET_HEADER, self._token)
        ]
