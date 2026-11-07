import pytest
from contextlib import suppress

import ydb.iam


def test_tx_commit(driver_sync, database):
    session = driver_sync.table_client.session().create()
    prepared = session.prepare(
        "DECLARE $param as Int32;\n SELECT $param as value",
    )

    tx = session.transaction()
    tx.execute(prepared, {"$param": 2})
    tx.commit()
    tx.commit()


def test_tx_rollback(driver_sync, database):
    session = driver_sync.table_client.session().create()
    prepared = session.prepare(
        "DECLARE $param as Int32;\n SELECT $param as value",
    )

    tx = session.transaction()
    tx.execute(prepared, {"$param": 2})
    tx.rollback()
    tx.rollback()


def test_tx_begin(driver_sync, database):
    session = driver_sync.table_client.session().create()
    session.create()

    tx = session.transaction()
    tx.begin()
    tx.begin()
    tx.rollback()


def test_tx_snapshot_ro(driver_sync, database):
    session = driver_sync.table_client.session().create()
    description = (
        ydb.TableDescription()
        .with_primary_keys("key")
        .with_columns(
            ydb.Column("key", ydb.OptionalType(ydb.PrimitiveType.Uint64)),
            ydb.Column("value", ydb.OptionalType(ydb.PrimitiveType.Uint64)),
        )
    )
    tb_name = f"{database}/test"
    with suppress(ydb.issues.SchemeError):
        session.drop_table(tb_name)
    session.create_table(tb_name, description)
    session.transaction(ydb.SerializableReadWrite()).execute(
        """INSERT INTO `test` (`key`, `value`) VALUES (1, 1), (2, 2)""",
        commit_tx=True,
    )

    ro_tx = session.transaction(tx_mode=ydb.SnapshotReadOnly())
    data1 = ro_tx.execute("SELECT value FROM `test` WHERE key = 1")

    session.transaction(ydb.SerializableReadWrite()).execute("UPDATE `test` SET value = value + 1", commit_tx=True)

    data2 = ro_tx.execute("SELECT value FROM `test` WHERE key = 1")
    assert data1[0].rows == data2[0].rows == [{"value": 1}]

    ro_tx.commit()

    ro_tx = session.transaction(tx_mode=ydb.SnapshotReadOnly())
    with pytest.raises(ydb.issues.GenericError) as exc_info:
        ro_tx.execute("UPDATE `test` SET value = value + 1")
    assert "read only transaction" in exc_info.value.message

    data = session.transaction(tx_mode=ydb.SnapshotReadOnly()).execute(
        "SELECT value FROM `test` WHERE key = 1",
        commit_tx=True,
    )
    assert data[0].rows == [{"value": 2}]

    with suppress(ydb.issues.SchemeError):
        session.drop_table(tb_name)


def test_split_transactions_deny_split(driver_sync, table_name):
    with ydb.SessionPool(driver_sync, 1) as pool:

        def check_transaction(s: ydb.table.Session):
            with s.transaction(allow_split_transactions=False) as tx:
                tx.execute("INSERT INTO %s (id) VALUES (1)" % table_name)
                tx.commit()

                with pytest.raises(RuntimeError):
                    tx.execute("INSERT INTO %s (id) VALUES (2)" % table_name)

                tx.commit()

            with s.transaction() as tx:
                rs = tx.execute("SELECT COUNT(*) as cnt FROM %s" % table_name)
                assert rs[0].rows[0].cnt == 1

        pool.retry_operation_sync(check_transaction)


def test_split_transactions_deny_split_flag_commit(driver_sync, table_name):
    with ydb.SessionPool(driver_sync, 1) as pool:

        def check_transaction(s: ydb.table.Session):
            with s.transaction(allow_split_transactions=False) as tx:
                tx.execute("INSERT INTO %s (id) VALUES (1)" % table_name, commit_tx=True)

                with pytest.raises(RuntimeError):
                    tx.execute("INSERT INTO %s (id) VALUES (2)" % table_name)

                tx.commit()

            with s.transaction() as tx:
                rs = tx.execute("SELECT COUNT(*) as cnt FROM %s" % table_name)
                assert rs[0].rows[0].cnt == 1

        pool.retry_operation_sync(check_transaction)


