#!/bin/sh
# Workload entrypoint used by ydb-slo-action v2.
#
# The action launches the same image for both `current` and `baseline` workloads
# in parallel; both must be able to schema-prepare and then run.
#
# Inputs come from the env vars injected by the action:
#   WORKLOAD_NAME       sync-table | sync-query | async-query | sync-topic | async-topic
#   WORKLOAD_DURATION   run duration in seconds
#   YDB_ENDPOINT        grpc://ydb:2136
#   YDB_DATABASE        /Root/testdb
#
# The sync/async execution mode is derived from the WORKLOAD_NAME label itself
# (an `async-*` label runs the async path); no extra flag is needed here.
#
# Anything passed after the script name is appended to the `*-run` command —
# this is how tuning flags from `workload_current_command` (e.g. --read-rps)
# reach the workload.

set -e

case "${WORKLOAD_NAME:-sync-query}" in
    sync-table|sync-query|async-query) PREFIX=table ;;
    topic|sync-topic|async-topic) PREFIX=topic ;;
    *)
        echo "Unknown WORKLOAD_NAME: ${WORKLOAD_NAME}" >&2
        exit 1
        ;;
esac

ENDPOINT="${YDB_ENDPOINT:-grpc://localhost:2136}"
DATABASE="${YDB_DATABASE:-/local}"
DURATION="${WORKLOAD_DURATION:-600}"

# Topic paths must live under the database; derive one from $DATABASE so the
# same image works against both local (/local) and CI (/Root/testdb) databases.
# Scope the topic by ref so the current and baseline containers (same cluster,
# run in parallel) don't share a topic — otherwise their readers/producers would
# cross-contaminate delivery/ordering validation.
EXTRA_ARGS=""
if [ "$PREFIX" = "topic" ]; then
    REF_RAW="${WORKLOAD_REF:-${REF:-main}}"
    SAFE_REF=$(printf '%s' "$REF_RAW" | tr -c 'a-zA-Z0-9_' '_')
    EXTRA_ARGS="--path ${DATABASE%/}/slo_topic_${SAFE_REF}"
fi

if [ "$PREFIX" = "table" ]; then
    TABLE_NAME="key_value_$(python -c 'import uuid; print(uuid.uuid4().hex)')"
    python ./tests/slo/src table-create "$ENDPOINT" "$DATABASE" --table-name "$TABLE_NAME"
    exec python -c '
import signal
import subprocess
import sys

table, endpoint, database, duration = sys.argv[1:5]
common = [sys.executable, "./tests/slo/src"]
workload = subprocess.Popen([
    *common, "table-run", endpoint, database, "--time", duration,
    *sys.argv[5:], "--table-name", table,
])
for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGQUIT):
    signal.signal(signum, lambda received, _frame: workload.send_signal(received))
try:
    status = workload.wait()
finally:
    cleanup = subprocess.run([
        *common, "table-cleanup", endpoint, database, "--table-name", table,
    ], check=False)
    if cleanup.returncode:
        print("WARN: table cleanup failed", file=sys.stderr)
sys.exit(status if status >= 0 else 128 - status)
' "$TABLE_NAME" "$ENDPOINT" "$DATABASE" "$DURATION" "$@"
fi

# Topic schema preparation retains its existing behavior.
python ./tests/slo/src "${PREFIX}-create" "$ENDPOINT" "$DATABASE" $EXTRA_ARGS \
    || echo "WARN: ${PREFIX}-create exited non-zero (treated as already-prepared)" >&2

exec python ./tests/slo/src \
    "${PREFIX}-run" "$ENDPOINT" "$DATABASE" \
    --time "$DURATION" \
    $EXTRA_ARGS \
    "$@"
