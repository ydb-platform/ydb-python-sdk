# OpenTelemetry example (YDB Python SDK)

Async demo in [`otel_example.py`](otel_example.py): OTLP export, `enable_tracing()`,
`enable_metrics()`, `app_startup` and `example_tli` application spans, SDK client
metrics, bank table, Serializable transactions (TLI-style load), and an explicitly
named topic Reader that emits `ydb.topic.reader.received.messages`,
`ydb.topic.reader.received.bytes`, `ydb.topic.reader.delivered.messages`,
`ydb.topic.reader.compression.duration`,
`ydb.topic.reader.message.processing.duration`,
`ydb.topic.reader.commit.queued`,
`ydb.topic.reader.commit.acknowledged`,
`ydb.topic.reader.commit_offset.lag.max`,
`ydb.topic.reader.session.errors`,
`ydb.topic.reader.credit_balance_bytes`,
`ydb.topic.reader.local_buffer.messages`,
`ydb.topic.reader.local_buffer.message_age.max`, and
`ydb.topic.reader.partition_session.count`.

## Topic Reader metrics in the example

The demo enables metrics before creating the Reader and supplies
`reader_name="otel-example-reader"`. It creates a unique topic for the run, deletes only
that topic during cleanup, then writes and reads one message, producing:

- `ydb.topic.reader.received.messages`: the number of messages received before
  decoding, split by `topic`;
- `ydb.topic.reader.received.bytes`: the total `ReadResponse.bytes_size` received by
  that logical Reader, without a `topic` label because one response can contain data
  from several topics;
- `ydb.topic.reader.delivered.messages`: the number of messages returned by
  `receive_message`, `receive_batch`, or `receive_batch_with_tx`, split by `topic`;
- `ydb.topic.reader.compression.duration`: seconds spent decompressing each non-RAW
  message, excluding decoder-executor queueing, split by `topic`, `codec`, and
  `outcome`;
- `ydb.topic.reader.message.processing.duration`: seconds from receipt until each
  non-RAW message's batch is ready for delivery, including decoder queueing and split
  by `topic`, `codec`, and `outcome`;
- `ydb.topic.reader.commit.queued`: messages in commit ranges accepted by the SDK,
  counted as `range.end - range.start` and split by `topic`;
- `ydb.topic.reader.commit.acknowledged`: monotonic committed-offset advances reported
  by regular acknowledgements, plus ranges from successful transaction commits, split
  by `topic`;
- `ydb.topic.reader.commit_offset.lag.max`: the largest gap between a regular stream
  commit request's end offset and the acknowledged offset across active partitions,
  split by `topic`;
- `ydb.topic.reader.session.errors`: failed sessions or connection attempts, split by
  `retry_decision=retry|stop`, `status_code`, and `error.type`; normal shutdown is not
  counted and `topic` is omitted;
- `ydb.topic.reader.credit_balance_bytes`: protocol byte credit granted to the server
  and not yet consumed by read responses; `0` between stream sessions and without
  `topic`;
- `ydb.topic.reader.local_buffer.messages`: the current number of messages retained by
  the logical Reader, including decoding and ready-to-deliver queues, without `topic`;
- `ydb.topic.reader.local_buffer.message_age.max`: the age in seconds of the oldest
  retained message, or `0` when the buffer is empty, without `topic`;
- `ydb.topic.reader.partition_session.count`: the current number of active partition
  sessions, split by `topic` and without a `partition` label; configured topics report
  `0` before their first session starts.

All thirteen metrics also carry `endpoint`, `database`, and `reader.name`; `consumer` is
included for consumer-based reads. They remain attached to the same logical Reader
across stream reconnects. Use the rate of the cumulative counters to compare incoming
traffic with messages visible to the application, and read the observable instruments
as current values.

The example keeps the message buffered, then keeps the empty Reader open, for
`OTEL_TOPIC_BUFFER_OBSERVATION_SECONDS` seconds in each state. Its default is 7 seconds,
which is longer than this stack's 5-second Prometheus scrape interval, so both the
positive and zero gauge samples are observable.

[`load_tank.py`](load_tank.py) runs a small step-like load profile for the
metrics dashboard:

```text
Peak RPS -> Medium RPS -> Min RPS -> Medium RPS -> repeat
```

The same process also creates a temporary multi-partition topic and keeps a named
Reader and writer active for the whole run. By default the writer produces 20 messages
per second while the Reader deliberately pauses for 0.1 seconds per message. This
creates a visible, bounded SDK-side prefetch buffer and continuously exercises all
Topic Reader counters, histograms, and gauges. A short Reader against a deliberately missing topic
emits the deterministic `session.errors{retry_decision="stop"}` case without
interrupting the main stream. A synthetic transient `ABORTED` probe exercises real
multi-attempt retry metrics without changing the database.

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

