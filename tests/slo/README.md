# SLO workload

SLO is the type of test where app based on ydb-sdk is tested against falling YDB cluster nodes, tablets, network
(that is possible situations for distributed DBs with hundreds of nodes)

### Workload types:

There are two workload types:

- **Table SLO** - tests table operations (read/write)
- **Topic SLO** - tests topic operations (publish/consume)

### Implementations:

- `sync`
- `async` (now unimplemented)

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

### Run examples with all arguments:

**Table examples:**

table-create:
`python tests/slo/src/ table-create localhost:2136 /local -t tableName
--min-partitions-count 6 --max-partitions-count 1000 --partition-size 1 -с 1000
--write-timeout 10000`

table-cleanup:
`python tests/slo/src/ table-cleanup localhost:2136 /local -t tableName`

table-run:
`python tests/slo/src/ table-run localhost:2136 /local -t tableName
--prom-pgw http://prometheus-pushgateway:9091 --report-period 250
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
--prom-pgw http://prometheus-pushgateway:9091 --report-period 250
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

  --prom-pgw              <string> prometheus push gateway
  --report-period         <int>    prometheus push period in milliseconds

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

  --prom-pgw                      <string> prometheus push gateway
  --report-period                 <int>    prometheus push period in milliseconds

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
When running `topic-run` command, the program creates three jobs: `readJob`, `writeJob`, `metricsJob`.

- `readJob`    reads messages from topic using TopicReader and commits offsets
- `writeJob`   generates and publishes messages to topic using TopicWriter
- `metricsJob` periodically sends metrics to Prometheus

Messages contain:
- Sequential message ID
- Thread identifier
- Configurable payload size (padded with 'x' characters)

## Collected metrics
- `oks`      - amount of OK requests
- `not_oks`  - amount of not OK requests
- `inflight` - amount of requests in flight
- `latency`  - summary of latencies in ms
- `attempts` - summary of amount for request

Metrics are collected for both table operations (`read`, `write`) and topic operations (`read`, `write`).

> You must reset metrics to keep them `0` in prometheus and grafana before beginning and after ending of jobs

## Look at metrics in grafana
You can get dashboard used in that test [here](https://github.com/ydb-platform/slo-tests/blob/main/k8s/helms/grafana.yaml#L69) - you will need to import json into grafana.
