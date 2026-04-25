#!/usr/bin/env bash
set -euo pipefail

# Local SLO runner.
#
# This script:
#   1) clones / updates ydb-slo-action deploy configs
#   2) builds the workload image
#   3) starts everything via docker compose (YDB + Prometheus + workload)
#   4) tears down on exit
#
# The workload runs as the "workload-current" service from the compose file,
# configured via WORKLOAD_CURRENT_IMAGE and WORKLOAD_CURRENT_COMMAND env vars.
#
# Infra configs: https://github.com/ydb-platform/ydb-slo-action/tree/v2/deploy
#
# Configuration (env vars):
#   WORKLOAD_NAME   : workload type (default: topic)
#   RUN_TIME_SEC    : workload run time seconds (default: 120)
#   WRITE_RPS       : topic write rps (default: 1)
#   READ_THREADS    : topic read threads (default: 0)
#   WRITE_THREADS   : topic write threads (default: 1)
#   MESSAGE_SIZE    : topic message size bytes (default: 100)
#   REPORT_PERIOD_MS: metrics flush period ms (default: 1000)
#   DEBUG           : 1 to enable --debug for workload (default: 0)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

INFRA_DIR="${SCRIPT_DIR}/.infra"
INFRA_REPO="https://github.com/ydb-platform/ydb-slo-action.git"
INFRA_BRANCH="v2"

WORKLOAD_NAME="${WORKLOAD_NAME:-topic}"
RUN_TIME_SEC="${RUN_TIME_SEC:-120}"
WRITE_RPS="${WRITE_RPS:-1}"
READ_THREADS="${READ_THREADS:-0}"
WRITE_THREADS="${WRITE_THREADS:-1}"
MESSAGE_SIZE="${MESSAGE_SIZE:-100}"
REPORT_PERIOD_MS="${REPORT_PERIOD_MS:-1000}"
DEBUG="${DEBUG:-0}"

WORKLOAD_IMAGE="${WORKLOAD_IMAGE:-ydb-python-slo:local}"

# ---------------------------------------------------------------------------
# Infra management (ydb-slo-action/v2/deploy)
# ---------------------------------------------------------------------------

fetch_infra() {
  if [[ -d "${INFRA_DIR}/.git" ]]; then
    echo "[slo_runner] updating infra configs..."
    git -C "${INFRA_DIR}" fetch origin "${INFRA_BRANCH}" --depth 1 --quiet
    git -C "${INFRA_DIR}" -c advice.detachedHead=false checkout FETCH_HEAD --quiet
  else
    echo "[slo_runner] cloning infra configs (${INFRA_REPO} @ ${INFRA_BRANCH}, sparse: deploy/)..."
    git clone --no-checkout --depth 1 --branch "${INFRA_BRANCH}" --filter=blob:none "${INFRA_REPO}" "${INFRA_DIR}"
    git -C "${INFRA_DIR}" sparse-checkout init --cone
    git -C "${INFRA_DIR}" sparse-checkout set deploy
    git -C "${INFRA_DIR}" checkout "${INFRA_BRANCH}"
  fi
}

COMPOSE_FILE="${INFRA_DIR}/deploy/compose.yml"

build_workload_image() {
  echo "[slo_runner] building workload image: ${WORKLOAD_IMAGE} ..."
  docker build --platform linux/amd64 -f "${REPO_ROOT}/tests/slo/Dockerfile" -t "${WORKLOAD_IMAGE}" "${REPO_ROOT}"
}

# ---------------------------------------------------------------------------
# Build workload command
# ---------------------------------------------------------------------------

build_workload_command() {
  local cmd=(
    --workload-name "${WORKLOAD_NAME}"
    --report-period "${REPORT_PERIOD_MS}"
    --read-threads "${READ_THREADS}"
    --write-threads "${WRITE_THREADS}"
    --write-rps "${WRITE_RPS}"
    --message-size "${MESSAGE_SIZE}"
    --time "${RUN_TIME_SEC}"
  )
  if [[ "${DEBUG}" == "1" ]]; then
    cmd+=(--debug)
  fi
  echo "${cmd[*]}"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

fetch_infra
build_workload_image

echo "[slo_runner] starting infra + workload..."
echo "[slo_runner] workload image: ${WORKLOAD_IMAGE}"
echo "[slo_runner] workload name: ${WORKLOAD_NAME}"
echo "[slo_runner] run time: ${RUN_TIME_SEC}s"

export WORKLOAD_CURRENT_IMAGE="${WORKLOAD_IMAGE}"
export WORKLOAD_CURRENT_COMMAND="$(build_workload_command)"
export WORKLOAD_NAME
export WORKLOAD_DURATION="${RUN_TIME_SEC}"

COMPOSE="docker compose -f ${COMPOSE_FILE} --profile telemetry --profile workload-current"
trap '${COMPOSE} down' EXIT

echo "[slo_runner] starting infra..."
${COMPOSE} up -d --wait

prom_port=$(docker port ydb-prometheus 9090 2>/dev/null | head -1 || true)
if [[ -n "${prom_port}" ]]; then
  echo "[slo_runner] prometheus: http://${prom_port}"
fi

echo "[slo_runner] waiting for workload to finish..."
${COMPOSE} logs -f workload-current &
LOGS_PID=$!

exit_code=$(docker wait ydb-workload-current)

kill "${LOGS_PID}" 2>/dev/null || true
echo "[slo_runner] workload exited with code ${exit_code}"
exit "${exit_code}"