To turn this into an automated e2e check, start the stack in the background and run
the verifier. It waits up to three minutes for every SDK metric, including the topic
error probe, to carry the expected non-zero activity in Prometheus. The retry check
also requires at least one operation with more than one attempt. The verifier reads
the current load-generator run ID from the shared Compose volume and only accepts
series carrying that `service.instance.id`, so metrics left by an older run cannot
make the check pass:

```sh
docker compose -f examples/opentelemetry/compose-e2e.yaml up --build -d
docker compose -f examples/opentelemetry/compose-e2e.yaml --profile verify run --rm metrics-verifier
```

The verifier returns exit code `1` and prints the missing Prometheus series if the
contract is incomplete. Run it directly against another Prometheus instance with:

```sh
python examples/opentelemetry/verify_metrics.py \
    --prometheus-url http://localhost:9090 \
    --service-instance-id <load-tank-run-id> \
    --require-error-probe
```

Use the value printed as `run_id` by `load_tank.py`, or set `LOAD_TANK_RUN_ID`
explicitly before starting it. The verifier requires either `--service-instance-id`
or `--run-id-file`; it never searches unscoped historical series.

Grafana is provisioned with the **YDB Python SDK Metrics** dashboard. It uses
Prometheus queries for SDK metrics such as `ydb_client_operation_duration`,
`ydb_client_operation_failed`, `ydb_query_session_count`,
`ydb_query_session_pending_requests`, `ydb_query_session_create_time`, and
`ydb_client_retry_duration`. The example also publishes the topic Reader received and
delivered message counters by topic, the reader-level received-byte counter, and the
reader-level local-buffer count and oldest-age gauges. It also publishes commit-queued
and commit-acknowledged messages, commit-offset lag, and the active partition-session
count by topic, the reader-level credit balance, and message processing/decompression
latency histograms. Use Grafana Explore for ad-hoc traces through Tempo and metrics
through Prometheus.

In Grafana Explore, select the Prometheus data source and query:

```promql
ydb_topic_reader_local_buffer_messages{reader_name="otel-example-reader"}
```

The oldest buffered-message age is available as:

```promql
ydb_topic_reader_local_buffer_message_age_max_seconds{reader_name="otel-example-reader"}
```

Active partition sessions are available as:

```promql
ydb_topic_reader_partition_session_count{reader_name="otel-example-reader"}
```

The current byte credit granted to the server is available as:

```promql
ydb_topic_reader_credit_balance_bytes{reader_name="otel-example-reader"}
```

The six counters use Prometheus' conventional `_total` suffix, for example:

```promql
ydb_topic_reader_received_messages_total{reader_name="otel-example-reader"}
```

Commit ranges accepted by the Reader are available as:

```promql
ydb_topic_reader_commit_queued_total{reader_name="otel-example-reader"}
```

Successfully acknowledged commit ranges are available as:

```promql
ydb_topic_reader_commit_acknowledged_total{reader_name="otel-example-reader"}
```

The maximum outstanding commit-offset gap is available as:

```promql
ydb_topic_reader_commit_offset_lag_max{reader_name="otel-example-reader"}
```

The p95 time from message receipt until the decoded batch is ready is available as:

```promql
histogram_quantile(0.95,
  sum by (le, reader_name, topic, codec, outcome) (
    rate(ydb_topic_reader_message_processing_duration_seconds_bucket[$__rate_interval])
  )
)
```

The p95 time spent inside the decompressor is available as:

```promql
histogram_quantile(0.95,
  sum by (le, reader_name, topic, codec, outcome) (
    rate(ydb_topic_reader_compression_duration_seconds_bucket[$__rate_interval])
  )
)
```

Session errors appear only after a failed session or connection attempt:

```promql
ydb_topic_reader_session_errors_total{reader_name="load-tank-topic-error-probe", retry_decision="stop"}
```

The SDK configures explicit OpenTelemetry histogram bucket boundaries for its
own duration and retry-attempt metrics. Duration values are recorded in seconds,
with sub-millisecond and millisecond-scale buckets so Grafana percentiles show
meaningful latency distributions for fast local YDB operations.

