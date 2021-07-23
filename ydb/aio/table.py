import logging
from kikimr.public.sdk.python.client import issues

from kikimr.public.sdk.python.client.table import (
    BaseSession,
    BaseTableClient,
    _scan_query_request_factory,
    _wrap_scan_query_response,
    BaseTxContext
)
from . import _utilities
from kikimr.public.sdk.python.client import _apis, _session_impl
logger = logging.getLogger(__name__)


class Session(BaseSession):

    async def read_table(
        self, path, key_range=None, columns=(), ordered=False, row_limit=None, settings=None, use_snapshot=None
    ):
        request = _session_impl.read_table_request_factory(self._state, path, key_range, columns, ordered, row_limit,
                                                           use_snapshot=use_snapshot)
        stream_it = await self._driver(
            request, _apis.TableService.Stub, _apis.TableService.StreamReadTable, settings=settings
        )
        return _utilities.AsyncResponseIterator(stream_it, _session_impl.wrap_read_table_response)

    async def keep_alive(self, settings=None):
        return await super(Session, self).keep_alive(settings)

    async def create(self, settings=None):
        return await super(Session, self).create(settings)

    async def delete(self, settings=None):
        return await super(Session, self).delete(settings)

    async def execute_scheme(self, yql_text, settings=None):
        return await super(Session, self).execute_scheme(yql_text, settings)

    async def prepare(self, query, settings=None):
        return await super(Session, self).prepare(query, settings)

    async def explain(self, yql_text, settings=None):
        return await super(Session, self).explain(yql_text, settings)

    async def create_table(self, path, table_description, settings=None):
        return await super(Session, self).create_table(path, table_description, settings)

    async def drop_table(self, path, settings=None):
        return await super(Session, self).drop_table(path, settings)

    async def alter_table(
            self, path,
            add_columns=None, drop_columns=None,
            settings=None,
            alter_attributes=None,
            add_indexes=None, drop_indexes=None,
            set_ttl_settings=None, drop_ttl_settings=None,
            add_column_families=None, alter_column_families=None,
            alter_storage_settings=None,
            set_compaction_policy=None,
            alter_partitioning_settings=None,
            set_key_bloom_filter=None,
            set_read_replicas_settings=None):
        return await super(Session, self).alter_table(
            path,
            add_columns,
            drop_columns,
            settings,
            alter_attributes,
            add_indexes,
            drop_indexes,
            set_ttl_settings,
            drop_ttl_settings,
            add_column_families,
            alter_column_families,
            alter_storage_settings,
            set_compaction_policy,
            alter_partitioning_settings,
            set_key_bloom_filter,
            set_read_replicas_settings
        )

    def transaction(self, tx_mode=None):
        return TxContext(self._driver, self._state, self, tx_mode)

    async def describe_table(self, path, settings=None):
        return await super(Session, self).describe_table(path, settings)

    async def copy_table(self, source_path, destination_path, settings=None):
        return await super(Session, self).copy_table(source_path, destination_path, settings)

    async def copy_tables(self, source_destination_pairs, settings=None):
        return await super(Session, self).copy_tables(source_destination_pairs, settings)


class TableClient(BaseTableClient):

    def session(self):
        return Session(self._driver, self._table_client_settings)

    async def bulk_upsert(self, *args, **kwargs):
        return await super(TableClient, self).bulk_upsert(*args, **kwargs)

    async def scan_query(self, query, parameters=None, settings=None):
        request = _scan_query_request_factory(query, parameters, settings)
        response = await self._driver(
            request, _apis.TableService.Stub, _apis.TableService.StreamExecuteScanQuery, settings=settings
        )
        return _utilities.AsyncResponseIterator(
            response, lambda resp: _wrap_scan_query_response(resp, self._table_client_settings)
        )


class TxContext(BaseTxContext):
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._tx_state.tx_id is not None:
            # It's strictly recommended to close transactions directly
            # by using commit_tx=True flag while executing statement or by
            # .commit() or .rollback() methods, but here we trying to do best
            # effort to avoid useless open transactions
            logger.warning("Potentially leaked tx: %s", self._tx_state.tx_id)
            try:
                await self.rollback()
            except issues.Error:
                logger.warning(
                    "Failed to rollback leaked tx: %s", self._tx_state.tx_id)

            self._tx_state.tx_id = None

    async def execute(self, query, parameters=None, commit_tx=False, settings=None):
        return await super(TxContext, self).execute(query, parameters, commit_tx, settings)

    async def commit(self, settings=None):
        return await super(TxContext, self).commit(settings)

    async def rollback(self, settings=None):
        return await super(TxContext, self).rollback(settings)

    async def begin(self, settings=None):
        return await super(TxContext, self).begin(settings)
