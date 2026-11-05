"""Verify acknowledged data with one Query driver throughout Bridge chaos."""

import json
import os
import time
import traceback
import uuid
from pathlib import Path

import ydb


def main():
    result = {"successes": 0, "errors": [], "missing": [], "verified": False}
    table = "bridge_probe_" + uuid.uuid4().hex
    confirmed = {}
    try:
        config = ydb.DriverConfig(
            os.environ["YDB_ENDPOINT"],
            database=os.environ["YDB_DATABASE"],
            credentials=ydb.AnonymousCredentials(),
        )
        with ydb.Driver(config) as driver:
            driver.wait(timeout=60)
            with ydb.QuerySessionPool(driver) as pool:
                version = pool.execute_with_retries("SELECT CAST(version() AS Utf8) AS version;")
                result["server_version"] = version[0].rows[0].version
                pool.execute_with_retries(f"CREATE TABLE `{table}` (id Uint64, payload Utf8, PRIMARY KEY(id));")
                deadline = time.monotonic() + int(os.environ.get("WORKLOAD_DURATION", "900"))
                retry = ydb.RetrySettings(
                    max_retries=10,
                    max_session_acquire_timeout=2,
                    backoff_slot_duration=0.1,
                    backoff_ceiling=3,
                    idempotent=True,
                )
                seq = 0
                while time.monotonic() < deadline:
                    seq += 1
                    payload = f"{table}_{seq}"
                    started = time.monotonic()
                    try:
                        rows = pool.execute_with_retries(
                            f"UPSERT INTO `{table}` (id, payload) VALUES "
                            f'(CAST({seq} AS Uint64), CAST("{payload}" AS Utf8)); '
                            f"SELECT payload FROM `{table}` WHERE id = CAST({seq} AS Uint64);",
                            tx_mode=ydb.QuerySerializableReadWrite(),
                            settings=ydb.BaseRequestSettings().with_timeout(10),
                            retry_settings=retry,
                        )
                        if len(rows[0].rows) != 1 or rows[0].rows[0].payload != payload:
                            raise AssertionError(f"Incorrect read-after-write result for {seq}")
                        confirmed[seq] = payload
                        result["successes"] += 1
                        print(json.dumps({"seq": seq, "ok": True, "seconds": time.monotonic() - started}), flush=True)
                    except AssertionError:
                        raise
                    except Exception as error:
                        result["errors"].append({"seq": seq, "error": repr(error)})
                        print(json.dumps({"seq": seq, "ok": False, "error": repr(error)}), flush=True)
                    time.sleep(0.5)
                rows = pool.execute_with_retries(f"SELECT id, payload FROM `{table}`;")
                stored = {row.id: row.payload for row in rows[0].rows}
                result["missing"] = [seq for seq, payload in confirmed.items() if stored.get(seq) != payload]
                result["verified"] = True
    except Exception as error:
        result["fatal"] = repr(error)
        traceback.print_exc()
    result["passed"] = bool(
        result["successes"]
        and result["verified"]
        and not result["errors"]
        and not result["missing"]
        and not result.get("fatal")
    )
    Path("/tmp/bridge-probe.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result), flush=True)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
