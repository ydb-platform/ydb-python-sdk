# SLO workload

SLO is the type of test where app based on ydb-sdk is tested against falling YDB cluster nodes, tablets, network
(that is possible situations for distributed DBs with hundreds of nodes)

### Workload types:

There are two workload types:

- **Table SLO** - tests table operations (read/write)
- **Topic SLO** - tests topic operations (publish/consume)

### Implementations / labels:

The workload is selected by a single label (`WORKLOAD_NAME` env var, also the
`sdk.name` matrix value in `.github/workflows/slo.yml`). The sync/async
execution mode is derived from the label itself — an `async-*` label runs the
async (`ydb.aio`) path:

| Label            | Service               | Mode  |
|------------------|-----------------------|-------|
| `sync-table`     | Table service         | sync  |
| `sync-query`     | Query service         | sync  |
| `async-query`    | Query service         | async |
| `sync-topic`     | Topic service         | sync  |
| `async-topic`    | Topic service         | async |
| `sync-topic-tx`  | Topic + Query (tx)    | sync  |
| `async-topic-tx` | Topic + Query (tx)    | async |

> The `--async` CLI flag is kept as a manual override for `*-run` commands.
> The bare `topic` label is still accepted as an alias for `sync-topic`.

### Usage:

Each workload type has 3 commands:

**Table commands:**
- `table-create`  - creates table in database
- `table-cleanup` - drops table in database
- `table-run`     - runs table workload (read and write to table with set RPS)

**Topic commands:**
- `topic-create`  - creates topic with consumer in database
- `topic-cleanup` - drops topic in database
- `topic-run`     - runs topic workload (publish and consume messages with set RPS)

### Infra (Docker Compose)

SLO workload is designed to run **inside the Docker Compose network** so it can reach YDB/Prometheus by service DNS names without publishing ports to localhost.

Infra compose configs are maintained in a separate repo:
- https://github.com/ydb-platform/ydb-slo-action/tree/main/deploy

Expected setup:
- Start infra using `deploy/compose.yml` from `ydb-slo-action`
- Infra network name should be `ydb_cluster`
- Workload container attaches to that network

Example infra start (from the `ydb-slo-action` repo root):
- `docker compose -f deploy/compose.yml --profile telemetry up -d --build`

### Runner script (`tests/slo/slo_runner.sh`)

This repo contains a simple maintainer convenience runner that:
1) builds the workload image
2) runs a basic SLO workload inside `ydb_cluster`

It is intentionally minimal (not a complete interface for all workload options). For full control, use the commands in `tests/slo/src/` directly.

Example usage (infra must already be running):
- `NETWORK_NAME=ydb_cluster ./tests/slo/slo_runner.sh`

Defaults used by the runner (override via env vars):
- `NETWORK_NAME=ydb_cluster`
- `YDB_ENDPOINT=grpc://ydb-storage-1:2136` (also commonly works as `grpc://storage-1:2136`)
- `YDB_DATABASE=/Root/testdb`
- `OTLP_ENDPOINT=http://prometheus:9090/api/v1/otlp/v1/metrics`

### Run examples with all arguments:

You can also configure the OTLP endpoint via environment variable:
- `OTLP_ENDPOINT=http://ydb-prometheus:9090/api/v1/otlp/v1/metrics` (full OTLP metrics endpoint)

**Table examples:**

table-create:
`python tests/slo/src/ table-create localhost:2136 /local -t tableName
--min-partitions-count 6 --max-partitions-count 1000 --partition-size 1 -с 1000
--write-timeout 10000`

table-cleanup:
`python tests/slo/src/ table-cleanup localhost:2136 /local -t tableName`

table-run:
`python tests/slo/src/ table-run localhost:2136 /local -t tableName
--otlp-endpoint http://ydb-prometheus:9090/api/v1/otlp/v1/metrics
--report-period 250
--read-rps 1000 --read-timeout 10000
--write-rps 100 --write-timeout 10000
--time 600 --shutdown-time 30`

**Topic examples:**

topic-create:
`python tests/slo/src/ topic-create localhost:2136 /local
--topic-path /local/slo_topic --topic-consumer slo_consumer`

topic-cleanup:
`python tests/slo/src/ topic-cleanup localhost:2136 /local --topic-path /local/slo_topic`