def test_split_transactions_allow_split(driver_sync, table_name):
    with ydb.SessionPool(driver_sync, 1) as pool:

        def check_transaction(s: ydb.table.Session):
            with s.transaction(allow_split_transactions=True) as tx:
                tx.execute("INSERT INTO %s (id) VALUES (1)" % table_name)
                tx.commit()

                tx.execute("INSERT INTO %s (id) VALUES (2)" % table_name)
                tx.commit()

            with s.transaction() as tx:
                rs = tx.execute("SELECT COUNT(*) as cnt FROM %s" % table_name)
                assert rs[0].rows[0].cnt == 2

        pool.retry_operation_sync(check_transaction)


def test_split_transactions_default(driver_sync, table_name):
    with ydb.SessionPool(driver_sync, 1) as pool:

        def check_transaction(s: ydb.table.Session):
            with s.transaction() as tx:
                tx.execute("INSERT INTO %s (id) VALUES (1)" % table_name)
                tx.commit()

                with pytest.raises(RuntimeError):
                    tx.execute("INSERT INTO %s (id) VALUES (2)" % table_name)

                tx.commit()

            with s.transaction() as tx:
                rs = tx.execute("SELECT COUNT(*) as cnt FROM %s" % table_name)
                assert rs[0].rows[0].cnt == 1

        pool.retry_operation_sync(check_transaction)


def test_truncated_response(driver_sync, table_name, table_path):
    column_types = ydb.BulkUpsertColumns().add_column("id", ydb.PrimitiveType.Int64)

    rows = []

    rows_count = 1100
    for i in range(rows_count):
        rows.append({"id": i})

    driver_sync.table_client.bulk_upsert(table_path, rows, column_types)

    table_client = driver_sync.table_client  # default table client with driver's settings
    s = table_client.session()
    s.create()
    t = s.transaction()
    with pytest.raises(ydb.TruncatedResponseError):
        t.execute("SELECT * FROM %s" % table_name)


def test_truncated_response_allow(driver_sync, table_name, table_path):
    column_types = ydb.BulkUpsertColumns().add_column("id", ydb.PrimitiveType.Int64)

    rows = []

    rows_count = 1100
    for i in range(rows_count):
        rows.append({"id": i})

    driver_sync.table_client.bulk_upsert(table_path, rows, column_types)

    table_client = ydb.TableClient(driver_sync, ydb.TableClientSettings().with_allow_truncated_result(True))
    s = table_client.session()
    s.create()
    t = s.transaction()
    result = t.execute("SELECT * FROM %s" % table_name)
    assert result[0].truncated
    assert len(result[0].rows) == 1000


