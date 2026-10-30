Observability
=============

The SDK exposes a small, vendor-neutral tracing interface in :mod:`ydb.observability`.
Key YDB operations — session creation, query execution, transaction commit/rollback,
driver initialization, and retries — are turned into spans and handed to whichever
*tracing provider* you install. `OpenTelemetry <https://opentelemetry.io/>`_ is the
built-in backend (see :doc:`opentelemetry`), but any tracing system can be plugged in
by implementing the interface described below.

The same layer also exposes **client-side metrics** (operation latency and failures,
retry cost, query session pool state) through :func:`ydb.observability.enable_metrics`.
Tracing and metrics are independent — enable either, both, or neither.

Observability has a **zero-cost no-op path when disabled**: operations, query sessions,
and pools share no-op instrumentation without metric allocations, timers, locks, or
state tracking. The SDK never imports ``opentelemetry`` — or any other backend — on its
own. Backend dependencies are pulled in only when you explicitly opt into a concrete
backend.


The Tracing Interface
---------------------

Two small protocols make up the whole contract. A backend implements
:class:`~ydb.observability.TracingProvider`; the SDK calls it to create spans and to
collect metadata to propagate to the server:

.. code-block:: python

    class TracingProvider(Protocol):
        def create_span(self, name, attributes=None, kind=None) -> Span: ...
        def get_trace_metadata(self) -> Iterable[Tuple[str, str]]: ...

Every span it returns must satisfy :class:`~ydb.observability.Span`:

.. code-block:: python

    class Span(Protocol):
        def set_attribute(self, key, value): ...
        def set_error(self, exception): ...
        def end(self): ...
        def attach_context(self, end_on_exit=True) -> ContextManager["Span"]: ...

Both are :class:`typing.Protocol` types, so a provider does **not** need to subclass
anything — any object with matching methods works (duck typing).


Enabling and Disabling
----------------------

.. code-block:: python

    from ydb.observability import enable_tracing, disable_tracing

    enable_tracing(provider)   # install a backend
    disable_tracing()          # turn tracing off — back to the no-op default

``enable_tracing`` requires a provider. Calling it again replaces the previous one — the
old provider stops receiving spans immediately — so it is safe to reconfigure at any
time. ``disable_tracing()`` is the single way to switch tracing off; it restores the
built-in no-op default.


What Gets Traced
----------------

The SDK produces the following spans regardless of which backend is installed:

.. list-table::
   :header-rows: 1
   :widths: 35 20 45

   * - Span Name
     - Kind
     - Description
   * - ``ydb.Driver.Initialize``
     - INTERNAL
     - Driver wait / endpoint discovery.
   * - ``ydb.CreateSession``
     - CLIENT
     - Creating a new query session.
   * - ``ydb.ExecuteQuery``
     - CLIENT
     - Executing a query (including ``execute_with_retries``).
   * - ``ydb.BeginTransaction``
     - CLIENT
     - Explicitly beginning a transaction via ``.begin()``.
   * - ``ydb.Commit``
     - CLIENT
     - Committing an explicit transaction.
   * - ``ydb.Rollback``
     - CLIENT
     - Rolling back a transaction.
   * - ``ydb.RunWithRetry``
     - INTERNAL
     - Umbrella span wrapping the whole retryable block (``retry_operation_*`` / ``retry_tx_*`` / ``execute_with_retries``).
   * - ``ydb.Try``
     - INTERNAL
     - A single retry attempt. From the **second** attempt onward carries
       ``ydb.retry.backoff_ms`` — how long the retrier slept before starting this
       attempt (``0`` on the skip-yield retry path: ``Aborted`` / ``BadSession`` /
       ``NotFound`` / ``InternalError``, where the protocol prescribes immediate
       retry without backoff). The very first ``ydb.Try`` omits the attribute entirely.

Every RPC (CLIENT-kind) span is created with these standard attributes already filled
in, so they reach your provider through the ``attributes`` argument of
``create_span``:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Attribute
     - Description
   * - ``db.system.name``
     - Always ``"ydb"``.
   * - ``db.namespace``
     - Database path (e.g. ``"/local"``).
   * - ``server.address``
     - Host from the connection string.
   * - ``server.port``
     - Port from the connection string.
   * - ``network.peer.address``
     - Actual node host from the discovery endpoint map (set once the session is attached to a node).
   * - ``network.peer.port``
     - Actual node port from the discovery endpoint map.
   * - ``ydb.node.dc``
     - Data-center / location reported by discovery for the node (e.g. ``"vla"``, ``"sas"``).
   * - ``ydb.node.id``
     - YDB node that handled the request (when known).

