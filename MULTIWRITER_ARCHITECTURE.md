# Topic multi-partition writer — architecture

How write-by-key is built, why each piece is the way it is, and what breaks if it is built
differently. Written from the Python implementation, but deliberately language-agnostic: it
describes the protocol interactions and the state machine, not the API.

Cross-checked against the two existing implementations — C++ `TProducer`
(`src/client/topic/impl/producer.{h,cpp}`) and Go `topicmultiwriter`
(`internal/topic/topicmultiwriter`). Differences are called out where they exist.

---

## 1. What it is

A **multi-writer** is one logical writer that spreads messages over all partitions of a topic
while keeping per-key ordering. The caller attaches a **key** to each message; the writer decides
which partition owns that key and writes there.

The reason it exists is server-side auto-partitioning: the server splits a partition when it gets
hot. A plain writer targets one partition and simply dies when that partition goes away. The
multi-writer follows the topology instead.

```
                 write(key="user-42", data=...)
                              │
                              ▼
                  ┌───────────────────────┐
                  │      orchestrator     │   routing, seqno, in-flight ownership,
                  │                       │   repartition handling
                  └───────────┬───────────┘
            route by key      │      one sub-writer per partition
        ┌──────────────┬──────┴───────┬──────────────┐
        ▼              ▼              ▼              ▼
   sub-writer     sub-writer     sub-writer     sub-writer
   partition 0    partition 1    partition 2    partition N
   producer       producer       producer       producer
   "pfx-0"        "pfx-1"        "pfx-2"        "pfx-N"
        │              │              │              │
        ▼              ▼              ▼              ▼
     independent write stream per partition
     (own buffering, encoding, reconnect, token refresh)
```

The sub-writer is an **ordinary single-partition writer**, unmodified. The orchestrator adds
routing, sequence numbering and repartition handling on top. This is the single most important
structural decision: buffering, compression, reconnection and auth refresh are not reimplemented.

> Why this lives in the client at all. Routing by key was originally meant to be a server feature:
> the client would attach a `message_group_id` to each message and the server would spread the
> groups across partitions itself. The protocol still carries that plan — `message_group_id` exists
> both as a session-level setting and, in `MessageData.partitioning`, as a per-message one, which
> only makes sense if the server was going to do the routing. It never shipped, so every SDK does
> the routing on the client instead, and the multi-writer is that work.
>
> The practical consequence: **treat `message_group_id` as another name for the producer id.** Every
> implementation sets the two to the same value, nothing routes by it, and the key you attach to a
> message has nothing to do with it. It is not a second identity to reason about.

---

## 2. The contract

What a caller may rely on:

| # | Guarantee |
|---|---|
| 1 | All messages with a given key go to one partition, or to its descendants after a split |
| 2 | Order is preserved per key |
| 3 | Every accepted message reaches a terminal state: acknowledged or failed. Never silently dropped, never left pending |
| 4 | A split is invisible: no loss, and no duplicates for messages the server had already persisted |
| 5 | A split does not require the caller to recreate the writer |
| 6 | Transient errors are retried internally |
| 7 | Closing with flush delivers everything already accepted |

What it deliberately does **not** guarantee:

- No global order across different keys. Only per-key.

---

## 3. Internal invariants

These are the properties every part of the implementation is protecting. If you are porting this,
these are the things to write tests against.

1. **One key → one branch of the partition tree.** A key may travel `p0 → p2 → p5`, but must never
   appear in two siblings. Violating this breaks per-key ordering for readers.
2. **The routing view never has a gap.** Every key must map to exactly one live partition at every
   moment, including mid-split.
3. **A seqno identifies a message for its whole life.** It is assigned once and never changes, even
   when the message moves to another partition.
4. **A message is in exactly one place:** in flight under exactly one partition, or resolved.
5. **The dedup cut only ever comes from the server.** See §9.4 — this is the subtlest part.

---

## 4. State

Everything below is owned by the orchestrator and guarded by a single lock (§11).

| State | Shape | Purpose |
|---|---|---|
| routing view | `partition_id → partition info` | live leaves only; what the chooser routes to |
| sub-writers | `partition_id → writer` | lazily created, idle-evicted |
| in-flight | `partition_id → {seqno → message}` | messages the orchestrator may still have to resend |
| seqno cursor | single integer | one sequence for the whole writer (§7) |
| init seqno | `partition_id → int` | server's persisted seqno when the current sub-writer opened |
| retired seqno | `partition_id → int` | server's final persisted seqno for a retired producer; cacheable |
| max acked | `partition_id → int` | highest ack actually observed |
| retiring | set of partition ids | suppresses expected ack failures during teardown |
| repartition tasks | `partition_id → task` | coalescing + shutdown ownership |
| last write time | `partition_id → timestamp` | idle eviction |

