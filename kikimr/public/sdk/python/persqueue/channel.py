#!/usr/bin/env python
# -*- coding: utf-8 -*-
import grpc
import logging
from concurrent import futures

import kikimr.core.protos.grpc_pb2_grpc as grpc_server
import kikimr.public.api.grpc.draft.persqueue_pb2_grpc as pq_server
from kikimr.public.sdk.python.persqueue import errors
from kikimr.core.protos import msgbus_pb2 as msgbus
import threading


_MAX_MESSAGE_SIZE = 64 * 10 ** 6
_STATUS_OK = 1
_CONNECT_OPTIONS = [
    ('grpc.max_receive_message_length', _MAX_MESSAGE_SIZE),
    ('grpc.max_send_message_length', _MAX_MESSAGE_SIZE),
    ('grpc.primary_user_agent', 'ChannelOpsHandler')
]


logger = logging.getLogger(__name__)


def _is_choose_proxy_success(response):
    return response.Status == _STATUS_OK


def _on_reply(future, grpc_future):
    try:
        future.set_result(grpc_future.result())
    except grpc.RpcError as e:
        future.set_exception(errors.ConnectionError(str(e)))

    except Exception as e:
        future.set_exception(e)


class ChannelOpsHandler(object):
    def __init__(self, host, port):
        self._base_host = host
        self._base_port = port
        self._channel = None
        self._pq_stub = None
        self._stub = None
        self.proxy_cookie = None
        self.__conn_thread = None

    def _instantiate_channel(self, host, port, timeout=2):
        try:
            self._channel = grpc.insecure_channel('%s:%s' % (host, port), options=_CONNECT_OPTIONS)
            self._pq_stub = pq_server.PersQueueServiceStub(self._channel)
            self._stub = grpc_server.TGRpcServerStub(self._channel)
            ready_future = grpc.channel_ready_future(self._channel)
            ready_future.result(timeout=timeout)
        except grpc.RpcError as e:
            self.close(False)
            raise errors.ConnectionError(e)

        except Exception:
            self.close(False)

            raise

    def close(self, wait_shutdown=True):
        for item in (self._stub, self._pq_stub, self._channel):
            try:
                del item
            except AttributeError:
                pass
        if self.__conn_thread is not None and wait_shutdown:
            self.__conn_thread.join()

    def invoke(self, request, method, pq_stub=True):
        try:
            stub = self._pq_stub if pq_stub else self._stub
            stub_method = getattr(stub, method)
            response = stub_method(request)
        except grpc.RpcError as e:
            raise errors.ConnectionError(str(e))

        return response

    def connect(self):
        try:
            self._instantiate_channel(self._base_host, self._base_port)

            response = self.invoke(msgbus.TChooseProxyRequest(), 'ChooseProxy', pq_stub=False)

            if not _is_choose_proxy_success(response):
                raise errors.ConnectionError("Unable to choose proxy")

            self.close(False)

            self._instantiate_channel(response.ProxyName, self._base_port)
            self.proxy_cookie = response.ProxyCookie

        except grpc.RpcError as e:
            self.close(False)

            raise errors.ConnectionError(e)
        except Exception:
            self.close(False)
            raise

    def async_connect(self):
        assert self.__conn_thread is None

        def _do_conn(f):
            try:
                self.connect()
                f.set_result(None)
            except Exception as e:
                logger.exception("Connect failed with exception")
                f.set_exception(e)

        f = futures.Future()
        self.__conn_thread = threading.Thread(target=_do_conn, args=(f, ), name='_conn_thread')
        self.__conn_thread.setDaemon(True)
        self.__conn_thread.start()
        return f