How **errors** are recorded is up to the provider: the SDK calls ``span.set_error(exc)``
and the provider decides what to store. The built-in OpenTelemetry backend, for example,
adds ``error.type`` and ``db.response.status_code`` and marks the span status — see
:doc:`opentelemetry`.


Choosing a Backend
------------------

OpenTelemetry (built-in)
~~~~~~~~~~~~~~~~~~~~~~~~~

The recommended backend for most users. Enabling it is a single call:

.. code-block:: python

    from ydb.opentelemetry import enable_tracing

    enable_tracing()

Under the hood this constructs an
:class:`~ydb.opentelemetry.plugin.OtelTracingProvider` and installs it via
``ydb.observability.enable_tracing``. Installation, exporters, trace-context
propagation, and a full runnable example live on the :doc:`opentelemetry` page.


Writing a Custom Provider
~~~~~~~~~~~~~~~~~~~~~~~~~~

To send traces somewhere OpenTelemetry does not cover — a home-grown collector, a log
line, an in-memory recorder for tests — implement the two protocols yourself. Nothing to
subclass; just match the method signatures:

.. code-block:: python

    import contextlib

    from ydb.observability import enable_tracing, disable_tracing


    class LoggingSpan:
        def __init__(self, name, attributes):
            self.name = name
            self.attributes = dict(attributes or {})
            self.error = None

        def set_attribute(self, key, value):
            self.attributes[key] = value

        def set_error(self, exception):
            self.error = exception

        def end(self):
            status = f"ERROR {self.error!r}" if self.error else "OK"
            print(f"[trace] {self.name} {status} {self.attributes}")

        @contextlib.contextmanager
        def attach_context(self, end_on_exit=True):
            # Make this span the "current" one for your backend here, if it has a
            # notion of an active span (optional).
            try:
                yield self
            except BaseException as exc:
                # Setup failed: end the span here — nobody else will.
                self.set_error(exc)
                self.end()
                raise
            else:
                if end_on_exit:
                    self.end()
                # If end_on_exit is False the span is left open on purpose — see below.


    class LoggingProvider:
        def create_span(self, name, attributes=None, kind=None):
            return LoggingSpan(name, attributes)

        def get_trace_metadata(self):
            # (key, value) header pairs to inject into every outgoing gRPC call so the
            # server can join the trace. Return () if you do not propagate context.
            return ()


    enable_tracing(LoggingProvider())
    # ... use the SDK; spans are printed as they finish ...
    disable_tracing()

``kind`` is the semantic span kind the SDK requests — ``"client"`` for RPC spans and
``"internal"`` for umbrella/retry spans; map it to your backend or ignore it.


The Streaming Subtlety (``end_on_exit``)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Most SDK spans are **single-shot**: the span is entered, the RPC runs inside the ``with``
block, and the span ends when the block exits — that is ``end_on_exit=True``, the default.

**Streaming** RPCs (such as query execution, which returns a result-set iterator) are
different. The span must stay open while the *caller* consumes the stream, which happens
**after** the setup ``with`` block has already returned. For those the SDK calls
``attach_context(end_on_exit=False)``: the span's context is attached only while the call
is being initiated, and ownership of ``end()`` is handed to the result iterator, which
ends the span once the stream is fully consumed (or fails). If setup itself raises inside
the ``with`` block, the span is ended right there instead — the caller never received an
iterator to drain.

A custom ``attach_context`` must therefore honour this three-way contract on block exit:

.. list-table::
   :header-rows: 1
   :widths: 45 55

   * - Situation
     - Action
   * - An exception is raised inside the block
     - ``set_error(exc)`` then ``end()`` — always, regardless of ``end_on_exit``.
   * - Clean exit, ``end_on_exit=True``
     - ``end()``.
   * - Clean exit, ``end_on_exit=False``
     - Do **nothing** — the result iterator owns ``end()`` and will call it later.

