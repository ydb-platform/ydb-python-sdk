# Topic-tx SLO scenario — transactional topic ↔ table pipeline

What the `sync-topic-tx` / `async-topic-tx` workloads do: an **exactly-once**
processing pipeline where both ends run inside a YDB transaction. Producers write
to the topic with a `tx_writer` (a transactional topic write); consumers read from
the topic with `receive_batch_with_tx` and, in the *same* transaction, UPSERT the
message into a sink table. The commit atomically advances the topic offset and
persists the sink rows — so every produced message lands in the sink table exactly
once, even while a chaos monkey keeps killing YDB nodes.

## Topology

```
   producer tx (transactional topic write)          per-ref topic: /Root/testdb/slo_topic_tx_<ref>
        │  tx_writer(tx).write(msg); commit          ┌──────────────────────────────────────────────┐
   w0 ──┼──produce p0──▶ partition 0 ────────────────▶│ p0: m1 m2 m3 …   (server-ordered per producer) │
   w1 ──┴──produce p1──▶ partition 1 ────────────────▶│ p1: m1 m2 m3 …                                 │
                                                      └───────────────────────┬──────────────────────┘
                                                                             │ one consumer group
                                   ┌──────────────────────────────────────────▼──────────────────────┐
                                   │ consumer tx: receive_batch_with_tx(tx) → decode → validate        │
                                   │              → UPSERT sink(writer_id, seqno); commit               │
                                   └───────────────────────────────────────────┬───────────────────────┘
                                  ▲                                             ▼  sink(writer_id, seqno) — exactly once
                   chaos-monkey: kills a YDB node every ~20-60s
```

Each message is self-describing: `writer_id : seqno : write_ts_ns : <padding>`
(same codec as the plain topic scenario, `jobs/topic_payload.py`).

## Flow (happy path + chaos)

```mermaid
sequenceDiagram
    autonumber
    participant W as Producer tx (tx_writer)
    participant S as YDB topic · partition i
    participant R as Consumer tx (receive_batch_with_tx)
    participant T as sink table
    participant M as Metrics (OTLP)

    Note over W: retry_tx: tx_writer.write(msgs), commit
    loop until --time
        W->>S: tx_writer.write(payload)   (buffered, flushed on commit)
        alt commit ok
            S-->>W: topic write committed
            Note right of W: seqno advances only on commit (no gap)
        else Unavailable (chaos)
            Note right of W: retry_tx re-runs callee; nothing persisted (no gap)
        end
    end

    loop drain as fast as messages arrive
        S-->>R: receive_batch_with_tx(tx)
        R->>T: UPSERT sink(writer_id, seqno) — keyed, idempotent
        alt commit ok
            R->>M: for each msg: delivered++, e2e = now - write_ts, validate seqno
            Note right of R: offset advance + sink rows committed atomically
        else Unavailable (chaos)
            R->>M: retry_tx re-reads from last committed offset
            Note right of R: rolled-back tx advanced no offset ⇒ re-processed, upsert idempotent
        end
    end
```

## Invariants we assert

| Signal | Meaning | Expectation |
|--------|---------|-------------|
| `topic_lost_errors` | forward gap in a producer's seqno (real loss) | **0** — hard-fails the run, under chaos |
| exactly-once into sink | sink keyed by `(writer_id, seqno)` — idempotent UPSERT | re-processing after a rollback creates no duplicate row |
| `topic_e2e_latency_p50/p99` | write-commit → read-commit latency | reported |
| `topic_duplicates` | redelivery after a rolled-back tx | informational (at-least-once at the app level) |
| `read/write_availability` | liveness under chaos | ~100% |

## Why it stays correct under chaos

- **The topic read and the table write share one transaction.** A consumer commit
  advances the topic offset *and* writes the sink row atomically; an abort (chaos)
  rolls back both. There is no window where one happened without the other.
- **seqno advances only after a successful commit** — an aborted/retried producer
  tx leaves no gap. Validation reads the seqno embedded in the payload, so a
  retried commit is at worst an app-level duplicate, never a false loss.
- **sink is keyed by `(writer_id, seqno)`** — a consumer tx that rolls back
  (chaos) re-reads the same messages from the last committed offset and
  re-UPSERTs the same keys: idempotent, so the table stays exactly-once.
- **validation runs only after the commit returns** — only durable offsets/rows
  feed the per-producer next-expected-seqno check (shared across readers, since a
  partition can move between them on rebalance).
- **per-ref topic + per-ref sink table** — the `current` and `baseline` containers
  run on the same cluster in parallel; ref-scoping keeps their validation from
  mixing.

## Not covered here

- Reading the sink table back for an independent full-table exactly-once audit
  (validation is the in-memory per-producer next-expected-seqno check, fed only by
  committed batches; the atomic offset+row commit makes that a faithful proxy).
- Snapshot/read-only tx modes — the pipeline runs serializable read-write.
- Deliberate non-retriable failures (SchemeError/BadRequest) — those are code/config
  bugs, out of scope for a liveness SLO.
