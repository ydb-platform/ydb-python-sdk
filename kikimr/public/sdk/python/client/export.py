
from kikimr.public.sdk.python.client import settings_impl as s_impl
from kikimr.public.api.protos import ydb_export_pb2
from kikimr.public.api.grpc import ydb_export_v1_pb2_grpc
from kikimr.public.sdk.python.client import operation

_ExportToYt = 'ExportToYt'


class ExportToYTSettings(s_impl.BaseRequestSettings):
    def __init__(self):
        super(ExportToYTSettings, self).__init__()
        self.items = ()
        self.token = None
        self.host = None
        self.port = None

    def with_port(self, port):
        self.port = port
        return self

    def with_host(self, host):
        self.host = host
        return self

    def with_token(self, token):
        self.token = token
        return self

    def with_items(self, *items):
        """
        Src & dst pairs.
        :param items:
        :return:
        """

        self.items = items
        return self


def _export_to_yt_request_factory(settings):
    request = ydb_export_pb2.ExportToYtSettings(host=settings.host, token=settings.token)
    if settings.port:
        request.port = settings.port
    for source_path, destination_path in settings.items:
        request.items.add(source_path=source_path, destination_path=destination_path)
    return request


class ExportClient(object):
    def __init__(self, driver):
        self.driver = driver

    def async_export_to_yt(self, settings):
        """
        Experimental call. Don't use until api is defined as stable.
        :param settings: a ExportToYTSettings instance
        :return: a future of operation instance.
        """
        return self.driver.future(
            _export_to_yt_request_factory(settings),
            ydb_export_v1_pb2_grpc.ExportServiceStub,
            _ExportToYt,
            operation.Operation,
        )