The ``LoggingSpan`` above already implements exactly this. Getting it wrong leaks spans
(never ended) or ends them too early (streaming spans that miss the actual read time).


Metrics
-------

Client-side metrics are enabled independently of tracing:

.. code-block:: python

    from ydb.observability import enable_metrics, disable_metrics

    enable_metrics(provider)   # install a metrics backend
    disable_metrics()          # turn metrics off — back to the no-op default

Operation and retry metrics follow the currently active provider immediately. Call
``enable_metrics`` before creating query sessions, a ``QuerySessionPool``, or a topic
Reader whose lifecycle should be instrumented. Session, pool, and Reader lifecycle
trackers created while metrics are disabled keep shared no-op instrumentation and are
not retrofitted later.

Calling ``enable_metrics`` again replaces the active backend. New events go to the new
backend, while operations and wait timers already in flight finish on the backend on
which they started. Observable callbacks registered by an old backend become inactive.
Pools and topic Readers that were created while metrics were active retain their
lightweight lifecycle state across ``disable_metrics`` / re-enable, so a replacement
backend observes their current values. Pools and Readers created while metrics were
disabled retain no-op lifecycle instrumentation.

For OpenTelemetry the built-in convenience is ``ydb.opentelemetry.enable_metrics``,
which builds an OTel-backed provider from a meter provider and installs it here — see
the :doc:`opentelemetry` page for the meter-provider and exporter setup.

The Metrics Interface
~~~~~~~~~~~~~~~~~~~~~~

A metrics backend implements :class:`~ydb.observability.MetricsProvider` — three
methods, one per instrument kind:

.. code-block:: python

    class MetricsProvider(Protocol):
        def record(self, name, value, attributes=None): ...       # value distribution (histogram)
        def add(self, name, value, attributes=None): ...          # additive counter (may go negative)
        def observe_gauge(self, name, callback): ...              # asynchronous gauge

``record`` and ``add`` are pushed at the moment of the event. ``observe_gauge`` is
different: the SDK owns the accumulated state (open sessions per pool, configured pool
size) and hands the backend a ``callback`` that returns the current
``(value, attributes)`` observations; the backend reads it whenever it collects. This
keeps the pool bookkeeping vendor-neutral instead of pushing it into every backend.

It is a :class:`typing.Protocol`, so a backend does **not** need to subclass anything —
any object with these three methods works.

Instruments
~~~~~~~~~~~

The SDK records the following instruments regardless of backend (the OpenTelemetry
adapter maps them to instruments on the ``"ydb.sdk"`` meter):