The routing view holds live leaves only: a partition is dropped from it the moment it is retired,
or keys would keep being sent to it. Nothing here remembers retired partitions, and nothing needs
to — see §9.4 for why the dedup cut never looks past the partition being retired.

---

## 5. Routing

### 5.1 Key ranges

**The server owns the ranges; the client only reads them.** They arrive in the `DescribeTopic`
response, one per partition:

```
DescribeTopicResult.PartitionInfo.key_range : PartitionKeyRange
    optional bytes from_bound   // inclusive left border, empty = -inf
    optional bytes to_bound     // exclusive right border, empty = +inf
```

Nothing on the client side derives, splits or interpolates a range. It reads what describe reports,
hashes the key, and picks the partition whose range contains the hash. A client that computed
ranges itself would immediately disagree with the server about which key belongs where.

Note the shape: **one interval per partition, not a set of them.** There is no way to express a
partition that owns two disjoint stretches of the key space. That single fact answers most
questions about what topology changes are even possible — see §9.6 for what it means for merges.

Bounds are opaque byte strings compared **bytewise, lexicographically**. No locale, no encoding
awareness, no numeric interpretation. Observed live: bounds are short — a real split produced
2-byte bounds like `efea`, `f7f5`.

```
before split      p0: ["",  "")                    ← one partition owns everything

after split       p0: ["",  "")   inactive, children [1,2]
                  p1: ["",  m)    active
                  p2: [m,   "")   active

key hashes to "apple" → p1
key hashes to "zebra" → p2
key hashes to "m"     → p2        ← left bound inclusive, right exclusive
```

### 5.2 The key is hashed before comparison

> Two different hashes appear in this document, for two different routing schemes. They are not
> alternatives and they are not a contradiction:
>
> | Scheme | Hash | Used for |
> |---|---|---|
> | range-based (§5.4) | **MurmurHash64A**, 64-bit | placing a key inside `[from_bound, to_bound)` |
> | hash-modulo (§5.5) | **murmur2, 32-bit** | `% partition_count` on a fixed partition count |
>
> The range-based one is the YDB path and is the one that has to match other writers. The 32-bit
> one exists only to reproduce Apache Kafka's partitioner and never touches key ranges.

For the range-based scheme the client does not compare the raw key against the bounds. It hashes
it:

```
partition_key = MurmurHash64A(key_bytes, seed=0)  →  8 bytes, big-endian
```

and puts that value into **message metadata under the key `__partition_key`**.

This is a real, supported contract, not a client-side convention — the server reads that exact
metadata key. All three SDKs use the same name and the same hash. A custom hasher is allowed but
must agree with whatever produced the topic's bounds.

> Historical trap: an older C++ implementation used a **16-byte** hasher (two hashes, the second
> with seed `0x9E3779B97F4A7C15`, high half first). The current one is 8 bytes. The server's bound
> encoding supports both widths — it just writes an integer big-endian — so a mismatched hasher
> does not fail loudly, it silently routes keys to the wrong partitions.

### 5.3 What the server does with `__partition_key`

**It does not validate routing.** The value is consumed only by the auto-partitioning logic, as
input to deciding *where to cut* when the partition splits. A write goes to whatever partition the
client addressed, whether or not the key belongs there.

Consequence for implementers: a routing bug produces no error. It shows up much later, as one key
smeared across two branches of the partition tree. Client-side range checking is the only defence.

### 5.4 Lookup

The ranges **tile** the key space: they do not overlap, and together they cover all of it. So a
hashed key falls into exactly one of them, and that partition owns it. That is the whole model.

In code the lookup is a lower-bound search — index the partitions by `from_bound` and take the
greatest one at or below the hashed key:

```
partition = greatest from_bound <= hashed_key
```

On a complete set that is already the answer: the tiling guarantees the key is below that
partition's `to_bound`.

Which is exactly why comparing against `to_bound` anyway is worth doing. It is not part of the
lookup, it is a check on *our own view of the topology*:

```
if partition.to_bound is not empty and hashed_key >= partition.to_bound:
    refuse — our partition set is not a tiling; it has a hole
```

