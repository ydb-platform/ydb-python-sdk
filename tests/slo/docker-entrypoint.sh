#!/bin/sh
# Workload entrypoint used by ydb-slo-action v2.
#
# The action launches the same image for both `current` and `baseline` workloads
# in parallel; both must be able to schema-prepare and then run.
#
# Inputs come from the env vars injected by the action:
#   WORKLOAD_NAME       sync-table | sync-query | topic
#   WORKLOAD_DURATION   run duration in seconds
#   YDB_ENDPOINT        grpc://ydb:2136
#   YDB_DATABASE        /Root/testdb
#
# Anything passed after the script name is appended to the `*-run` command —
# this is how tuning flags from `workload_current_command` (e.g. --read-rps)
# reach the workload.

set -e

case "${WORKLOAD_NAME:-sync-query}" in
    sync-table|sync-query) PREFIX=table ;;
    topic) PREFIX=topic ;;
    *)
        echo "Unknown WORKLOAD_NAME: ${WORKLOAD_NAME}" >&2
        exit 1
        ;;
esac

ENDPOINT="${YDB_ENDPOINT:-grpc://localhost:2136}"
DATABASE="${YDB_DATABASE:-/local}"
DURATION="${WORKLOAD_DURATION:-600}"

# Schema prep is idempotent at the SDK level for topics; for tables, a parallel
# baseline container may race and fail with "already exists" — tolerate it.
python ./tests/slo/src "${PREFIX}-create" "$ENDPOINT" "$DATABASE" \
    || echo "WARN: ${PREFIX}-create exited non-zero (treated as already-prepared)" >&2

exec python ./tests/slo/src \
    "${PREFIX}-run" "$ENDPOINT" "$DATABASE" \
    --time "$DURATION" \
    "$@"
