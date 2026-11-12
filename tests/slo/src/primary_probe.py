"""Exercise fresh-session routing and acknowledged data on long-lived drivers."""

import asyncio
import json
import os
from pathlib import Path
import threading
import time
import traceback
from urllib.parse import parse_qs, urlparse
import uuid

import ydb
import ydb.aio

from bridge_observer import BridgeObserver, is_rpc_cancellation, route_observation

MODES = ("sync-table", "sync-query", "async-table", "async-query", "control-table")


class Probe:
    def __init__(self):
        self.table = "primary_probe_" + uuid.uuid4().hex
        self.stop = threading.Event()
        self.lock = threading.Lock()
        self.stats = {mode: {"successes": 0, "errors": [], "confirmed": [], "driver_starts": 0} for mode in MODES}
        self.fatal = []
        self.observer = BridgeObserver(os.environ["ORACLE_ENDPOINTS"].split(","), os.environ["YDB_DATABASE"])

    def emit(self, event, mode, **values):
        with self.lock:
            print(json.dumps({"event": event, "mode": mode, "ts": time.time(), **values}), flush=True)

    def error(self, mode, error, stage):
        with self.lock:
            self.stats[mode]["errors"].append({"stage": stage, "error": repr(error)})
        self.emit("error", mode, error=repr(error), stage=stage)

    def fail(self, mode, error):
        with self.lock:
            self.fatal.append({"mode": mode, "error": repr(error)})
        traceback.print_exc()
        self.stop.set()

    def config(self, mode):
        return ydb.DriverConfig(
            os.environ["YDB_ENDPOINT"],
            database=os.environ["YDB_DATABASE"],
            credentials=ydb.AnonymousCredentials(),
            prefer_primary_pile=mode != "control-table",
        )

    def sql(self, mode, seq):
        payload = f"{self.table}:{mode}:{seq}"
        return (
            f"UPSERT INTO `{self.table}` (`mode`, seq, payload) VALUES "
            f'(CAST("{mode}" AS Utf8), CAST({seq} AS Uint64), CAST("{payload}" AS Utf8)); '
            f'SELECT payload FROM `{self.table}` WHERE `mode` = CAST("{mode}" AS Utf8) '
            f"AND seq = CAST({seq} AS Uint64);"
        )

    def validate(self, mode, seq, rows):
        if len(rows) != 1 or len(rows[0].rows) != 1 or rows[0].rows[0].payload != f"{self.table}:{mode}:{seq}":
            raise AssertionError(f"Incorrect read-after-write for {mode}/{seq}")

    def confirm(self, mode, seq):
        with self.lock:
            self.stats[mode]["successes"] += 1
            self.stats[mode]["confirmed"].append(seq)
            if all(self.stats[name]["successes"] for name in MODES):
                Path("/tmp/bridge-probe-ready").touch()
        self.emit("operation", mode, seq=seq, ok=True)

    def started(self, mode):
        with self.lock:
            self.stats[mode]["driver_starts"] += 1
        self.emit("driver_started", mode, prefer_primary_pile=mode != "control-table", sdk=ydb.__version__)

    def session_created(self, mode, session, before, after):
        if mode.endswith("query"):
            node_id = session.node_id
        else:
            node_id = int(parse_qs(urlparse(session.session_id).query)["node_id"][0])
        self.emit("session_created", mode, **route_observation(node_id, before, after))

    def sync_worker(self, mode):
        try:
            with ydb.Driver(self.config(mode)) as driver:
                driver.wait(timeout=60)
                self.started(mode)
                seq = 0
                while not self.stop.is_set():
                    seq += 1
                    session = None
                    try:
                        before = self.observer.snapshot()
                        session = ydb.QuerySession(driver) if mode.endswith("query") else driver.table_client.session()
                        session.create(settings=ydb.BaseRequestSettings().with_timeout(5))
                        self.session_created(mode, session, before, self.observer.snapshot())
                        if mode.endswith("query"):
                            with session.transaction(ydb.QuerySerializableReadWrite()) as tx:
                                with tx.execute(
                                    self.sql(mode, seq), settings=ydb.BaseRequestSettings().with_timeout(5)
                                ) as stream:
                                    self.validate(mode, seq, list(stream))
                                tx.commit(settings=ydb.BaseRequestSettings().with_timeout(5))
                        else:
                            rows = session.transaction(ydb.SerializableReadWrite()).execute(
                                self.sql(mode, seq), commit_tx=True, settings=ydb.BaseRequestSettings().with_timeout(5)
                            )
                            self.validate(mode, seq, rows)
                        self.confirm(mode, seq)
                    except ydb.Error as error:
                        self.error(mode, error, "operation")
                    finally:
                        if session is not None and session.session_id:
                            try:
                                session.delete(settings=ydb.BaseRequestSettings().with_timeout(5))
                            except ydb.Error as error:
                                self.error(mode, error, "cleanup")
                    self.stop.wait(1)
        except BaseException as error:
            self.fail(mode, error)

    async def async_worker(self, mode):
        try:
            async with ydb.aio.Driver(self.config(mode)) as driver:
                await driver.wait(timeout=60)
                self.started(mode)
                seq = 0
                while not self.stop.is_set():
                    seq += 1
                    session = None
                    try:
                        before = await asyncio.to_thread(self.observer.snapshot)
                        session = (
                            ydb.aio.QuerySession(driver) if mode.endswith("query") else driver.table_client.session()
                        )
                        await session.create(settings=ydb.BaseRequestSettings().with_timeout(5))
                        after = await asyncio.to_thread(self.observer.snapshot)
                        self.session_created(mode, session, before, after)
                        if mode.endswith("query"):
                            async with session.transaction(ydb.QuerySerializableReadWrite()) as tx:
                                async with await tx.execute(
                                    self.sql(mode, seq), settings=ydb.BaseRequestSettings().with_timeout(5)
                                ) as stream:
                                    self.validate(mode, seq, [part async for part in stream])
                                await tx.commit(settings=ydb.BaseRequestSettings().with_timeout(5))
                        else:
                            rows = await session.transaction(ydb.SerializableReadWrite()).execute(
                                self.sql(mode, seq), commit_tx=True, settings=ydb.BaseRequestSettings().with_timeout(5)
                            )
                            self.validate(mode, seq, rows)
                        self.confirm(mode, seq)
                    except ydb.Error as error:
                        self.error(mode, error, "operation")
                    except asyncio.CancelledError as error:
                        if not is_rpc_cancellation():
                            raise
                        self.error(mode, error, "rpc_cancelled")
                        self.emit("rpc_cancelled", mode, task_cancel_requests=0)
                    finally:
                        if session is not None and session.session_id:
                            try:
                                await session.delete(settings=ydb.BaseRequestSettings().with_timeout(5))
                            except ydb.Error as error:
                                self.error(mode, error, "cleanup")
                            except asyncio.CancelledError as error:
                                if not is_rpc_cancellation():
                                    raise
                                self.error(mode, error, "cleanup_rpc_cancelled")
                    await asyncio.sleep(1)
        except BaseException as error:
            self.fail(mode, error)

    async def async_workers(self):
        await asyncio.gather(self.async_worker("async-table"), self.async_worker("async-query"))

    def run(self):
        with ydb.Driver(self.config("control-table")) as setup:
            setup.wait(timeout=60)
            with ydb.QuerySessionPool(setup) as pool:
                version = pool.execute_with_retries("SELECT CAST(version() AS Utf8) AS version;")[0].rows[0].version
                pool.execute_with_retries(
                    f"CREATE TABLE `{self.table}` (`mode` Utf8, seq Uint64, payload Utf8, PRIMARY KEY(`mode`, seq));"
                )
        threads = [
            threading.Thread(target=self.sync_worker, args=(mode,), daemon=True)
            for mode in ("sync-table", "sync-query", "control-table")
        ]
        threads.append(threading.Thread(target=lambda: asyncio.run(self.async_workers()), daemon=True))
        for thread in threads:
            thread.start()
        deadline = time.monotonic() + int(os.environ["WORKLOAD_DURATION"]) + 180
        while not self.stop.is_set() and time.monotonic() < deadline and not Path("/tmp/bridge-probe-stop").exists():
            time.sleep(0.5)
        stopped_at = time.time()
        self.stop.set()
        for thread in threads:
            thread.join(timeout=60)
        if any(thread.is_alive() for thread in threads):
            self.fatal.append({"error": "Probe worker did not finish"})
        self.observer.close()
        result = {
            "table": self.table,
            "server_version": version,
            "modes": self.stats,
            "fatal": self.fatal,
            "stopped_at": stopped_at,
            "passed": not self.fatal and all(self.stats[mode]["successes"] for mode in MODES),
        }
        Path("/tmp/bridge-probe.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result), flush=True)
        return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(Probe().run())
