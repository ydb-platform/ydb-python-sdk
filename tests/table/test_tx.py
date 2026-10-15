import asyncio
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import ydb.aio
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


def _rmw_manager(rmw, store):
    args = SimpleNamespace(
        write_timeout=20000, read_timeout=10000, counter_count=2, time=3600, write_threads=4, report_period=1000
    )
    return rmw.AsyncRmwJobManager(store, args, Mock(), "/local/owned_counters", "/local/owned_ledger")


class RmwStore:
    # A serializable transaction seam, not evidence of real SDK/server recovery.
    def __init__(self):
        self.counters = {key: dict(counter_id=key, value=0, version=0) for key in range(2)}
        self.ledger = {}
        self.revision = 0
        self.commits = 0
        self.before_commit = None
        self.after_commit = None
        self.on_counter_read = None
        self.extra_ledger = []
        self.extra_counters = []
        self.read_failure = None
        self.sessions = []

    def checkout(self, timeout=None):
        store = self

        class Session:
            async def __aenter__(self):
                store.sessions.append(self)
                return self

            async def __aexit__(self, *args):
                pass

            def transaction(self, mode):
                assert isinstance(mode, ydb.QuerySerializableReadWrite)
                return RmwTransaction(store)

        return Session()


class RmwTransaction:
    def __init__(self, store):
        self.store = store
        self.counters = deepcopy(store.counters)
        self.ledger = deepcopy(store.ledger)
        self.revision = store.revision
        self.wrote = False
        self.operation = None
        self.finished = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def execute(self, query, parameters=None, settings=None):
        assert not self.finished
        assert settings.timeout in (10, 20)
        parameters = {key[1:]: value[0] for key, value in (parameters or {}).items()}
        if query.startswith("UPSERT"):
            self.wrote = True
            self.operation = parameters["op_id"]
            self.counters[parameters["counter_id"]] = {
                key: parameters[key] for key in ("counter_id", "value", "version")
            }
            assert parameters["op_id"] not in self.ledger
            self.ledger[parameters["op_id"]] = {
                key: parameters[key] for key in ("op_id", "counter_id", "delta", "payload")
            }
            rows = []
        elif "WHERE op_id" in query:
            row = self.ledger.get(parameters["op_id"])
            rows = [row] if row is not None else []
        elif "WHERE counter_id" in query:
            row = self.counters.get(parameters["counter_id"])
            rows = [row] if row is not None else []
            if self.store.on_counter_read:
                await self.store.on_counter_read()
        else:
            if self.store.read_failure:
                raise self.store.read_failure
            if "counter_id, value, version" in query:
                rows = list(self.counters.values()) + self.store.extra_counters
            else:
                rows = list(self.ledger.values()) + self.store.extra_ledger

        class Stream:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            def __aiter__(self):
                async def parts():
                    yield SimpleNamespace(rows=deepcopy(rows))

                return parts()

        return Stream()

    async def commit(self, settings=None):
        if self.wrote:
            if self.store.before_commit:
                await self.store.before_commit(self)
            if self.revision != self.store.revision:
                raise ydb.Aborted("serializable conflict")
            self.store.counters, self.store.ledger = self.counters, self.ledger
            self.store.revision += 1
            self.store.commits += 1
        self.finished = True
        if self.wrote and self.store.after_commit:
            await self.store.after_commit(self)