A lower-bound search always returns *something*. If our set is incomplete — a split whose second
child is not visible yet — the something it returns is the left neighbour, a sibling. Sending the
key there breaks invariant 1, and per §5.3 the server will not catch it. The check turns a silent
misroute into a refusal the caller can retry.

The same applies when a partition set is accepted: validate it **after sorting**, not in arrival
order. Describe responses carry no ordering promise, and only the leftmost partition may have an
open lower bound.

### 5.5 Two choosers

| Chooser | Rule | Use |
|---|---|---|
| range-based | as above | auto-partitioned topics (the only correct one there) |
| hash-modulo | `murmur2_32(key) & 0x7FFFFFFF, then % partition_count` | fixed partition count; Kafka-compatible |

The masking before the modulo matters for Kafka compatibility — Kafka applies `toPositive()` to a
*signed* 32-bit hash before the modulo.

> Trap if you port from Go: its hash chooser carries a comment saying "Same as Kafka Partitioner"
> with a link to `BuiltInPartitioner`, but computes `hash % uint32(n)` with no mask. Unsigned
> modulo and masked signed modulo disagree for any hash with the high bit set, so keys land on
> different partitions than a Kafka producer would choose. For key `"a"` over 3 partitions Kafka
> picks index 2; the unmasked form picks 1.

Selection is **adaptive**: pick range-based if the topic has auto-partitioning enabled *or* any
partition reports a key range, else hash-modulo.

> Trap: a freshly created single-partition auto-partitioned topic can report **no key range at
> all**. Keying the decision on "does any partition have a range" alone therefore picks the
> hash-modulo chooser, which then rejects the bounded children the first split produces — the
> writer breaks precisely when the feature it exists for finally triggers. Prefer the topic's
> auto-partitioning strategy as the signal.

---

## 6. Sub-writers

### 6.1 Identity

```
producer_id = <prefix> + separator + <partition_id>
```

The producer id is **per partition**, not per key. All three implementations agree.

This has a large consequence: server-side deduplication is scoped to
`(partition, producer_id, seqno)`, so it **cannot span a split** — the child writes under a
different producer id. Everything in §9.4 exists because of this.

Per-key producer ids would give cross-split dedup for free, but a write session carries exactly
one producer id, so that would mean one session per key. Nobody does this.

### 6.2 Creation

Sub-writers are created **lazily, on the first write to a partition**, never up front. An
auto-partitioned topic can have far more partitions than the caller's keys touch.

Creation is: build settings → open the session → **wait for the init handshake** → register.

Two details that are easy to get wrong:

- **Bound the init wait.** A session pinned to an inactive partition never completes its handshake.
  Since creation happens under the orchestrator lock, an unbounded wait there freezes every write,
  flush and repartition in the whole writer. This is reachable in normal operation: splits cascade,
  so the child you just routed to may itself have split already.
- **Register only after init succeeds.** Otherwise a failed creation leaves a permanently broken
  writer in the pool.

Sub-writers are configured with **automatic sequence numbering disabled** — the orchestrator
supplies the numbers (§7).

### 6.3 Sessions always name their partition

A session that writes always sets `partition_id`. There is no second mode to choose from.

The one place the partition id is deliberately left out is reading the persisted seqno of a
partition that has already split (§9.4). That session never writes anything: it is opened only for
its init response and closed again. Leaving the id out is what makes it work at all — pinned to an
inactive partition, the session would never finish its init, and the number being read belongs to
the producer rather than to any one partition anyway.

### 6.4 Idle eviction

A sub-writer with **no in-flight messages** and no writes for the idle timeout is closed and
recreated on demand. Both conditions matter: closing a session with unacked writes would strand
them.

Eviction must not be observable. In particular the **seqno cursor survives it** — a re-opened
partition continues the sequence rather than restarting.

Recommended idle timeout is minutes, not seconds; too short and a bursty workload pays for constant
reconnects.

### 6.5 Lifecycle

```
        first write to partition
                 │
                 ▼
          ┌─────────────┐   idle, no in-flight    ┌──────────┐
          │   ACTIVE    │ ──────────────────────► │  EVICTED │
          │             │ ◄────────────────────── │          │
          └──────┬──────┘    write arrives        └──────────┘
                 │
                 │ OVERLOADED on the write stream
                 ▼
          ┌─────────────┐
          │  RETIRING   │  session closed, ack failures suppressed,
          │             │  successes still honoured
          └──────┬──────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
   topology changed   no children found
   → RETIRED          → recovered in place, back to ACTIVE
```