.. list-table::
   :header-rows: 1
   :widths: 32 22 46

   * - Metric
     - Kind
     - Description
   * - ``db.client.operation.duration``
     - Histogram (``s``)
     - Latency of user-visible YDB client operations.
   * - ``ydb.client.operation.failed``
     - Counter
     - Failed user-visible YDB client operations.
   * - ``ydb.query.session.create_time``
     - Histogram (``s``)
     - Time spent creating a query session.
   * - ``ydb.query.session.pending_requests``
     - UpDownCounter
     - Requests currently waiting for a session from the pool.
   * - ``ydb.query.session.timeouts``
     - Counter
     - Session acquisition timeouts.
   * - ``ydb.query.session.count``
     - ObservableUpDownCounter
     - Current number of open query sessions by pool and ``ydb.query.session.state`` (``idle`` / ``used``).
   * - ``ydb.query.session.closed``
     - Counter
     - Closed query sessions by pool and closure ``reason``.
   * - ``ydb.query.session.max``
     - ObservableUpDownCounter
     - Maximum configured number of sessions for a query session pool.
   * - ``ydb.query.session.min``
     - ObservableUpDownCounter
     - Minimum configured pool size. The SDK sets no minimum, so this is always ``0``.
   * - ``ydb.client.retry.duration``
     - Histogram (``s``)
     - Total duration of a logical retried operation, including attempts and backoff.
   * - ``ydb.client.retry.attempts``
     - Histogram
     - Number of attempts performed for one logical retried operation.
   * - ``ydb.topic.reader.received.messages``
     - Counter (``{message}``)
     - Messages received by the SDK topic Reader before decoding.
   * - ``ydb.topic.reader.received.bytes``
     - Counter (``By``)
     - Total ``ReadResponse`` bytes received by the SDK topic Reader.
   * - ``ydb.topic.reader.delivered.messages``
     - Counter (``{message}``)
     - Messages returned by the topic Reader to the application.
   * - ``ydb.topic.reader.compression.duration``
     - Histogram (``s``)
     - Time spent decompressing a message, excluding decoder-executor queueing.
   * - ``ydb.topic.reader.message.processing.duration``
     - Histogram (``s``)
     - Time from receipt until a message is ready for delivery.
   * - ``ydb.topic.reader.commit.queued``
     - Counter (``{message}``)
     - Messages in commit ranges accepted by the SDK.
   * - ``ydb.topic.reader.commit.acknowledged``
     - Counter (``{message}``)
     - Messages acknowledged by regular committed-offset advances or successful transactions.
   * - ``ydb.topic.reader.commit_offset.lag.max``
     - ObservableGauge (``{message}``)
     - Maximum gap between requested and acknowledged commit offsets across active partitions.
   * - ``ydb.topic.reader.session.errors``
     - Counter (``{error}``)
     - Reader session errors by retry decision, status code, and error type.
   * - ``ydb.topic.reader.credit_balance_bytes``
     - ObservableGauge (``By``)
     - Protocol credit granted to the server and not yet consumed by read responses.
   * - ``ydb.topic.reader.local_buffer.messages``
     - ObservableUpDownCounter (``{message}``)
     - Current number of messages owned by the topic Reader and not yet returned to the application.
   * - ``ydb.topic.reader.local_buffer.message_age.max``
     - ObservableGauge (``s``)
     - Age of the oldest message owned by the topic Reader and not yet returned to the application.
   * - ``ydb.topic.reader.partition_session.count``
     - ObservableUpDownCounter (``{session}``)
     - Current number of active partition sessions owned by the topic Reader.

Attributes
~~~~~~~~~~

Operation metrics (``db.client.operation.*``) carry stable labels only:

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Attribute
     - Description
   * - ``database``
     - Database path.
   * - ``endpoint``
     - Configured endpoint in ``host:port`` form.
   * - ``operation.name``
     - SDK operation name without the ``ydb.`` prefix, e.g. ``"ExecuteQuery"``.
   * - ``status_code``
     - Added only to ``ydb.client.operation.failed``.