class TestSloRmwData:
    @pytest.fixture
    def rmw(self, monkeypatch):
        monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "tests/slo/src"))
        from jobs import rmw_jobs

        return rmw_jobs

    @pytest.fixture
    def store(self):
        return RmwStore()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("ambiguous", [False, True])
    async def test_apply_uses_same_id_after_sdk_retry_and_deduplicates(self, rmw, store, ambiguous):
        workload = _rmw_manager(rmw, store)
        operation = rmw.Operation("writer:1", 0, 3)
        workload.expected[operation.op_id] = operation
        injected = False

        async def failure(tx):
            nonlocal injected
            if not injected:
                injected = True
                raise ydb.BadSession("synthetic lost commit acknowledgement") if ambiguous else ydb.Aborted("conflict")

        if ambiguous:
            store.after_commit = failure
        else:
            store.before_commit = failure
        await workload.apply(operation)
        await workload.apply(operation)
        await workload.validate()
        assert store.commits == 1
        assert store.counters[0] == dict(counter_id=0, value=3, version=1)
        assert store.ledger == {operation.op_id: operation.row()}
        assert workload.attempts == 3
        assert workload.replays == (2 if ambiguous else 1)
        assert len({id(session) for session in store.sessions}) == len(store.sessions)
        assert workload.retry_settings.max_retries == ydb.RetrySettings().max_retries
        assert workload.retry_settings.idempotent
        assert workload.retry_settings.max_session_acquire_timeout == 20
        assert workload.metrics.stop.call_args.kwargs["attempts"] == 1

    @pytest.mark.asyncio
    async def test_run_stops_admission_and_settles_contending_calls_before_validate(self, rmw, store):
        workload = _rmw_manager(rmw, store)
        admitted = 0
        barrier = asyncio.Event()

        async def first_reads():
            nonlocal admitted
            if admitted < workload.args.write_threads:
                admitted += 1
                if admitted == workload.args.write_threads:
                    workload.stop.set()
                    barrier.set()
                await asyncio.wait_for(barrier.wait(), 5)

        store.on_counter_read = first_reads
        await asyncio.wait_for(workload.run_tests(), 5)
        assert len(workload.expected) == len(store.ledger) == store.commits == 4
        assert workload.attempts > store.commits
        assert store.counters[0] == dict(counter_id=0, value=7, version=4)
        assert store.counters[1] == dict(counter_id=1, value=0, version=0)
        assert workload.metrics.stop.call_args.args[0] == ("read",)

    @pytest.mark.asyncio
    async def test_original_final_error_wins_and_other_admitted_call_settles(self, rmw, store):
        workload = _rmw_manager(rmw, store)
        workload.args.write_threads = 2
        both = asyncio.Event()
        terminal = ydb.BadRequest("original final SDK error")
        started = 0

        async def first_reads():
            nonlocal started
            started += 1
            if started == 2:
                both.set()
            await asyncio.wait_for(both.wait(), 5)

        async def fail_one(tx):
            if tx.operation.startswith("0:"):
                store.read_failure = ydb.BadRequest("diagnostic failure")
                raise terminal
            await asyncio.wait_for(workload.stop.wait(), 5)

        def metric_stop(*args, **kwargs):
            if kwargs["error"] is terminal:
                raise RuntimeError("metric diagnostic failure")

        workload.metrics.stop.side_effect = metric_stop
        store.on_counter_read = first_reads
        store.before_commit = fail_one
        with pytest.raises(ydb.BadRequest) as failure:
            await asyncio.wait_for(workload.run_tests(), 5)
        assert failure.value is terminal
        assert store.commits == 1
        assert set(store.ledger) == {"1:1"}
        assert set(workload.expected) == {"0:1", "1:1"}

    @pytest.mark.asyncio
    async def test_sdk_failure_wins_over_an_earlier_success_metric_failure(self, rmw, store):
        workload = _rmw_manager(rmw, store)
        workload.args.write_threads = 2
        both = asyncio.Event()
        terminal = ydb.BadRequest("original final SDK error")
        started = 0

        async def first_reads():
            nonlocal started
            started += 1
            if started == 2:
                both.set()
            await asyncio.wait_for(both.wait(), 5)

        async def fail_second(tx):
            if tx.operation.startswith("1:"):
                await asyncio.wait_for(workload.stop.wait(), 5)
                raise terminal

        def metric_stop(labels, *args, **kwargs):
            if labels == ("write",) and kwargs["error"] is None:
                raise RuntimeError("earlier metrics failure")

        workload.metrics.stop.side_effect = metric_stop
        store.on_counter_read = first_reads
        store.before_commit = fail_second
        with pytest.raises(ydb.BadRequest) as failure:
            await asyncio.wait_for(workload.run_tests(), 5)
        assert failure.value is terminal
        assert store.commits == 1

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "corruption",
        [
            "sum_preserving",
            "coherent_missing",
            "duplicate",
            "payload",
            "version",
            "counter_id",
            "delta",
            "extra",
            "missing_counter",
            "duplicate_counter",
        ],
    )
    async def test_independent_validation_rejects_exact_data_corruption(self, rmw, store, corruption):
        workload = _rmw_manager(rmw, store)
        for key in range(2):
            operation = rmw.Operation(f"writer:{key}", key, 2)
            workload.expected[operation.op_id] = operation
            await workload.apply(operation)
        if corruption == "sum_preserving":
            store.counters[0]["value"] -= 1
            store.counters[1]["value"] += 1
        elif corruption == "coherent_missing":
            del store.ledger["writer:0"]
            store.counters[0].update(value=0, version=0)
        elif corruption == "duplicate":
            store.extra_ledger = [store.ledger["writer:0"]]
        elif corruption in ("payload", "counter_id", "delta"):
            store.ledger["writer:0"][corruption] = "bad" if corruption == "payload" else 17
        elif corruption == "version":
            store.counters[0]["version"] += 1
        elif corruption == "extra":
            store.ledger["extra"] = rmw.Operation("extra", 0, 0).row()
        elif corruption == "missing_counter":
            del store.counters[0]
        elif corruption == "duplicate_counter":
            store.extra_counters = [store.counters[0]]
        with pytest.raises(RuntimeError):
            await workload.validate()

    @pytest.mark.asyncio
    async def test_apply_rejects_nonidentical_replay_without_an_increment(self, rmw, store):
        workload = _rmw_manager(rmw, store)
        operation = rmw.Operation("same-id", 0, 1)
        await workload.apply(operation)
        with pytest.raises(RuntimeError):
            await workload.apply(rmw.Operation("same-id", 1, 2))
        assert store.commits == 1
        assert store.counters[1]["value"] == 0

    def test_rmw_cli_uses_existing_async_lifecycle_and_rejects_invalid_inputs(self, rmw):
        from options import get_root_parser
        from root_runner import _is_async_workload, create_runner
        from runners.rmw_runner import RmwRunner

        parser = get_root_parser()
        args = parser.parse_args(["rmw-run", "grpc://localhost:13936", "/local"])
        assert _is_async_workload(args)
        assert create_runner().runners["rmw"] is RmwRunner
        for option in (
            "--time",
            "--write-threads",
            "--counter-count",
            "--write-timeout",
            "--read-timeout",
            "--report-period",
        ):
            with pytest.raises(SystemExit) as failure:
                parser.parse_args(["rmw-run", "grpc://localhost:13936", "/local", option, "0"])
            assert failure.value.code == 2

    @pytest.mark.asyncio
    async def test_counts_sdk_checkout_retry_before_transaction_body(self, rmw, store, monkeypatch):
        workload = _rmw_manager(rmw, store)
        operation = rmw.Operation("checkout:1", 0, 1)
        workload.expected[operation.op_id] = operation
        original = store.checkout
        acquisitions = 0

        class FailedCheckout:
            async def __aenter__(self):
                raise ydb.Aborted("checkout failed before the transaction callback")

            async def __aexit__(self, *args):
                raise AssertionError("failed checkout was never entered")

        def checkout(timeout=None):
            nonlocal acquisitions
            acquisitions += 1
            return FailedCheckout() if acquisitions == 1 else original(timeout)

        monkeypatch.setattr(store, "checkout", checkout)
        await workload.apply(operation)
        assert acquisitions == 2
        assert workload.attempts == 2
        assert workload.metrics.stop.call_args.kwargs["attempts"] == 2
        assert store.counters[0] == dict(counter_id=0, value=1, version=1)
        assert store.ledger == {operation.op_id: operation.row()}

    @pytest.mark.asyncio
    @pytest.mark.parametrize("failed_create", [1, 2])
    async def test_setup_failure_drops_only_successfully_created_tables(self, rmw, monkeypatch, failed_create):
        from runners import rmw_runner

        failure = ydb.BadRequest("CREATE failed without ownership")
        statements = []

        class Pool:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def execute_with_retries(self, query):
                statements.append(query)
                if query.startswith("CREATE") and len(statements) == failed_create:
                    raise failure

        monkeypatch.setattr(rmw_runner, "create_metrics", lambda _: Mock())
        monkeypatch.setattr(rmw_runner.ydb.aio, "QuerySessionPool", lambda _: Pool())
        with pytest.raises(ydb.BadRequest) as caught:
            await rmw_runner.RmwRunner().run_async(SimpleNamespace(otlp_endpoint="", db="/local"))
        assert caught.value is failure
        drops = [query for query in statements if query.startswith("DROP")]
        owned = statements[0].split("`")[1]
        assert drops == ([f"DROP TABLE `{owned}`;"] if failed_create == 2 else [])