---

## 7. Sequence numbers

### 7.1 One cursor for the whole writer

There is **one counter for the entire multi-writer** — not one per partition, and not one per key.

```
write(key=A) → seqno 1   → partition 0
write(key=B) → seqno 2   → partition 1
write(key=A) → seqno 3   → partition 0
write(key=C) → seqno 4   → partition 0
```

Per-partition numbering looks simpler and is wrong in a specific way: when a split moves a message
to a child, a number drawn from the parent's sequence means nothing in the child's, so the message
must be **renumbered** — and a message that changes identity mid-flight can no longer be matched
against the attempt that may already have been persisted. A global cursor keeps the number valid in
every partition, which is what makes resend-preserving-seqno possible at all.

Both reference implementations use a single global cursor for exactly this reason.

Sequences per partition therefore have gaps. That is fine and expected.

### 7.2 Seeding

Each partition's producer has its own persisted history on the server. When a sub-writer opens, its
handshake reports that producer's last persisted seqno, and the cursor is lifted:

```
cursor = max(cursor, last_seqno_reported_by_this_session)
```

This is what makes a **stable producer id prefix** resume numbering across restarts instead of
colliding with what is already stored. Without it, a restarted writer re-uses low numbers and the
server rejects them as duplicates.

### 7.3 Caller-supplied seqno

When the caller numbers messages itself, the writer validates and tracks rather than generates:

- a missing number is a **validation error**, not a writer-stopped error — the writer is healthy,
  the input is not;
- the cursor is still lifted to the highest number seen, so a later switch or an internal use stays
  consistent;
- uniqueness is enforced **per partition**, matching Go. Global uniqueness is *not* required.

Merge is the one case where per-partition scope is not enough: two partitions may each hold seqno 5,
and a merge brings both into one child. This is detected and reported on one of the two messages
rather than silently overwriting state. Note both reference implementations ignore this case
entirely — they assume a single parent per partition.

---

## 8. The normal write path

```
caller                orchestrator                 sub-writer            server
  │                        │                            │                   │
  │ write(key, data)       │                            │                   │
  ├───────────────────────►│                            │                   │
  │                        │ 1. choose partition by key │                   │
  │                        │    (stamps __partition_key)│                   │
  │                        │                            │                   │
  │                        │ 2. get or create sub-writer│                   │
  │                        ├───────────────────────────►│                   │
  │                        │                            │ init handshake    │
  │                        │                            ├──────────────────►│
  │                        │                            │◄──────────────────┤
  │                        │    cursor = max(cursor, last_seqno)            │
  │                        │                            │                   │
  │                        │ 3. seqno = ++cursor        │                   │
  │                        │ 4. hand message to writer  │                   │
  │                        ├───────────────────────────►│                   │
  │                        │                            ├──────────────────►│
  │                        │ 5. record in-flight        │                   │
  │◄───────────────────────┤    return caller's future  │                   │
  │                        │                            │                   │
  │                        │                            │◄─── ack ──────────┤
  │                        │◄───────────────────────────┤                   │
  │                        │ 6. drop from in-flight     │                   │
  │                        │    raise max-acked         │                   │
  │◄───────────────────────┤    resolve caller's future │                   │
```

Order matters in two places:

- **Choose the partition before assigning the number.** The range-based chooser stamps
  `__partition_key` into the message during routing; anything that freezes the message earlier
  loses it.
- **Record in-flight only after the sub-writer accepts the message.** If admission fails —
  backpressure timeout, stopped writer — an entry recorded beforehand leaks a future nobody will
  ever resolve.

---

## 9. Split

### 9.1 The signal

There is **no split notification**. A split is discovered as an ordinary error on the write stream:
the partition goes inactive, and the next write to it is rejected as `OVERLOADED`.

```
status  = OVERLOADED
message = "Write to inactive partition N"
```

All three SDKs key on plain `OVERLOADED`. The server does carry a more precise internal code
(`WRITE_ERROR_PARTITION_INACTIVE`, surfaced as an issue code inside the overload status), which can
distinguish a split from ordinary load — but relying on it alone risks missing splits if it is not
always present, so it is best used as a fast positive signal with describe-based confirmation as the
fallback.