Metrics are wired through a dedicated SDK metrics plugin. Until `enable_metrics()`
is called, the SDK uses a no-op metrics registry and does not import
OpenTelemetry metrics packages from the hot-path metric helpers.

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
| `LOAD_TANK_RUN_ID` | optional stable `service.instance.id`; a random ID is used for each run |
| `LOAD_TANK_RUN_ID_FILE` | optional file to which the load tank atomically publishes its run ID |
| `LOAD_TANK_READY_FILE` | optional readiness marker created after YDB and the error probe succeed |
| `METRICS_SERVICE_INSTANCE_ID` | run ID selected by `verify_metrics.py` |
| `METRICS_RUN_ID_FILE` | file from which `verify_metrics.py` reads the selected run ID |
| `OTEL_TOPIC_BUFFER_OBSERVATION_SECONDS` | seconds to expose each buffer-gauge state, default `7` |
| `LOAD_TANK_TOTAL_TIME` | total load duration in seconds, default `300`; Compose uses `6000` |
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
| `LOAD_TANK_RETRY_PROBE_INTERVAL` | interval between deterministic retry probes, default `5.0`; set `0` to disable |
| `LOAD_TANK_RETRY_PROBE_FAILURES` | transient `ABORTED` attempts before success, default `2` |
| `LOAD_TANK_TOPIC_WRITE_RPS` | topic producer rate, default `20`; set `0` to disable topic load |
| `LOAD_TANK_TOPIC_READ_DELAY` | delay after each topic message, default `0.1` seconds           |
| `LOAD_TANK_TOPIC_MESSAGE_SIZE` | topic payload size, default `1024` bytes                       |
| `LOAD_TANK_TOPIC_PARTITIONS` | temporary topic partition count, default `2`                    |
| `LOAD_TANK_TOPIC_READER_NAME` | stable Reader metric label, default `load-tank-topic-reader`   |
| `LOAD_TANK_TOPIC_ERROR_PROBE_ENDPOINT` | endpoint used for a missing-topic error probe; defaults to `YDB_ENDPOINT` |
| `LOAD_TANK_TOPIC_ERROR_PROBE_SECONDS` | probe duration, default `0`; Compose sets it to `5`         |
| `LOAD_TANK_PEAK_DURATION` | peak phase duration in seconds, default `60`             |
| `LOAD_TANK_MEDIUM_DURATION` | medium phase duration in seconds, default `90`           |
| `LOAD_TANK_MIN_DURATION` | low phase duration in seconds, default `60`              |
| `LOAD_TANK_QUERY` | query executed by workers, default `SELECT 1 AS value`   |
| `LOAD_TANK_ERROR_QUERY` | query used to produce failed-operation metrics           |

## Load-test recipes

Run only the infrastructure first, then start one or more isolated load-generator
containers with overrides. This makes test duration and intensity explicit and keeps
Grafana available after a run:

```sh
docker compose -f examples/opentelemetry/compose-e2e.yaml up -d \
    ydb otel-collector prometheus tempo grafana

# Five-minute smoke/load run.
docker compose -f examples/opentelemetry/compose-e2e.yaml run --rm \
    -e LOAD_TANK_TOTAL_TIME=300 \
    -e LOAD_TANK_PEAK_RPS=200 \
    -e LOAD_TANK_WORKERS=80 \
    load-generator
```

Useful scenarios:

- **Throughput staircase:** increase `PEAK_RPS` until achieved RPS stops following the
  target or p95/p99 latency bends sharply.
- **Pool saturation:** keep `LOAD_TANK_PRESSURE_POOL_SIZE=1`, increase
  `LOAD_TANK_PRESSURE_WORKERS`, and watch pending requests and acquire timeouts.
- **Retries:** increase `LOAD_TANK_RETRY_PROBE_FAILURES` and watch retry-attempt count,
  average attempts, retrying calls, and retry duration.
- **Topic backpressure:** make `1 / LOAD_TANK_TOPIC_READ_DELAY` lower than
  `LOAD_TANK_TOPIC_WRITE_RPS`; the local-buffer count and oldest-message age should
  rise while received and delivered rates diverge.
- **Balanced topic stream:** set read capacity above write RPS; the buffer and age
  should return close to zero while received and delivered rates converge.
- **Reconnect/chaos:** use the repository's `tests/slo` multi-node chaos setup for a
  long run. The Reader session-error counter should grow while message delivery
  resumes; do not restart this example's single in-memory YDB merely to create an
  error sample.

For repeatable comparison, change one dimension at a time, warm up before measuring,
keep a fixed measurement window, and record offered RPS, achieved RPS, p50/p95/p99,
error rate, retry ratio, pool saturation, and topic receive/delivery lag.
