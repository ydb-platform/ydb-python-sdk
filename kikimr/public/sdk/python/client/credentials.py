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
    @abc.abstractproperty
    def expired(self):
        pass

    @abc.abstractmethod
    def auth_metadata(self):
        """
        :return: An iterable with auth metadata
        """
        pass


class AuthTokenCredentials(Credentials):
    def __init__(self, token):
        self._token = token

    @property
    def expired(self):
        return False

    def auth_metadata(self):
        return [
            (YDB_AUTH_TICKET_HEADER, self._token)
        ]
