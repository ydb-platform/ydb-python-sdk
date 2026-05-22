# OpenTelemetry example (YDB Python SDK)

Async demo in [`otel_example.py`](otel_example.py): OTLP export, `enable_tracing()`,
`enable_metrics()`, `app_startup` and `example_tli` application spans, SDK client
metrics, bank table, Serializable transactions (TLI-style load).

[`load_tank.py`](load_tank.py) runs a small step-like load profile for the
metrics dashboard:

```text
Peak RPS -> Medium RPS -> Min RPS -> Medium RPS -> repeat
```

Most steps assume the **repository root** as the current directory; the install step also shows the variant from this folder.

## 1. Start YDB (or the full stack) with Docker **first**

Without running containers, the example has nothing to connect to.

**Only YDB** (minimal `docker-compose.yml` in the repo root — enough for the script on the host):

```sh
cd /path/to/ydb-python-sdk
docker compose up -d
# wait until the ydb container is healthy / port 2136 is open, then continue
```

**Full stack** (YDB + OTLP collector + Tempo + Prometheus + Grafana; the
`otel-example` service runs the tracing/metrics demo once, and `load-generator`
runs the metrics load tank). The compose file is `compose-e2e.yaml` next to this
README.

```sh
cd /path/to/ydb-python-sdk
docker compose -f examples/opentelemetry/compose-e2e.yaml up --build
```

From this folder the build context is still resolved correctly (it is `../..` relative to the compose file):

```sh
cd /path/to/ydb-python-sdk/examples/opentelemetry
docker compose -f compose-e2e.yaml up --build
```

The first run builds the `otel-example` image from the local SDK source (`Dockerfile` in this folder, `.dockerignore` at the repo root keeps the context small). Subsequent runs reuse the cached image; pass `--build` if you change the SDK or the demo script.

Grafana: http://localhost:3000
Prometheus: http://localhost:9090

Grafana is provisioned with the **YDB Python SDK Metrics** dashboard. It uses
Prometheus queries for SDK metrics such as `db_client_operation_duration`,
`ydb_client_operation_failed`, `ydb_query_session_count`,
`ydb_query_session_pending_requests`, `ydb_query_session_create_time`, and
`ydb_client_retry_duration`. Use Grafana Explore for ad-hoc traces through Tempo
and metrics through Prometheus.

The examples configure custom OpenTelemetry histogram views in
[`metrics_views.py`](metrics_views.py). The SDK records duration values in
seconds, but the default histogram buckets are too coarse for fast local YDB
operations. The custom views keep the `s` unit and use sub-millisecond /
millisecond-scale buckets so Grafana percentiles show meaningful latency
distributions.

**Logs for `otel-example`:** the container name is prefixed (e.g. `opentelemetry-otel-example-1`); use `docker compose -f examples/opentelemetry/compose-e2e.yaml ps` or `docker ps -a` to find it. The service is one-shot (`restart: "no"`) — it may already have exited.

**Logs for `load-generator`:** the service is also one-shot. It runs for
`LOAD_TANK_TOTAL_TIME` seconds and then exits after flushing metrics.

## 2. Install dependencies (on the host, for a local `python` run)

**From the repository root** (editable SDK + pins from this example):

```sh
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e '.[opentelemetry]' -r examples/opentelemetry/requirements.txt
```

**If your shell is already in** `examples/opentelemetry/` (same result):

```sh
pip install -e '../..[opentelemetry]' -r requirements.txt
```

`requirements.txt` includes a merge of the repository’s core `requirements.txt` (grpc, ``packaging``, …) plus the OpenTelemetry lines. The `-e` install is only needed to register the package; otherwise this example prepends the repo to ``sys.path``.

**Without** `pip -e` (``ydb`` from the checkout via `sys.path`): from this directory run `pip install -r requirements.txt`, then ``python otel_example.py``.

## 3. Run the example (after YDB from step 1 is up)

```sh
python examples/opentelemetry/otel_example.py
```

Defaults: YDB `grpc://localhost:2136`, OTLP `http://localhost:4317` (for a local collector, if you use one). The same OTLP endpoint receives both traces and metrics.

Run the load tank against an already running local stack:

```sh
python examples/opentelemetry/load_tank.py
```

## Environment (Docker / overrides)

| Variable | Meaning                                                  |
|----------|----------------------------------------------------------|
| `YDB_ENDPOINT` | e.g. `grpc://ydb:2136` inside the Compose network        |
| `YDB_DATABASE` | default `/local`                                         |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | e.g. `http://otel-collector:4317`                        |
| `OTEL_SERVICE_NAME` | service name attached to exported telemetry              |
| `LOAD_TANK_TOTAL_TIME` | total load duration in seconds, default `6000`           |
| `LOAD_TANK_WORKERS` | number of concurrent workers, default `40`               |
| `LOAD_TANK_POOL_SIZE` | query session pool size, default `20`                    |
| `LOAD_TANK_PEAK_RPS` | peak phase target RPS, default `120`                     |
| `LOAD_TANK_MEDIUM_RPS` | medium phase target RPS, default `30`                    |
| `LOAD_TANK_MIN_RPS` | low phase target RPS, default `3`                        |
| `LOAD_TANK_ERROR_RPS` | failed query target RPS, default `1`; set `0` to disable |
| `LOAD_TANK_PRESSURE_POOL_SIZE` | pool size for session pressure metrics, default `1`      |
| `LOAD_TANK_PRESSURE_WORKERS` | concurrent contenders for the pressure pool, default `8` |
| `LOAD_TANK_PRESSURE_HOLD_TIME` | seconds to hold the pressure-pool session, default `1.5` |
| `LOAD_TANK_PRESSURE_ACQUIRE_TIMEOUT` | short acquire timeout for timeout metrics, default `1.0` |
| `LOAD_TANK_PRESSURE_INTERVAL` | pause between pressure rounds, default `0.2`             |
| `LOAD_TANK_SESSION_CHURN_INTERVAL` | interval for creating fresh sessions, default `2.0`      |
| `LOAD_TANK_PEAK_DURATION` | peak phase duration in seconds, default `60`             |
| `LOAD_TANK_MEDIUM_DURATION` | medium phase duration in seconds, default `90`           |
| `LOAD_TANK_MIN_DURATION` | low phase duration in seconds, default `60`              |
| `LOAD_TANK_QUERY` | query executed by workers, default `SELECT 1 AS value`   |
| `LOAD_TANK_ERROR_QUERY` | query used to produce failed-operation metrics           |
