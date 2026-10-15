# Concurrent transactional RMW

`async-query-rmw` is a separate SLO scenario. It uses only the asynchronous
Query service adapter (`ydb.aio.QuerySessionPool` and
`QuerySession.transaction(ydb.QuerySerializableReadWrite())`). Sync Query,
Table service and Topic are not RMW adapters.

Use the existing image entrypoint with `WORKLOAD_NAME=async-query-rmw`, or run:

```sh
python tests/slo/src rmw-run grpc://localhost:2136 /local \
  --time 60 --write-threads 4 --counter-count 2 \
  --otlp-endpoint http://localhost:9090/api/v1/otlp/v1/metrics
```

The command creates two tables named `slo_rmw_<process-unique UUID>_counters`
and `slo_rmw_<same UUID>_ledger` inside the selected database, initializes
zero-valued counters, runs, validates and drops only tables whose creation
succeeded. There is no
separate startup process, create command or cross-process namespace to carry.
Current, baseline and overlapping runs use different tables even with the same
ref. The existing consuming workflow overlays the same SLO harness on the
baseline checkout while retaining each checkout's SDK and its own Dockerfile.

Each round admits one operation per writer against a shared counter. Rounds
alternate counters. All admitted calls settle before the next round; this
prevents a fast writer from starving peers that are retrying. IDs are allocated
before the SDK retry callback, and each operation has an independently retained
counter, delta and payload. A serializable transaction reads that ID's ledger
record first. An exact replay is a no-op; a conflicting replay fails. A new
operation reads the counter, increments its value and version, inserts the
ledger record and commits atomically. Streams are consumed before commit and
each callback owns its session and transaction.

Admission stops on duration, SIGINT, SIGTERM or a final error. It does not cancel
admitted SDK calls. After they settle, a new serializable transaction reads all
counters and ledger rows. Validation requires the exact admitted ID/counter/
delta/payload set, no duplicate IDs, every expected counter, and exact per-counter
value and version. This detects sum-preserving lost writes and a coherently
missing operation as well as corrupted data. The first final transaction error
wins over validation, metrics and cleanup errors.

Write/read request timeout defaults remain 20/10 seconds, with the same
idempotent retry settings and session-acquisition budgets as the existing async
Query workload. SDK retry limits, backoff and driver deadlines are not changed.
`--time` bounds admission, not settlement; in-flight calls retain their SDK
operation budgets. Existing `read`/`write` operation and retry-attempt metrics
are used unchanged. A write metric represents one logical operation. Its
technical attempts include session checkout failures before the transaction
body, using the existing public SDK retry helper with the same settings and
pooled session lifecycle. The independent final check is a read operation.

Deterministic regression coverage:

```sh
python -m pytest -q tests/table/test_tx.py::TestSloRmwData
```

The tests execute production Apply/Run/Validate through the actual SDK
retry helper and a transactional store seam. Their controlled conflicts and
post-commit error simulate retry/acknowledgement behavior; they are not proof of
a real transport-level ambiguous commit. Native database and CI receipts belong
to the release verification, not to this deterministic test claim.