Because ordinary overload is indistinguishable by type, **the topology change must be confirmed by
a describe** before anything is committed.

### 9.2 Discovery

Children are the **active leaf partitions that list the retiring partition as a parent**. Re-describe
with backoff until they appear; if none ever do, this was ordinary overload (§10).

Discovery must also verify **coverage**: the children's ranges must span the parent's range without
a gap.

```
parent   p0: ["", "")

partial describe        complete describe
  p1: ["", 0x80)          p1: ["",   0x80)
  (p2 not yet active)     p2: [0x80, "")

  ▲ retiring p0 here      ▲ safe to retire p0
    leaves [0x80, "")
    unowned → keys in
    that range route to
    p1, a sibling
```

A mid-split describe genuinely can show one child before its sibling becomes active. Committing to
that view breaks invariants 1 and 2. Treat an incomplete graph as *retry later*, never as a
successful split.

Coverage means **"at least the parent's range"**, not an exact tiling: a merge child owns the ranges
of both its parents, so it legitimately covers more.

### 9.3 Ordering of operations

```
1. discover children, verify coverage        ← may abort; nothing committed yet
2. update the routing view:
     add children, then remove every retired parent    ← atomic, under the lock
3. quiesce every retired parent:
     close its session, let pending acks settle
4. for each retired parent:
     read the dedup cut  ← only now
     migrate its in-flight messages
```

Step 2 before step 4 means migration re-routes only to surviving partitions. Step 3 before step 4 is
what stops a still-open sibling from persisting a message *after* its cut was read — which would
duplicate that message on resend.

All of this happens **under the orchestrator lock**, so no write can interleave and see a
half-updated topology.

### 9.4 The dedup cut — the subtle part

The question migration has to answer for every in-flight message is: *was this already persisted to
the partition we are retiring?* Below the cut → report it written, do not resend. Above → resend.

**The cut must come from the server, not from acks the client observed.**

```
1. server persists seqno 42
2. the session dies in the split, the ack never arrives
3. client's highest observed ack is 41
4. client concludes 42 was not written and resends it to the child
5. the child writes under a different producer id, so nothing on the
   server can recognise the duplicate
6. the reader sees the message twice
```

The observed-ack cut is wrong in exactly the window the mechanism exists to protect.

Getting the server's answer for a partition that is already inactive is the trick worth copying:

```
open a session with the retiring partition's producer id
        WITHOUT a partition id
        → init handshake reports that producer's persisted seqno
        → close it
```

Why that works is in the protocol itself. `InitResponse.last_seq_no` is documented as *"last
persisted message's sequence number for this producer"*, and `get_last_seq_no` warns that it *"may
be expensive, if producer wrote to many partitions before"* — the number belongs to the producer,
not to the partition the session happened to land on. So the session does not need to reach the
retired partition; it only needs to name its producer.

Which is fortunate, because it cannot reach it: a session pinned to an inactive partition never
finishes its handshake — a real hang, not a slow path. Dropping the partition id is what lets the
session start at all. Both reference implementations do exactly this, and only for the split case.

The cut is **the retiring partition's own high-water mark, and nothing else**. It is tempting to
walk up the partition tree and take the maximum over the ancestors as well -- both reference
implementations do -- but that is unnecessary here, and with merges it is actively wrong.

Unnecessary, because a message sitting in this partition cannot have been persisted under any
producer it used earlier:

```
every move is gated by a cut of at least that producer's server seqno
  -> anything already stored there was resolved as written on the spot
  -> a message that travelled has a number strictly above it
  -> and a retired producer never grows

so asking an ancestor can only repeat an answer already known to be too low to matter
```

Wrong, because a merge child has two parents, and those branches numbered independently:

```
branch p1 numbered up to 5      branch p2 numbered up to 100
             \                    /
              →  merged into p3  ←

max over the parents = 100
a message that came down p1 with seqno 6 is "already written" -- and is dropped
```

The sibling's history says nothing about messages that came down this branch, and can be
arbitrarily higher than theirs. Neither reference hits this: both read only the first parent and
state that a partition is assumed to have exactly one, so for them the walk is merely redundant.
Combining their walk with real merge support is what makes it unsafe.

The same reasoning is why the recovery path (§10) has always used the partition's own value only.
With the walk gone the two paths compute the cut the same way.

### 9.5 Migration