topic-run:
`python tests/slo/src/ topic-run localhost:2136 /local
--topic-path /local/slo_topic --topic-consumer slo_consumer
--otlp-endpoint http://ydb-prometheus:9090/api/v1/otlp/v1/metrics
--report-period 250
--topic-write-rps 50 --topic-read-rps 100
--topic-write-timeout 5000 --topic-read-timeout 3000
--time 600 --shutdown-time 30`

## Arguments for commands:

### table-create
`python tests/slo/src/ table-create <endpoint> <db> [options]`

```
Arguments:
  endpoint                        YDB endpoint to connect to
  db                              YDB database to connect to

Options:
  -t --table-name                  <string> table name to create

  -p-min   --min-partitions-count  <int>    minimum amount of partitions in table
  -p-max   --max-partitions-count  <int>    maximum amount of partitions in table
  -p-size  --partition-size        <int>    partition size in mb

  -c --initial-data-count          <int>    amount of initially created rows

  --write-timeout                  <int>    write timeout milliseconds

  --batch-size                     <int>    amount of new records in each create request
  --threads                        <int>    number of threads to use

```

### table-cleanup
`python tests/slo/src/ table-cleanup <endpoint> <db> [options]`

```
Arguments:
  endpoint                        YDB endpoint to connect to
  db                              YDB database to connect to

Options:
  -t --table-name                  <string> table name to create
```

### table-run
`python tests/slo/src/ table-run <endpoint> <db> [options]`

```
Arguments:
  endpoint                        YDB endpoint to connect to
  db                              YDB database to connect to

Options:
  -t --table-name         <string> table name to create

  --otlp-endpoint         <string> Prometheus OTLP metrics endpoint (e.g. http://ydb-prometheus:9090/api/v1/otlp/v1/metrics)
  --report-period         <int>    metrics export period in milliseconds

  --read-rps              <int>    read RPS
  --read-timeout          <int>    read timeout milliseconds

  --write-rps             <int>    write RPS
  --write-timeout         <int>    write timeout milliseconds

  --time                  <int>    run time in seconds
  --shutdown-time         <int>    graceful shutdown time in seconds

  --read-threads          <int>    number of threads to use for write requests
  --write-threads         <int>    number of threads to use for read requests
```

### topic-create
`python tests/slo/src/ topic-create <endpoint> <db> [options]`

```
Arguments:
  endpoint                        YDB endpoint to connect to
  db                              YDB database to connect to

Options:
  --topic-path                    <string> topic path to create
  --topic-consumer                <string> consumer name
  --topic-min-partitions          <int>    minimum active partitions
  --topic-max-partitions          <int>    maximum active partitions
  --topic-retention-hours         <int>    retention period in hours
```

### topic-cleanup
`python tests/slo/src/ topic-cleanup <endpoint> <db> [options]`

```
Arguments:
  endpoint                        YDB endpoint to connect to
  db                              YDB database to connect to

Options:
  --topic-path                    <string> topic path to drop
```

### topic-run
`python tests/slo/src/ topic-run <endpoint> <db> [options]`

```
Arguments:
  endpoint                        YDB endpoint to connect to
  db                              YDB database to connect to

Options:
  --topic-path                    <string> topic path
  --topic-consumer                <string> consumer name

  --otlp-endpoint                 <string> Prometheus OTLP metrics endpoint (e.g. http://ydb-prometheus:9090/api/v1/otlp/v1/metrics)
  --report-period                 <int>    metrics export period in milliseconds

  --topic-read-rps                <int>    read RPS for topics
  --topic-read-timeout            <int>    read timeout milliseconds for topics
  --topic-write-rps               <int>    write RPS for topics
  --topic-write-timeout           <int>    write timeout milliseconds for topics

  --topic-message-size            <int>    message size in bytes
  --topic-read-threads            <int>    number of threads to use for read requests
  --topic-write-threads           <int>    number of threads to use for write requests

  --time                          <int>    run time in seconds
  --shutdown-time                 <int>    graceful shutdown time in seconds
```

## Authentication

