# Topic stream stack

The topic reader and writer share their reconnect + bidi-stream lifecycle through two base
classes in this package. The concrete reader/writer reconnectors and stream objects are thin
subclasses.

```
StreamReconnector (abc, Generic[ConnT])      — WHEN to (re)connect
  • the single reconnect loop, backoff, the reconnector-level fatal signal, close ordering
  • _new_connection() (sync) + _handshake(conn) + _run(conn)
        │ creates / drives
        ▼
StreamConnection (abc)                        — WHAT a bidi stream is
  • owns the gRPC wrapper (built SYNC), connect() = start + init handshake,
    the per-connection death signal (wait_error), the update-token loop, close()
        ├── ReaderStream            ("fat": read/decode loops, partition sessions, commits)
        └── WriterAsyncIOStream     ("thin": receive()/write(); send/read loops in the reconnector)

ReaderReconnector(StreamReconnector["ReaderStream"])
WriterAsyncIOReconnector(StreamReconnector["WriterAsyncIOStream"])
```

## StreamReconnector — the reconnect loop

```python
attempt = 0
while not closed:
    conn = self._new_connection()      # SYNC: builds the connection, which owns its gRPC stream
    try:
        await self._handshake(conn)    # open call + init handshake
        self._conn = conn              # publish only after a successful handshake
        attempt = 0                     # reset ONLY on a successful connect
        await self._on_connected(conn)
        self._state_changed.set()
        await self._run(conn)          # block until this connection dies
    except BaseException as err:
        if CancelledError and not closed: err = ConnectionLost(...)
        info = self._classify_error(err, attempt)
        if not info.is_retriable:
            self._signal_fatal(err); return
        await asyncio.sleep(info.sleep); attempt += 1
    finally:
        await self._close_connection(conn, flush=False)   # local `conn`: an interrupted
                                                          # handshake is still closed (no zombie)
```

Hooks: `_new_connection` (sync), `_handshake`, `_run`, `_close_connection`, `_terminal_error`
(required); `_on_connected`, `_on_fatal`, `_classify_error` (defaults). `_run(conn)` is
`await conn.wait_error()` for **both** reader and writer.

## StreamConnection — the bidi stream

Constructed synchronously (no network in `__init__`; it builds its `GrpcWrapperAsyncIO`
immediately). `connect(driver)` = `stream.start(...)` + `_init_and_spawn()`. Owns the
per-connection death signal (`_first_error` / `wait_error` / `_set_first_error`) and the shared
update-token loop. Hooks: `_init_and_spawn`, `_make_update_token_request`, `_on_first_error`.

## Two error signals

- **connection-level** `StreamConnection._first_error` (`wait_error`): *this stream* died →
  `_run` returns → reconnect.
- **reconnector-level** `StreamReconnector._fatal` (`_signal_fatal`): the reconnector is
  terminally done (non-retriable / `close()`) → surfaces to the public API.

## Invariants

1. **Single live stream, no zombie — structural.** Only the one loop assigns `_conn`, and the
   `finally` closes the current connection before the next is created. Because `_new_connection()`
   is synchronous and the connection owns its gRPC stream, the reconnector holds a closeable
   reference *before* the first cancellable network await — so a cancel during the handshake
   (e.g. `close()` mid-reconnect) always closes the stream instead of leaking it. No per-`create`
   cleanup guard, and it covers the writer too. (`test_reconnect_handshake_cancel_closes_stream`.)
2. **Backoff grows.** `attempt` lives in the base loop and resets only on a successful connect.
3. **close ordering.** Mark closed, flush + close the live connection, wake waiters, cancel the
   loop. The writer flushes *before* `super().close()` while `_closed` is still False (flushing
   after would deadlock — the loop wouldn't bring up the connection the buffered writes need).

## Reader/writer asymmetry (intentional)

`_run` is symmetric, but the run-loops live in different places, dictated by **data ownership
across reconnects**:

- the reader's per-stream state (partition sessions, read-ahead) *must die* on reconnect → it
  lives on `ReaderStream`, with the read/decode loops;
- the writer's loops drive the unacked outbox (`_messages`, `_messages_future`, seqno dedup) that
  *must survive* reconnect → it lives on the reconnector, with the send/read loops next to it.

Moving the writer's loops onto the stream would require extracting that outbox into its own
object (the reconnector keeps it; each stream pumps it). Not done.
