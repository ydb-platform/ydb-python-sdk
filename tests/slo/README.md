# SLO workload

SLO is the type of test where app based on ydb-sdk is tested against falling YDB cluster nodes, tablets, network
(that is possible situations for distributed DBs with hundreds of nodes)

## Workload types

- **sync-query** — tests table operations via Query API (read/write)
- **sync-table** — tests table operations via Table API (read/write)
- **topic** — tests topic operations (publish/consume)

## Quick start (Docker Compose)

The runner script handles everything: clones [ydb-slo-action](https://github.com/ydb-platform/ydb-slo-action/tree/v2/deploy) infra configs, builds the workload image,
starts YDB cluster + Prometheus via docker compose, runs the workload, and tears down on exit.

```sh
cd tests/slo

# Run topic workload (default)
WORKLOAD_NAME=topic ./slo_runner.sh

# Run table workload
WORKLOAD_NAME=sync-query ./slo_runner.sh
```

## Local run (against your own YDB)

Start the playground cluster and run the workload directly with Python.
All examples run from `tests/slo/` directory with activated venv.

```sh
# Start playground YDB cluster
docker compose -f playground/configs/compose.yaml up -d

# Activate venv
source ../../.venv/bin/activate
```

### Using CLI arguments

```sh
# Topic workload — write only, 60 sec, debug logging
python ./src grpc://localhost:2136 /Root/testdb \
    --workload-name topic \
    --topic-path /Root/testdb/slo_topic \
    --otlp-endpoint "" \
    --write-rps 1 --write-threads 1 --read-threads 0 \
    --time 60 --debug

# Topic workload — read + write
python ./src grpc://localhost:2136 /Root/testdb \
    --workload-name topic \
    --otlp-endpoint "" \
    --write-rps 5 --write-threads 2 --read-threads 2 --read-rps 10 \
    --time 120

# Table workload (sync-query) — default RPS
python ./src grpc://localhost:2136 /Root/testdb \
    --workload-name sync-query \
    --otlp-endpoint "" \
    --time 60 --debug

# Table workload — high load
python ./src grpc://localhost:2136 /Root/testdb \
    --workload-name sync-query \
    --otlp-endpoint "" \
    --read-rps 500 --write-rps 100 --read-threads 8 --write-threads 4 \
    --time 300
```

### Using environment variables

```sh
# All settings via env vars
YDB_ENDPOINT=grpc://localhost:2136 \
YDB_DATABASE=/Root/testdb \
WORKLOAD_NAME=topic \
WORKLOAD_DURATION=60 \
OTEL_EXPORTER_OTLP_ENDPOINT="" \
    python ./src --debug

# Mix: connection via env, tuning via args
YDB_ENDPOINT=grpc://localhost:2136 \
YDB_DATABASE=/Root/testdb \
    python ./src --workload-name sync-query --otlp-endpoint "" \
    --read-rps 200 --write-rps 50 --time 120
```

### Tear down

```sh
docker compose -f playground/configs/compose.yaml down
```

### Configuration

Override defaults via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `WORKLOAD_NAME` | `topic` | Workload type: `sync-query`, `sync-table`, `topic` |
| `RUN_TIME_SEC` | `120` | Workload run time in seconds |
| `WRITE_RPS` | `1` | Write RPS |
| `READ_THREADS` | `0` | Read worker threads |
| `WRITE_THREADS` | `1` | Write worker threads |
| `MESSAGE_SIZE` | `100` | Topic message size in bytes |
| `REPORT_PERIOD_MS` | `1000` | Metrics flush period in ms |
| `DEBUG` | `0` | Set to `1` to enable debug logging |
| `WORKLOAD_IMAGE` | `ydb-python-slo:local` | Docker image name for the workload |

## CLI arguments

The workload runs as a single command that creates resources, runs the workload, and cleans up.
Every flag supports a fallback chain: **CLI arg > environment variable > hardcoded default**.

```
python tests/slo/src [endpoint] [db] [options]
```

### Connection & identity

| Argument | Env var | Default | Description |
|----------|---------|---------|-------------|
| `endpoint` (positional) | `YDB_ENDPOINT` | `grpc://ydb:2136` | YDB endpoint |
| `db` (positional) | `YDB_DATABASE` | `/Root/testdb` | YDB database path |
| `--workload-name` | `WORKLOAD_NAME` | `sync-query` | Workload type |
| `--workload-ref` | `WORKLOAD_REF` / `REF` | `main` | Reference label for metrics |
| `--otlp-endpoint` | `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://ydb-prometheus:9090/api/v1/otlp` | OTLP endpoint |
| `--time` | `WORKLOAD_DURATION` | `600` | Workload duration in seconds |
| `--debug` | — | `false` | Enable debug logging |

### Run parameters

| Argument | Default | Description |
|----------|---------|-------------|
| `--read-rps` | `100` | Read RPS limit |
| `--read-timeout` | `10000` | Read timeout in ms |
| `--write-rps` | `10` | Write RPS limit |
| `--write-timeout` | `20000` | Write timeout in ms |
| `--read-threads` | `8` | Read worker threads |
| `--write-threads` | `4` | Write worker threads |
| `--shutdown-time` | `10` | Graceful shutdown time in seconds |
| `--report-period` | `1000` | Metrics push period in ms |

### Table parameters

| Argument | Default | Description |
|----------|---------|-------------|
| `--table-name` | `key_value` | Table name |
| `--min-partitions-count` | `6` | Minimum partition count |
| `--max-partitions-count` | `1000` | Maximum partition count |
| `--partition-size` | `100` | Partition size in MB |
| `--initial-data-count` | `1000` | Rows to pre-fill |
| `--batch-size` | `100` | Rows per insert batch |
| `--threads` | `10` | Threads for initial data fill |

### Topic parameters

| Argument | Default | Description |
|----------|---------|-------------|
| `--topic-path` | `/Root/testdb/slo_topic` | Topic path |
| `--topic-consumer` | `slo_consumer` | Consumer name |
| `--topic-partitions` | `1` | Topic partition count |
| `--message-size` | `100` | Message size in bytes |

## What's inside

### Table workload

Creates three jobs: `readJob`, `writeJob`, `metricsJob`.

- `readJob` — reads rows from the table with random identifiers
- `writeJob` — generates and inserts rows
- `metricsJob` — periodically sends metrics to Prometheus

Table schema:
- `object_id Uint64`
- `object_hash Uint64 Digest::NumericHash(id)`
- `payload_str UTF8`
- `payload_double Double`
- `payload_timestamp Timestamp`

Primary key: `("object_hash", "object_id")`

### Topic workload

Creates three jobs: `readJob`, `writeJob`, `metricsJob`.

- `readJob` — reads messages from topic using TopicReader and commits offsets
- `writeJob` — generates and publishes messages using TopicWriter
- `metricsJob` — periodically sends metrics to Prometheus

## Collected metrics

- `sdk_operations_total` — total operations (labeled by `operation_status`: success/err)
- `sdk_errors_total` — errors by type
- `sdk_pending_operations` — in-flight operations
- `sdk_retry_attempts_total` — retry attempts
- `sdk_operation_latency_p50_seconds` — P50 latency
- `sdk_operation_latency_p95_seconds` — P95 latency
- `sdk_operation_latency_p99_seconds` — P99 latency