class TestSloControlData:
    def test_sync_result_checked_after_retry_and_stream_errors_preserved(self, monkeypatch):
        from pathlib import Path
        from types import SimpleNamespace
        from unittest.mock import Mock

        monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "tests/slo/src"))
        from jobs.table_jobs import RequestParams, check_control_result, control_row, execute_query

        expected = control_row(2)
        session = Mock()
        active = False

        def retry(callee, retry_settings):
            nonlocal active
            active = True
            try:
                return ydb.retry_operation_sync(lambda: callee(session), retry_settings=retry_settings)
            finally:
                active = False

        def check(rows):
            assert not active
            check_control_result(rows, expected)

        pool = SimpleNamespace(retry_operation_sync=retry)
        metrics = Mock()
        errors = []
        request = RequestParams(
            pool, "query", {}, metrics, ("read",), None, ydb.RetrySettings(max_retries=1), check, errors.append
        )
        for changes in (
            {"payload_str": "generation:1"},
            {"payload_str": "corrupt"},
            {"payload_double": 2.5},
            {"payload_timestamp": 1},
            {"object_id": 1},
        ):
            session.transaction.return_value.execute.return_value = [SimpleNamespace(rows=[{**expected, **changes}])]
            with pytest.raises(RuntimeError):
                execute_query(request)
        for rows in ([], [expected, expected]):
            session.transaction.return_value.execute.return_value = [SimpleNamespace(rows=rows)]
            with pytest.raises(RuntimeError):
                execute_query(request)
        session.transaction.return_value.execute.side_effect = [
            ydb.Aborted("recovered"),
            [SimpleNamespace(rows=[dict(expected)])],
        ]
        assert execute_query(request) == [expected]
        assert metrics.stop.call_args.kwargs["attempts"] == 2
        terminal = ydb.BadRequest("original")

        class BrokenStream:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def __iter__(self):
                yield SimpleNamespace(rows=[expected])
                raise terminal

        session.transaction.return_value.execute.side_effect = None
        session.transaction.return_value.execute.return_value = BrokenStream()
        with pytest.raises(ydb.BadRequest) as failure:
            execute_query(request)
        assert failure.value is terminal
        assert errors[-1] is terminal

    @pytest.mark.asyncio
    async def test_async_result_checked_after_retry_and_stream_errors_preserved(self, monkeypatch):
        from pathlib import Path
        from types import SimpleNamespace
        from unittest.mock import AsyncMock, Mock

        monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "tests/slo/src"))
        from jobs.async_table_jobs import AsyncTableJobManager
        from jobs.table_jobs import check_control_result, control_row
        from ydb.retries import retry_operation_async

        expected = control_row(2)
        session = SimpleNamespace(execute=AsyncMock())
        manager = AsyncTableJobManager(Mock(), SimpleNamespace(), Mock(), "/local/load", 1000)
        active = False

        async def retry(callee, retry_settings):
            nonlocal active
            active = True
            try:
                return await retry_operation_async(lambda: callee(session), retry_settings=retry_settings)
            finally:
                active = False

        def check(rows):
            assert not active
            check_control_result(rows, expected)

        async def stream(rows, error=None):
            yield SimpleNamespace(rows=rows)
            if error is not None:
                raise error

        pool = SimpleNamespace(retry_operation_async=retry)
        settings = ydb.RetrySettings(max_retries=1)
        for rows in (
            [],
            [{**expected, "payload_str": "generation:1"}],
            [{**expected, "payload_str": "corrupt"}],
            [{**expected, "payload_double": 3.25}],
            [{**expected, "payload_timestamp": 1}],
            [{**expected, "object_id": 1}],
            [expected, expected],
        ):
            session.execute.return_value = stream(rows)
            with pytest.raises(RuntimeError):
                await manager._execute_query(pool, "query", {}, None, settings, ("read",), check)
        session.execute.side_effect = [ydb.Aborted("recovered"), stream([dict(expected)])]
        assert await manager._execute_query(pool, "query", {}, None, settings, ("read",), check) == [expected]
        terminal = ydb.BadRequest("original")
        session.execute.side_effect = None
        session.execute.return_value = stream([expected], terminal)
        with pytest.raises(ydb.BadRequest) as failure:
            await manager._execute_query(pool, "query", {}, None, settings, ("read",), check)
        assert failure.value is terminal

    def test_owned_control_tables_and_sequential_generations(self, monkeypatch):
        import threading
        from concurrent.futures import ThreadPoolExecutor
        from pathlib import Path
        from types import SimpleNamespace
        from unittest.mock import Mock

        monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "tests/slo/src"))
        from jobs import table_jobs

        barrier = threading.Barrier(2, timeout=5)
        tables = []
        checked = threading.local()

        def execute(request):
            if request.check_result_cb is None:
                generation = int(request.params["$payload_str"].split(":")[1])
                assert generation == getattr(checked, "generation", 0) + 1
                checked.expected = {key[1:]: value for key, value in request.params.items()}
                checked.expected["object_hash"] = 0
                if generation == 1:
                    barrier.wait()
            else:
                request.check_result_cb([dict(checked.expected)])
                checked.generation = int(checked.expected["payload_str"].split(":")[1])

        def scheme(query):
            tables.append(query.split("`")[1])

        session = Mock()
        session.execute_scheme.side_effect = scheme
        session.prepare.side_effect = lambda query: query
        pool = Mock()
        pool.__enter__ = Mock(return_value=pool)
        pool.__exit__ = Mock(return_value=False)
        pool.retry_operation_sync.side_effect = lambda callee: callee(session)
        monkeypatch.setattr(table_jobs.ydb, "SessionPool", lambda driver: pool)
        owners = [SimpleNamespace(hex=f"owner_{i}") for i in (1, 2)]
        monkeypatch.setattr(table_jobs, "uuid4", Mock(side_effect=owners))
        monkeypatch.setattr(table_jobs, "execute_query", execute)
        args = SimpleNamespace(read_timeout=10000, write_timeout=20000)

        def owner():
            manager = table_jobs.TableJobManager(Mock(), args, Mock(), "/local/load", 1000)
            manager.workload_type = "sync-table"
            manager._run_control_checks()
            assert checked.generation == 2

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(owner) for _ in range(2)]
            for future in futures:
                future.result(timeout=10)
        assert len(tables) == len(set(tables)) == 2
        assert sorted(call.args[0] for call in session.drop_table.call_args_list) == sorted(tables)
