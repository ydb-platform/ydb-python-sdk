#!/usr/bin/env python
# -*- coding: utf-8 -*-
import enum


class ConnectionError(Exception):
    pass


class SessionClosedException(RuntimeError):
    """
    Attempt to send a request when Grpc session was already closed, but Producer/Consumer didn't yet shutdown

    """
    pass


class ActorTerminatedException(RuntimeError):
    """
    Attempt to send a request to already terminated Producer/Consumer

    """
    pass


class ActorNotReadyException(RuntimeError):
    """
    Attempt to send request to not started Producer/Consumer or to create Producer/Consumer from not started API
    """
    pass


class TVMError(RuntimeError):
    """
    Tvm operation error
    """
    pass


class SessionFailureResult(object):
    def __init__(self, reason, description=None):
        self.__reason = reason
        self.__description = description

    @property
    def reason(self):
        return self.__reason

    @property
    def description(self):
        return self.__description

    def __str__(self):
        return "Session closed. Reason: {}, Description: {}".format(self.reason, self.description)


class SessionDeathReason(enum.Enum):
    InitFailed = "Init failed"
    FailedWithError = "Failed with error"
    ClosedUnexpectedly = "Closed unexpectedly"
    HostConnectionFailed = "Connection Failed"
    KilledByOwner = "Killed by owner"
