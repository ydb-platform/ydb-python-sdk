# Topic-tx SLO scenario — both-ends transactional topic ↔ table pipeline

What the `sync-topic-tx` / `async-topic-tx` workloads do: an **exactly-once**
processing pipeline where **both** ends run inside a YDB transaction. Producers
write to the topic in a `tx_writer` transaction that also touches a table;
consumers read from the topic with `receive_batch_with_tx` and, in the *same*
transaction, UPSERT the message into a sink table. The commit atomically advances
the topic offset and persists the table rows — so every produced message lands in
the sink table exactly once, even while a chaos monkey keeps killing YDB nodes.

On top of the connection breaks, we **deliberately induce TLI**
(`ydb.Aborted`, "transaction locks invalidated" — the штатный optimistic-lock
conflict) with a small set of shared hot rows. The tx retry loop must absorb both
failure modes and still deliver exactly once.

## Topology

```
   contention table (few hot rows)                      per-ref topic: /Root/testdb/slo_topic_tx_<ref>
   ┌─────────────────────────────┐                      ┌──────────────────────────────────────────────┐
   │ hot[0] hot[1] … hot[K-1]     │◀──read-modify-write──│ p0: m1 m2 m3 …   (server-ordered per producer) │
   └─────────────────────────────┘        (TLI)         │ p1: m1 m2 m3 …                                 │
        ▲ producer tx (table → topic)                   └───────────────────────┬──────────────────────┘
        │  tx_writer(tx).write(msg) + bump hot[k]                                │ one consumer group
        │  commit ⇒ topic write + table update atomic                           │
   w0 ──┘                                          consumer tx (topic → table)   │
                                     ┌──────────────────────────────────────────▼──────────────────────┐
                                     │ receive_batch_with_tx(tx) → decode → validate → UPSERT sink       │
                                     │ + bump hot[k];  commit ⇒ offset advance + sink rows atomic         │
                                     └───────────────────────────────────────────────────────────────────┘
                                  ▲                                    │
                   chaos-monkey: kills a YDB node every ~20-60s        ▼  sink(writer_id, seqno) — exactly once
```

Each message is self-describing: `writer_id : seqno : write_ts_ns : <padding>`
(same codec as the plain topic scenario, `jobs/topic_payload.py`).

## Flow (happy path + chaos + TLI)

```mermaid
sequenceDiagram
    autonumber
    participant W as Producer tx (tx_writer)
    participant H as hot[k] (contention row)
    participant S as YDB topic · partition i
    participant R as Consumer tx (receive_batch_with_tx)
    participant T as sink table
    participant M as Metrics (OTLP)

    Note over W: retry_tx: read+bump hot[k], write msgs, commit
    loop until --time
        W->>H: SELECT val / UPSERT val+1  (takes optimistic lock)
        W->>S: tx_writer.write(payload)   (buffered, flushed on commit)
        alt commit ok
            S-->>W: topic write + table update committed atomically
            Note right of W: seqno advances only on commit (no gap)
        else Aborted (TLI) or Unavailable (chaos)
            Note right of W: retry_tx re-runs callee; nothing persisted (no gap)
        end
    end

    loop drain as fast as messages arrive
        S-->>R: receive_batch_with_tx(tx)
        R->>H: SELECT val / UPSERT val+1  (takes optimistic lock)
        R->>T: UPSERT sink(writer_id, seqno) — keyed, idempotent
        alt commit ok
            R->>M: for each msg: delivered++, e2e = now - write_ts, validate seqno
            Note right of R: offset advance + sink rows committed atomically
        else Aborted (TLI) or Unavailable (chaos)
            R->>M: tli++ (if Aborted); retry_tx re-reads from last committed offset
            Note right of R: rolled-back tx advanced no offset ⇒ re-processed, upsert idempotent
        end
    end
```

## Invariants we assert

| Signal | Meaning | Expectation |
|--------|---------|-------------|
| `topic_lost_errors` | forward gap in a producer's seqno (real loss) | **0** — hard-fails the run, under chaos **and** TLI |
| exactly-once into sink | sink keyed by `(writer_id, seqno)` — idempotent UPSERT | re-processing after a rollback creates no duplicate row |
| `topic_tx_tli` | TLI aborts absorbed by the retry loop | > 0 (proves the mechanism fires) — informational |
| `topic_e2e_latency_p50/p99` | write-commit → read-commit latency | reported |
| `topic_duplicates` | redelivery after a rolled-back tx | informational (at-least-once at the app level) |
| `read/write_availability` | liveness under chaos | ~100% |

## Why it stays correct under chaos + TLI

- **The topic op and the table op share one transaction.** A commit advances the
  topic offset *and* writes the table row atomically; an abort (chaos or TLI)
  rolls back both. There is no window where one happened without the other.
- **seqno advances only after a successful commit** — an aborted/retried producer
  tx leaves no gap. Validation reads the seqno embedded in the payload, so a
  retried commit is at worst an app-level duplicate, never a false loss.
- **sink is keyed by `(writer_id, seqno)`** — a consumer tx that rolls back
  (TLI/chaos) re-reads the same messages from the last committed offset and
  re-UPSERTs the same keys: idempotent, so the table stays exactly-once.
- **TLI is retriable** (`ydb/_errors.py`, slow backoff) and counted via
  `RetrySettings.on_ydb_error_callback`; `retry_tx_*` absorbs it transparently.
- **validation runs only after the commit returns** — only durable offsets/rows
  feed the per-producer next-expected-seqno check (shared across readers, since a
  partition can move between them on rebalance).
- **per-ref topic + per-ref sink/hot tables** — the `current` and `baseline`
  containers run on the same cluster in parallel; ref-scoping keeps their
  validation and their hot-row contention from mixing.

## Inducing TLI on purpose

Both the producer and consumer transactions do a read-modify-write
(`SELECT val` / `UPSERT val+1`) on one of `--tli-hot-keys` shared hot rows
(chosen by `writer_id % hot_keys` / `reader_id % hot_keys`). The read takes an
optimistic lock, so concurrent transactions on the same key conflict on commit and
one gets `ydb.Aborted` (TLI). Keep the hot-key count small for frequent conflicts,
larger to make them rare. The hot table doubles as the producer's "table side" of
the table → topic transaction.

## Not covered here

- Reading the sink table back for an independent full-table exactly-once audit
  (validation is the in-memory per-producer next-expected-seqno check, fed only by
  committed batches; the atomic offset+row commit makes that a faithful proxy).
- Snapshot/read-only tx modes — the pipeline runs serializable read-write.
- Deliberate non-retriable failures (SchemeError/BadRequest) — those are code/config
  bugs, out of scope for a liveness SLO.
