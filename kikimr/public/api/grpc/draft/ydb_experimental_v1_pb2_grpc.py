# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from ydb.public.api.protos import ydb_experimental_pb2 as kikimr_dot_public_dot_api_dot_protos_dot_ydb__experimental__pb2


class ExperimentalServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.ExecuteStreamQuery = channel.unary_stream(
                '/Ydb.Experimental.V1.ExperimentalService/ExecuteStreamQuery',
                request_serializer=kikimr_dot_public_dot_api_dot_protos_dot_ydb__experimental__pb2.ExecuteStreamQueryRequest.SerializeToString,
                response_deserializer=kikimr_dot_public_dot_api_dot_protos_dot_ydb__experimental__pb2.ExecuteStreamQueryResponse.FromString,
                )


class ExperimentalServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def ExecuteStreamQuery(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_ExperimentalServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'ExecuteStreamQuery': grpc.unary_stream_rpc_method_handler(
                    servicer.ExecuteStreamQuery,
                    request_deserializer=kikimr_dot_public_dot_api_dot_protos_dot_ydb__experimental__pb2.ExecuteStreamQueryRequest.FromString,
                    response_serializer=kikimr_dot_public_dot_api_dot_protos_dot_ydb__experimental__pb2.ExecuteStreamQueryResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'Ydb.Experimental.V1.ExperimentalService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class ExperimentalService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def ExecuteStreamQuery(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_stream(request, target, '/Ydb.Experimental.V1.ExperimentalService/ExecuteStreamQuery',
            kikimr_dot_public_dot_api_dot_protos_dot_ydb__experimental__pb2.ExecuteStreamQueryRequest.SerializeToString,
            kikimr_dot_public_dot_api_dot_protos_dot_ydb__experimental__pb2.ExecuteStreamQueryResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
