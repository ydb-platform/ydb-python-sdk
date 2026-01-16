#!/usr/bin/env bash
set -euo pipefail

# Local SLO runner.
#
# This script:
#   1) checks that the infra docker network exists (default: ydb_cluster)
#   2) builds the workload image
#   3) runs topic-create + topic-run inside that network
#
# Why it runs the workload as a container:
# - infra compose does not necessarily publish YDB/Prometheus ports to localhost
# - attaching to the compose network makes service discovery reliable (DNS)
#
# Configuration (env vars):
#   NETWORK_NAME    : docker network to attach workload container to (default: ydb_cluster)
#   YDB_ENDPOINT    : grpc endpoint inside the network (default: grpc://ydb-storage-1:2136)
#   YDB_DATABASE    : database (default: /Root/testdb)
#   TOPIC_PATH      : topic path (default: /Root/testdb/slo_topic)
#   OTLP_ENDPOINT   : Prometheus OTLP receiver URL (default: http://prometheus:9090/api/v1/otlp/v1/metrics)
#   RUN_TIME_SEC    : workload run time seconds (default: 120)
#   WRITE_RPS       : topic write rps (default: 1)
#   READ_THREADS    : topic read threads (default: 0)
#   WRITE_THREADS   : topic write threads (default: 1)
#   MESSAGE_SIZE    : topic message size bytes (default: 100)
#   REPORT_PERIOD_MS: metrics flush period ms (default: 1000)
#   DEBUG           : 1 to enable --debug for workload (default: 0)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

NETWORK_NAME="${NETWORK_NAME:-ydb_cluster}"

YDB_DATABASE="${YDB_DATABASE:-/Root/testdb}"
TOPIC_PATH="${TOPIC_PATH:-${YDB_DATABASE}/slo_topic}"

OTLP_ENDPOINT="${OTLP_ENDPOINT:-http://prometheus:9090/api/v1/otlp/v1/metrics}"
RUN_TIME_SEC="${RUN_TIME_SEC:-120}"
WRITE_RPS="${WRITE_RPS:-1}"
READ_THREADS="${READ_THREADS:-0}"
WRITE_THREADS="${WRITE_THREADS:-1}"
MESSAGE_SIZE="${MESSAGE_SIZE:-100}"
REPORT_PERIOD_MS="${REPORT_PERIOD_MS:-1000}"
DEBUG="${DEBUG:-0}"

WORKLOAD_IMAGE="${WORKLOAD_IMAGE:-ydb-python-slo:local}"

# Infra configuration
#
# Infra is expected to be started separately (see https://github.com/ydb-platform/ydb-slo-action/tree/main/deploy).
# This runner only attaches the workload container to the existing docker network "${NETWORK_NAME}".
YDB_ENDPOINT="${YDB_ENDPOINT:-grpc://ydb-storage-1:2136}"

ensure_network() {
  if docker network inspect "${NETWORK_NAME}" >/dev/null 2>&1; then
    return 0
  fi

  echo "[slo_runner] docker network '${NETWORK_NAME}' not found." >&2
  echo "[slo_runner] Start infra and ensure it creates/uses this network, then re-run." >&2
  echo "[slo_runner] Infra configs: https://github.com/ydb-platform/ydb-slo-action/tree/main/deploy" >&2
  exit 2
}

workload_run() {
  # Runs workload as a container attached to the infra compose network.
  # Usage:
  #   workload_run <subcommand> <args...>
  docker run --rm --network "${NETWORK_NAME}" "${WORKLOAD_IMAGE}" "$@"
}

build_workload_image() {
  docker build -f "${REPO_ROOT}/tests/slo/Dockerfile" -t "${WORKLOAD_IMAGE}" "${REPO_ROOT}"
}

echo "[slo_runner] repo root: ${REPO_ROOT}"
echo "[slo_runner] compose network: ${NETWORK_NAME}"
echo "[slo_runner] ydb endpoint: ${YDB_ENDPOINT}"
echo "[slo_runner] ydb db: ${YDB_DATABASE}"
echo "[slo_runner] topic path: ${TOPIC_PATH}"
echo "[slo_runner] otlp endpoint: ${OTLP_ENDPOINT}"
echo "[slo_runner] checking docker network: ${NETWORK_NAME}..."
ensure_network
echo "[slo_runner] building workload image: ${WORKLOAD_IMAGE} ..."
build_workload_image

echo "[slo_runner] topic-create..."
topic_create_args=(
  topic-create
  "${YDB_ENDPOINT}"
  "${YDB_DATABASE}"
  --path "${TOPIC_PATH}"
)
if [[ "${DEBUG}" == "1" ]]; then
  topic_create_args+=(--debug)
fi
workload_run "${topic_create_args[@]}"

echo "[slo_runner] topic-run..."
topic_run_args=(
  topic-run
  "${YDB_ENDPOINT}"
  "${YDB_DATABASE}"
  --path "${TOPIC_PATH}"
  --otlp-endpoint "${OTLP_ENDPOINT}"
  --report-period "${REPORT_PERIOD_MS}"
  --read-threads "${READ_THREADS}"
  --write-threads "${WRITE_THREADS}"
  --write-rps "${WRITE_RPS}"
  --message-size "${MESSAGE_SIZE}"
  --time "${RUN_TIME_SEC}"
)
if [[ "${DEBUG}" == "1" ]]; then
  topic_run_args+=(--debug)
fi
workload_run "${topic_run_args[@]}"

echo "[slo_runner] done"
