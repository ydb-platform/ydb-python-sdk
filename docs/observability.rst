Observability
=============

The SDK exposes a small, vendor-neutral tracing interface in :mod:`ydb.observability`.
Key YDB operations — session creation, query execution, transaction commit/rollback,
driver initialization, and retries — are turned into spans and handed to whichever
*tracing provider* you install. `OpenTelemetry <https://opentelemetry.io/>`_ is the
built-in backend (see :doc:`opentelemetry`), but any tracing system can be plugged in
by implementing the interface described below.

Tracing is **zero-cost when disabled**: until you install a provider every span is a
no-op stub, and the SDK never imports ``opentelemetry`` — or any other backend — on its
own. The dependency is pulled in only when you explicitly opt into a concrete provider.


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
