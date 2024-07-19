from .base import (
    IQueryClient,
    SupportedDriverType,
    QueryClientSettings,
)

from .session import QuerySessionSync

from .._grpc.grpcwrapper.ydb_query_public_types import (
    QueryOnlineReadOnly,
    QuerySerializableReadWrite,
    QuerySnapshotReadOnly,
    QueryStaleReadOnly,
)

from .pool import QuerySessionPool


class QueryClientSync(IQueryClient):
    def __init__(self, driver: SupportedDriverType, query_client_settings: QueryClientSettings = None):
        self._driver = driver
        self._settings = query_client_settings

    def session(self) -> QuerySessionSync:
        return QuerySessionSync(self._driver, self._settings)