```
for each in-flight message of the retiring partition, in seqno order:

    seqno <= cut ?
        └─ yes → resolve as written (offset unknown), do not resend
        └─ no  → re-route through the chooser
                 open the child's sub-writer
                 re-check the message is still in flight   ← it may have been
                                                             acked during that await
                 keep the seqno, change only the partition
                 hand it to the child, re-wire the ack
```

Three things that look optional and are not:

- **Iterate in seqno order.** Migration is the one place order can be lost.
- **Re-check after every await.** Opening the child's session yields; an ack can land in that window
  and resolve the message. Resending it then duplicates it.
- **On a placement failure, fail this message and every message after it.** Dropping loses data
  silently; skipping ahead reorders the key. Failing the tail is the only option that preserves both
  invariants.

### 9.6 Merge

Structurally the same path: a merge child lists **two** parents. Discovering children of one parent
finds it, and every parent of that child that we still hold is retired **together** — otherwise the
sibling parent lingers in the routing view with a range that now overlaps the child's, and routing
becomes ambiguous.

Both reference implementations ignore merge (they read only the first parent). At the time of
writing the server does not implement it either, so this path is defensive.

**Only adjacent partitions can merge, and this is a protocol constraint, not a client one.** A
partition's range is a single `[from_bound, to_bound)` (§5.1). Merging two partitions that are not
neighbours in the key space would give the child two disjoint stretches, and there is no field in
which to report that — so the situation cannot arise no matter how the server chooses to implement
merging. Adjacency is what makes the result expressible:

```
p1 [a, m) + p2 [m, z)   →   p3 [a, z)        one interval, reportable
p1 [a, m) + p3 [t, z)   →   [a,m) ∪ [t,z)    no representation for this
```

This also means the client needs no special rule to reject a gapped child: it cannot be described
in the first place. What the client does have to handle is the *transition* — the moment when both
parents are still in its view alongside the child, which is why every parent of a discovered child
is retired in the same step.

### 9.7 Full sequence

```
sub-writer(p0)      orchestrator                describe        probe        child(p2)
     │                    │                        │              │              │
     │ OVERLOADED         │                        │              │              │
     ├───────────────────►│                        │              │              │
     │                    │ stop p0's writer with  │              │              │
     │◄───────────────────┤ a distinguishable error│              │              │
     │                    │                        │              │              │
     │                    │ schedule repartition   │              │              │
     │                    │ (coalesced per partition)              │             │
     │                    │                        │              │              │
     │                    ├───── describe ────────►│              │              │
     │                    │◄──── children [2,3] ───┤              │              │
     │                    │  verify coverage       │              │              │
     │                    │                        │              │              │
     │                    │ routing: +2 +3, -0      │              │              │
     │                    │                        │              │              │
     │                    │ quiesce p0 (close, settle acks)       │              │
     │                    │                        │              │              │
     │                    ├─── unpinned session, producer "pfx-0" ►│             │
     │                    │◄── last_seqno = 2593 ──────────────────┤             │
     │                    │  cut = 2593                            │             │
     │                    │                        │              │              │
     │                    │ seqno <= 2593 → resolve as written     │              │
     │                    │ seqno >  2593 → resend, same seqno ───────────────────►│
     │                    │                        │              │              │
```

---

## 10. Ordinary overload

If describe never shows children, the overload was not a topology change. The partition is kept and
**recovered in place**: drop the stopped session, open a fresh one for the same partition, resend
the in-flight messages with their original seqnos.

Here the cut is exact and cheap — the partition is still active, so the fresh session's handshake
reports the current persisted seqno directly. No probe needed.

It is worth spelling out why a cut is needed here at all, because the obvious argument says it is
not: the partition and the producer id have not changed, so if the server already stored one of
these messages it will recognise the repeat and deduplicate it. Resending everything should be
harmless.

It is not, and the reason has nothing to do with the server:

```
ack for seqno 42 is lost when the session breaks
recovery opens a fresh sub-writer for the same partition
   its handshake reports last_seq_no = 42       ← the server does have it
   the writer takes 42 as its high-water mark
resend 42  → rejected by our own writer, "seqno is duplicated"
             the message never leaves the process
resend 43, 44, ... → never attempted: the loop stopped at the error
```

Sub-writers run with automatic numbering disabled (§6.2), and such a writer refuses any seqno at or
below the high-water mark it learned at init. So the message is stopped on the client, before the
server ever gets the chance to deduplicate it. Because the resend is a single ordered pass, that
one rejection also takes down every message queued behind it: none of them are sent, and none of
them are resolved.