Workload using [auth-env](https://ydb.yandex-team.ru/docs/reference/ydb-sdk/recipes/auth-env) for authentication.

## What's inside

### Table workload
When running `table-run` command, the program creates three jobs: `readJob`, `writeJob`, `metricsJob`.

- `readJob`    reads rows from the table one by one with random identifiers generated by writeJob
- `writeJob`   generates and inserts rows
- `metricsJob` periodically sends metrics to Prometheus

Table have these fields:
- `object_id Uint64`
- `object_hash Uint64 Digest::NumericHash(id)`
- `payload_str UTF8`
- `payload_double Double`
- `payload_timestamp Timestamp`

Primary key: `("object_hash", "object_id")`

### Topic workload
When running `topic-run` (`sync-topic` / `async-topic`), the program creates `readJob`, `writeJob` and `metricsJob`, and additionally **validates end-to-end delivery and per-producer ordering** under chaos.

- `writeJob` — each writer is pinned to a partition (`partition_id = i % partitions`) with a stable, ref-scoped `producer_id`, and publishes with `write_with_ack`. The seqno advances only on a successful ack (a failed write leaves no gap).
- `readJob` — reads with a consumer, commits offsets, and demultiplexes messages by `writer_id`, tracking the next expected seqno per producer (shared across readers, since a partition can move between them on rebalance):
  - a **forward gap** (a seqno past the expected one) is counted as **lost** — partition order is server-guaranteed, so a gap is real loss (fails the run via the `*_error*` threshold);
  - a **backward** seqno (already seen) is a **duplicate** — reconnect redelivery; with producer-id dedup it should stay near zero (informational);
  - **end-to-end latency** is `read_ts − write_ts` for the first delivery of each message (writer and reader share the process, so the timestamps are comparable).

Each message carries `writer_id:seqno:write_ts_ns:` followed by padding to the configured size. Topics are scoped per ref so the current and baseline containers (same cluster, run in parallel) don't share a topic.

### Transactional topic ↔ table workload

When running `topic-run` under `sync-topic-tx` / `async-topic-tx`, **both** ends of
the pipeline run inside a YDB transaction, validating **exactly-once** delivery of
a topic into a table under chaos **and** under TLI (transaction locks invalidated):

- `writeJob` — a `tx_writer` writes a batch of messages to the topic while the same
  transaction reads-and-bumps a shared hot counter row (table → topic). The commit
  persists the topic write and the table update atomically; `seqno` advances only on
  a successful commit (a chaos/TLI abort leaves no gap).
- `readJob` — `receive_batch_with_tx` reads a batch while the same transaction
  UPSERTs each message into a sink table keyed by `(writer_id, seqno)` and bumps a
  hot row (topic → table). The commit advances the topic offset and writes the sink
  rows atomically, so a rolled-back tx re-reads and re-UPSERTs the same keys —
  idempotent, exactly-once.

TLI is induced on purpose via a few shared hot rows (`--tli-hot-keys`); the tx retry
loop absorbs it (`topic_tx_tli` counts the aborts, informational) and the run must
still finish with `topic_lost_errors == 0`. The topic and the sink/hot tables are
ref-scoped. See `TOPIC_TX_SCENARIO.md` for the full design; extra options:
`--messages-per-tx`, `--tli-hot-keys`, `--sink-table`, `--hot-table`.

## Collected metrics
- `oks`      - amount of OK requests
- `not_oks`  - amount of not OK requests
- `inflight` - amount of requests in flight
- `latency`  - summary of latencies in ms
- `attempts` - summary of amount for request

Metrics are collected for both table operations (`read`, `write`) and topic operations (`read`, `write`).

Topic workloads additionally emit (surfaced through `tests/slo/metrics-topic.yaml`, merged into the action metrics via `metrics_yaml_path`):
- `topic_e2e_latency_p50_ms` / `_p99_ms` — write → read latency of a delivered message (the meaningful topic latency; the generic `read_latency` mostly reflects `receive_message` wait time, not read cost, so it is kept **informational** for topics via `tests/slo/thresholds-topic.yaml` — `direction: neutral` — while `write_latency` stays gated)
- `topic_delivered_rps` — unique messages read back per second
- `topic_lost_errors` — messages detected as lost (must stay 0)
- `topic_duplicates` — redelivered messages (informational)

> Note: with Prometheus OTLP receiver (no Pushgateway) counters/histograms are cumulative and cannot be reset to `0`.
> If you need clean separation between runs, use distinct `REF`/`WORKLOAD` (and/or `SLO_INSTANCE_ID`) so each run writes into separate time series.

## Look at metrics in grafana
You can get dashboard used in that test [here](https://github.com/ydb-platform/slo-tests/blob/main/k8s/helms/grafana.yaml#L69) - you will need to import json into grafana.
