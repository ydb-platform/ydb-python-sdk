import enum

from kikimr.public.sdk.python.client import settings_impl as s_impl
from kikimr.public.api.protos import ydb_export_pb2
from kikimr.public.api.grpc import ydb_export_v1_pb2_grpc
from kikimr.public.sdk.python.client import operation

_ExportToYt = 'ExportToYt'
_progresses = {}


@enum.unique
class ExportProgress(enum.IntEnum):
    UNSPECIFIED = 0
    PREPARING = 1
    TRANSFER_DATA = 2
    DONE = 3
    CANCELLATION = 4
    CANCELLED = 5


def _initialize_progresses():
    for key, value in ydb_export_pb2.ExportProgress.Progress.items():
        _progresses[value] = getattr(ExportProgress, key[len('PROGRESS_'):])


_initialize_progresses()


class ExportToYTOperation(operation.Operation):
    def __init__(self, rpc_state, response, driver):
        super(ExportToYTOperation, self).__init__(rpc_state, response, driver)
        metadata = ydb_export_pb2.ExportToYtMetadata()
        response.operation.metadata.Unpack(metadata)
        self.progress = _progresses.get(metadata.progress)

    def __str__(self):
        return "ExportToYTOperation<id: %s, progress: %s>" % (self.id, self.progress.name)

    def __repr__(self):
        return self.__str__()


class ExportToYTSettings(s_impl.BaseRequestSettings):
    def __init__(self):
        super(ExportToYTSettings, self).__init__()
        self.items = []
        self.number_of_retries = 0
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

    def with_item(self, item):
        """
        :param: A source & destination tuple to export.
        """
        self.items.append(item)
        return self

    def with_source_and_destination(self, source_path, destination_path):
        return self.with_item((source_path, destination_path))

    def with_number_of_retries(self, number_of_retries):
        self.number_of_retries = number_of_retries
        return self

    def with_items(self, *items):
        self.items.extend(items)
        return self


def _export_to_yt_request_factory(settings):
    request = ydb_export_pb2.ExportToYtRequest(
        settings=ydb_export_pb2.ExportToYtSettings(
            host=settings.host, token=settings.token
        )
    )

    if settings.number_of_retries > 0:
        request.settings.number_of_retries = settings.number_of_retries

    if settings.port:
        request.settings.port = settings.port

    for source_path, destination_path in settings.items:
        request.settings.items.add(
            source_path=source_path,
            destination_path=destination_path
        )

    return request


class ExportClient(object):
    def __init__(self, driver):
        self._driver = driver

    def export_to_yt(self, settings):
        return self._driver(
            _export_to_yt_request_factory(settings),
            ydb_export_v1_pb2_grpc.ExportServiceStub,
            _ExportToYt,
            ExportToYTOperation,
            settings,
            (
                self._driver,
            )
        )

    def async_export_to_yt(self, settings):
        return self._driver.future(
            _export_to_yt_request_factory(settings),
            ydb_export_v1_pb2_grpc.ExportServiceStub,
            _ExportToYt,
            ExportToYTOperation,
            settings,
            (
                self._driver,
            )
        )
