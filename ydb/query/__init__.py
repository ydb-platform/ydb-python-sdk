__all__ = [
    "BaseQueryTxMode",
    "QueryExplainResultFormat",
    "QueryOnlineReadOnly",
    "QuerySerializableReadWrite",
    "QuerySnapshotReadOnly",
    "QuerySnapshotReadWrite",
    "QueryStaleReadOnly",
    "QuerySessionPool",
    "QueryClientSettings",
    "QuerySession",
    "QueryStatsMode",
    "QueryTxContext",
    "QuerySchemaInclusionMode",
    "QueryResultSetFormat",
    "ArrowCompressionCodecType",
    "ArrowCompressionCodec",
    "ArrowFormatSettings",
    "ArrowFormatMeta",
]

import logging
from typing import TYPE_CHECKING, Optional

from .._grpc.grpcwrapper.ydb_query_public_types import (
    ArrowCompressionCodec,
    ArrowCompressionCodecType,
    ArrowFormatMeta,
    ArrowFormatSettings,
    BaseQueryTxMode,
    QueryOnlineReadOnly,
    QuerySerializableReadWrite,
    QuerySnapshotReadOnly,
    QuerySnapshotReadWrite,
    QueryStaleReadOnly,
)
from .base import (
    QueryClientSettings,
    QueryExplainResultFormat,
    QueryResultSetFormat,
    QuerySchemaInclusionMode,
    QueryStatsMode,
)
from .pool import QuerySessionPool
from .session import QuerySession
from .transaction import QueryTxContext

if TYPE_CHECKING:
    from ..driver import Driver as SyncDriver

logger = logging.getLogger(__name__)


class QueryClientSync:
    _driver: "SyncDriver"

    def __init__(self, driver: "SyncDriver", query_client_settings: Optional[QueryClientSettings] = None):
        self._driver = driver
        self._settings = query_client_settings

    def session(self) -> QuerySession:
        return QuerySession(self._driver, self._settings)