Applying the cut removes the problem at the source — seqno 42 is at or below it, so it is reported
as written instead of resent, and the pass continues from 43.

---

## 11. Concurrency

A **single lock** serialises: routing decisions, sub-writer creation, seqno assignment, in-flight
bookkeeping, topology updates, migration, idle eviction.

That is coarse, and deliberately so: routing and topology changes must not interleave. The cost is
that anything slow taken under it stalls the whole writer, which is why every network wait under the
lock is bounded (§6.2, §9.4).

Repartition runs as a background task, and it must be **owned**:

- **coalesced per partition** — a burst of `OVERLOADED` must not start several concurrent recoveries
  of the same partition;
- **cancelled and awaited on close** — otherwise it keeps describing topics and opening sessions for
  a writer the caller believes is shut down;
- **blocked after close** — a late signal must not resurrect anything.

---

## 12. How a message can end

Every accepted message reaches exactly one of these:

| Outcome | When |
|---|---|
| written, with offset | normal ack |
| written, offset unknown | at or below a dedup cut — the server had it, the ack was lost |
| failed, placement | no ready partition owns the key, or the target could not be opened |
| failed, seqno conflict | a caller-supplied number collided in the target partition |
| failed, partition unusable | repartition and recovery both failed |
| failed, writer stopped | closed with messages still in flight |

The "offset unknown" outcome is a real part of the contract: the write happened, but the offset
came back on a stream that died. Both reference implementations do the same — C++ synthesises an
acknowledgement for exactly this case.

---

## 13. Traps, ranked by how much they cost to find

1. **A pinned session to an inactive partition hangs forever.** Costs: a frozen writer, if it is
   under the lock. Found only against a real split.
2. **The dedup cut from observed acks is wrong.** Costs: duplicates, rarely, unreproducibly.
3. **Closing a hook-stopped session re-raises the stop reason.** Closing a session you are
   discarding must swallow errors, or the repartition aborts on cleanup.
4. **Suppressing ack failures during teardown must not suppress successes.** A success landing while
   the session closes is real; dropping it lowers the cut and duplicates the message.
5. **A mid-split describe can show one child of two.** Committing to it smears a key across
   siblings.
6. **Greatest-lower-bound routing never fails, it just answers wrongly** when the partition set has
   a hole. And the server will not catch it.
7. **A single-partition auto-partitioned topic may report no key range**, which fools chooser
   selection that keys on ranges alone.
8. **You may not be able to make this writer split a topic at all.** On the cluster we tested,
   load driven through the multi-writer never triggered auto-partitioning, while separate
   load from ordinary writers, with no explicit partition id, split the topic in seconds. Whether that is general or a property of that
   build, we did not establish -- but plan test scenarios for it: drive splits with a separate
   producer rather than expecting the writer under test to cause its own.
9. **Test doubles hide all of the above.** Fakes that always accept a seqno, always initialise, and
   never raise on close will keep every one of these bugs green. Model the real contracts: the
   seqno high-water rejection, the init that never completes, the close that re-raises, and state
   keyed by producer id rather than by partition.

---

## 14. Implementation cross-reference

| Aspect | Here | C++ `TProducer` | Go `topicmultiwriter` |
|---|---|---|---|
| producer id | per partition | per partition | per partition |
| seqno cursor | one, writer-wide | one, writer-wide | one, writer-wide |
| resend keeps seqno | yes | yes | yes |
| cut source | server, retiring partition only | server, whole lineage | server, whole lineage |
| cut probe | unpinned session | unpinned session | unpinned session |
| split signal | `OVERLOADED` | `OVERLOADED` | `OVERLOADED` |
| key hash | murmur64a, 8B big-endian | same | same |
| Kafka positive mask | yes | n/a | no |
| merge | handled | single parent assumed | single parent assumed |
| transient overload | recovered in place | — | stops with error |
| coverage check before retiring | yes | no | no |
| upper-bound check on routing | yes | no | no |

The last four rows are places where this implementation is deliberately stricter than the
references.

---

## 15. Open items

- Batch writes are admitted message by message; a mid-batch failure can leave earlier messages
  accepted while the call raises, with no handle returned for them.
- Buffer limits are per sub-writer, so the effective budget scales with the number of open
  partitions rather than belonging to the logical writer.
- Split coverage in automated tests depends on the environment producing a real split; an
  environment that cannot must be distinguished from a split that failed to happen.