Operation metrics are recorded for ``ExecuteQuery``, ``Commit``, ``Rollback``,
``CreateSession`` and ``BeginTransaction``. Query session metrics use
``ydb.query.session.pool.name``: when ``name`` is not passed to ``QuerySessionPool``
the SDK falls back to the driver connection string ``<endpoint><database>`` (e.g.
``grpc://localhost:2136/local``) so the pool is identifiable out of the box. Pass
``QuerySessionPool(..., name="main-pool")`` (sync or async) when several pools share a
connection string. Retry metrics are recorded without attributes.

``ydb.query.session.closed`` uses these ``reason`` values:

* ``pool_idle_timeout`` — the idle-session cleaner removes a session. Python's
  ``QuerySessionPool`` has no idle-session timeout lifecycle, so it does not currently
  emit this reason.
* ``pool_graceful_shutdown`` — pool shutdown removes a session.
* ``client_timeout`` — a query stream exceeds its client-side transport timeout.
* ``client_cancelled`` — the client closes an unfinished query stream.
* ``attach_closed`` — the server closes the active attach stream.
* ``transport_error`` — an ``UNAVAILABLE`` status or a connection, query-stream, or
  attach-stream transport failure retires the session.
* ``node_shutdown`` — the server sends a node shutdown hint.
* ``session_shutdown`` — the server sends a session shutdown hint.
* ``bad_session`` — the server returns ``BAD_SESSION`` or ``SESSION_EXPIRED``.
* ``session_busy`` — the server returns ``SESSION_BUSY``.

Only an active session managed by a client pool publishes this metric. Failure of the
initial attach handshake does not count as closing an active session, and standalone
``QuerySession`` instances do not publish pool metrics. A session publishes at most one
closure event; the first terminal reason wins.

.. _topic-reader-receive-metrics:

Topic Reader Metrics
~~~~~~~~~~~~~~~~~~~~

Topic Reader metrics carry ``endpoint``, ``database``, and
``reader.name``. The ``consumer`` attribute is present only for consumer-based reads;
the SDK omits it when reading without a consumer. ``ydb.topic.reader.received.messages``,
``ydb.topic.reader.delivered.messages``, ``ydb.topic.reader.compression.duration``,
``ydb.topic.reader.message.processing.duration``, ``ydb.topic.reader.commit.queued``,
``ydb.topic.reader.commit.acknowledged``, ``ydb.topic.reader.commit_offset.lag.max``,
and ``ydb.topic.reader.partition_session.count`` additionally carry ``topic`` because
each message, commit offset, and partition session has an unambiguous topic. The reader-level
``ydb.topic.reader.received.bytes``, ``ydb.topic.reader.session.errors``,
``ydb.topic.reader.credit_balance_bytes``,
``ydb.topic.reader.local_buffer.messages``, and
``ydb.topic.reader.local_buffer.message_age.max`` metrics omit ``topic``: one
``ReadResponse`` can contain data from several topics, and the buffer gauges follow the
total retained by the logical Reader, while a session error belongs to the whole Reader.
Each response increments the byte counter once by ``ReadResponse.bytes_size``.
Metrics are published only when the application passes a non-empty ``reader_name`` to
``TopicClient.reader``. The name and metric context belong to the logical Reader and
remain stable across stream reconnects. The byte counter is updated as soon as the
transport delivers a ``ReadResponse`` to the SDK, before the response is converted to
batches; it is therefore counted even if conversion later fails. The message counter is
updated after the batches are created and queued, but before their payloads are decoded.
For a multi-topic Reader, message increments are
separated by ``topic`` while the response byte increment remains a single Reader-level
value. The delivery counter is updated only after a message or batch has been removed
from the SDK buffer and is ready to be returned by ``receive_message``, ``receive_batch``,
or ``receive_batch_with_tx``. A batch increments it by the number of messages actually
returned after applying ``max_messages`` and ``max_bytes``. Empty reads, timeouts, and
failures before the return point do not increment it. The local-buffer gauge increases
when accepted batches enter the decoding queue and decreases when messages leave the
internal buffer, including partial batch reads. It therefore includes both messages
waiting for decoding and decoded messages waiting for the application.
For every non-RAW message, ``ydb.topic.reader.compression.duration`` records only time
inside the decoder callable; time waiting in the decoder executor is excluded.
``ydb.topic.reader.message.processing.duration`` starts when the ``ReadResponse`` is
received and ends when the decoded batch becomes ready for delivery, so it includes
response conversion and decoder queueing. Both histograms carry ``topic``, ``codec``,
and ``outcome=ok|error``; failed measurements also carry ``error.type``. A batch is the
delivery unit in the Python SDK, so every message in one batch receives the same
processing duration. If any decoder fails, the batch's processing measurements use
``outcome=error``. RAW messages require no decoding and do not create either histogram
measurement. Only completed measurements are recorded.
Each commit range accepted by the SDK increments ``ydb.topic.reader.commit.queued`` by
``range.end - range.start``. A regular commit is counted after its
``CommitOffsetRequest`` is queued on the active stream. A transactional commit is counted
after its ranges pass SDK validation and are submitted to the transaction update path.
Already acknowledged ranges, expired partition sessions, and regular commit requests
that cannot be queued are not counted. A later transport or transaction failure does not
undo this cumulative counter.
For a regular ``CommitOffsetResponse``, ``ydb.topic.reader.commit.acknowledged`` increments
by ``max(0, committed_offset - previous_committed_offset)``. This counts the monotonic
committed-offset advance once even when queued ranges overlap. Repeated and stale
responses add nothing. Transactional ranges are acknowledged by their sizes only after
the whole transaction commits successfully; a failed commit or rollback does not
increment the counter.
``ydb.topic.reader.commit_offset.lag.max`` reports the maximum, across active partition
sessions of each topic, of ``max(0, highest_requested_end_offset - acknowledged_offset)``.
It increases after a regular ``CommitOffsetRequest`` is queued and decreases after a
``CommitOffsetResponse`` advances the acknowledged offset. Transactional commit ranges
remain visible in the commit counters but do not contribute to this stream-ACK gauge.
A stale acknowledgement cannot increase it. Stopping a partition session removes that
partition's contribution; reconnecting replaces the old stream's state, and a topic
with no active partition sessions has no observation.
Each failed session or connection attempt increments ``ydb.topic.reader.session.errors``
once after the retry policy classifies it. The ``retry_decision`` attribute is ``retry``
when the Reader will reconnect and ``stop`` when the error terminates the Reader.
``status_code`` contains the YDB status name when available and otherwise the exception
class name. ``error.type`` is ``transport_error`` for transport failures, ``ydb_error``
for other YDB errors, and the exception class name for other failures. Closing a Reader
normally does not increment the counter.
``credit_balance_bytes`` is set to the configured buffer size after the initial
``ReadRequest`` is sent, decreases by ``ReadResponse.bytes_size``, and increases only
when the Reader sends another ``ReadRequest`` after its release threshold is reached.
It is ``0`` while the logical Reader has no active stream, including reconnect gaps.
``local_buffer.message_age.max`` is computed with a monotonic clock from the receive
time of the oldest retained message; it is ``0`` when the buffer is empty. Receipt
cohorts are tracked internally per partition session so delivery from another partition
does not advance the oldest timestamp incorrectly. ``partition_session.count`` changes
when the server starts or stops a partition session, is split by ``topic``, and does not
carry a ``partition`` attribute. Each configured topic is observable with value ``0``
even before its first partition session starts. Remaining messages and partition
sessions are reset when a stream closes or reconnects, and closing the logical Reader
removes its observations. Use rates of the cumulative counters to compare incoming and
application-visible traffic; read the observable instruments as current values. For
matching Reader attributes, credit balances, buffer counts, and partition-session counts
are summed while the maximum buffer age is published.

See :ref:`opentelemetry-topic-reader-metrics` for an OpenTelemetry setup example. A
complete runnable version is available in ``examples/opentelemetry/otel_example.py``.

Writing a Custom Metrics Backend
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To send metrics somewhere OpenTelemetry does not cover — a home-grown collector, a log
line, an in-memory recorder for tests — implement the three methods. Nothing to
subclass; just match the signatures:

.. code-block:: python

    from ydb.observability import enable_metrics, disable_metrics


    class LoggingMetrics:
        def __init__(self):
            self._gauges = {}

        def record(self, name, value, attributes=None):
            # A value distribution (histogram): operation/create/retry durations, attempts.
            print(f"[metric] {name} = {value} {attributes or {}}")

        def add(self, name, value, attributes=None):
            # An additive counter; value may be negative (pending_requests goes up and down).
            print(f"[metric] {name} += {value} {attributes or {}}")

        def observe_gauge(self, name, callback):
            # Asynchronous gauge: keep the callback and poll it whenever you collect.
            # callback() -> iterable of (value, attributes).
            self._gauges[name] = callback

        def collect(self):
            for name, callback in self._gauges.items():
                for value, attributes in callback():
                    print(f"[gauge] {name} = {value} {attributes}")


    enable_metrics(LoggingMetrics())
    # ... use the SDK; record()/add() fire as operations happen ...
    disable_metrics()

The instrument kind for each metric is implied by which method the SDK calls: names in
the *Histogram* rows above arrive through ``record``, *Counter* / *UpDownCounter* names
through ``add``, and the eight observable instruments (the three query-session gauges,
``ydb.topic.reader.commit_offset.lag.max``,
``ydb.topic.reader.credit_balance_bytes``, ``ydb.topic.reader.local_buffer.messages``,
``ydb.topic.reader.local_buffer.message_age.max``, and
``ydb.topic.reader.partition_session.count``) through ``observe_gauge``. A backend
that has no notion of asynchronous gauges can simply store the callbacks (or ignore
them); the SDK never pushes those values, so nothing is lost elsewhere.

``disable_metrics()`` reverts event recording to the no-op default and deactivates the
current backend's gauge callbacks. Trackers belonging to already instrumented pools and
topic Readers remain available so a replacement backend starts with an accurate
snapshot; lifecycle trackers that started on the no-op path remain no-ops.
