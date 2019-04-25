# -*- coding: utf-8 -*-


class BaseRequestSettings(object):
    __slots__ = ('trace_id', 'timeout')

    def __init__(self):
        """
        Request settings to be used for RPC execution
        """
        self.trace_id = None
        self.timeout = None

    def with_trace_id(self, trace_id):
        """
        Includes trace id for RPC headers
        :param trace_id: A trace id string
        :return: The self instance
        """
        self.trace_id = trace_id
        return self

    def with_timeout(self, timeout):
        """
        Client-side timeout to complete request.
        Since YDB doesn't support request cancellation at this moment, this feature should be
        used properly to avoid server overload.
        :param timeout: timeout value in seconds
        :return: The self instance
        """
        self.timeout = timeout
        return self
