YDB Types
=========

YDB has its own type system. When passing parameters to queries you can let the SDK
infer the YDB type from the Python value automatically, or declare the type explicitly
when you need precise control.


Implicit Type Mapping
---------------------

For most common cases, pass a plain Python value and the SDK will pick the right type:

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Python value
     - YDB type inferred
     - Notes
   * - ``bool``
     - ``Bool``
     -
   * - ``int``
     - ``Int64``
     -
   * - ``float``
     - ``Double``
     -
   * - ``str``
     - ``Utf8``
     -
   * - ``bytes``
     - ``String``
     -
   * - ``dict``
     - ``Json``
     - serialised to JSON text
   * - ``list`` / ``tuple``
     - ``Json``
     - serialised to JSON text

.. code-block:: python

    pool.execute_with_retries(
        "DECLARE $name AS Utf8; SELECT * FROM users WHERE name = $name",
        parameters={"$name": "Alice"},        # str → Utf8
    )

    pool.execute_with_retries(
        "DECLARE $active AS Bool; SELECT * FROM users WHERE active = $active",
        parameters={"$active": True},         # bool → Bool
    )


Explicit Types
--------------

When the automatic mapping is ambiguous or you need a type that cannot be inferred,
declare the type explicitly using one of three forms.

Tuple form ``(value, type)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    parameters={
        "$id": (42, ydb.PrimitiveType.Uint64),
    }

``ydb.TypedValue``
^^^^^^^^^^^^^^^^^^

.. code-block:: python

    parameters={
        "$id": ydb.TypedValue(42, ydb.PrimitiveType.Uint64),
    }

Both forms are equivalent. The tuple form is more concise; :class:`~ydb.TypedValue` is more
explicit and works well with type checkers.


PrimitiveType Reference
-----------------------

Integers
^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Type
     - Range
     - Notes
   * - ``PrimitiveType.Bool``
     - true / false
     -
   * - ``PrimitiveType.Int8``
     - −128 … 127
     -
   * - ``PrimitiveType.Uint8``
     - 0 … 255
     -
   * - ``PrimitiveType.Int16``
     - −32 768 … 32 767
     -
   * - ``PrimitiveType.Uint16``
     - 0 … 65 535
     -
   * - ``PrimitiveType.Int32``
     - −2³¹ … 2³¹−1
     -
   * - ``PrimitiveType.Uint32``
     - 0 … 2³²−1
     -
   * - ``PrimitiveType.Int64``
     - −2⁶³ … 2⁶³−1
     - default for ``int``
   * - ``PrimitiveType.Uint64``
     - 0 … 2⁶⁴−1
     -

Floating point
^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Type
     - Notes
   * - ``PrimitiveType.Float``
     - 32-bit IEEE 754
   * - ``PrimitiveType.Double``
     - 64-bit IEEE 754; default for Python ``float``

Text and binary
^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Type
     - Notes
   * - ``PrimitiveType.Utf8``
     - UTF-8 encoded text; default for Python ``str``
   * - ``PrimitiveType.String``
     - arbitrary bytes; default for Python ``bytes``
   * - ``PrimitiveType.Json``
     - JSON text stored as ``Utf8``
   * - ``PrimitiveType.JsonDocument``
     - JSON stored in a binary representation optimised for field access
   * - ``PrimitiveType.Yson``
     - YSON binary/text format (YDB-specific)
   * - ``PrimitiveType.DyNumber``
     - arbitrary-precision decimal stored as text

Date and time
^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Type
     - Notes
   * - ``PrimitiveType.Date``
     - calendar date; maps to/from ``datetime.date``
   * - ``PrimitiveType.Datetime``
     - date + time without timezone (second precision)
   * - ``PrimitiveType.Timestamp``
     - date + time without timezone (microsecond precision); maps to/from ``datetime.datetime``
   * - ``PrimitiveType.Interval``
     - duration; maps to/from ``datetime.timedelta``
   * - ``PrimitiveType.Date32``
     - extended-range date (supports negative years)
   * - ``PrimitiveType.Datetime64``
     - extended-range datetime (second precision)
   * - ``PrimitiveType.Timestamp64``
     - extended-range timestamp (microsecond precision)
   * - ``PrimitiveType.Interval64``
     - extended-range interval

Other
^^^^^

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Type
     - Notes
   * - ``PrimitiveType.UUID``
     - UUID stored as two 64-bit integers; maps to/from ``uuid.UUID``

.. code-block:: python

    import datetime
    import ydb

    pool.execute_with_retries(
        "DECLARE $ts AS Timestamp; SELECT * FROM events WHERE created_at > $ts",
        parameters={
            "$ts": ydb.TypedValue(
                datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
                ydb.PrimitiveType.Timestamp,
            )
        },
    )


Collection Types
----------------

OptionalType
^^^^^^^^^^^^

Wraps any type to allow ``None`` values. Use when a parameter or column is nullable:

.. code-block:: python

    # Nullable Utf8 — pass None or a string
    ydb.OptionalType(ydb.PrimitiveType.Utf8)

    pool.execute_with_retries(
        "DECLARE $nickname AS Utf8?; "
        "INSERT INTO users (id, nickname) VALUES (1, $nickname)",
        parameters={"$nickname": (None, ydb.OptionalType(ydb.PrimitiveType.Utf8))},
    )

ListType
^^^^^^^^

A homogeneous ordered sequence:

.. code-block:: python

    ydb.ListType(ydb.PrimitiveType.Int64)

    pool.execute_with_retries(
        "DECLARE $ids AS List<Int64>; "
        "SELECT * FROM users WHERE id IN $ids",
        parameters={"$ids": ([1, 2, 3], ydb.ListType(ydb.PrimitiveType.Int64))},
    )

DictType
^^^^^^^^

A map from a key type to a value type:

.. code-block:: python

    # Dict<Utf8, Int64>
    ydb.DictType(ydb.PrimitiveType.Utf8, ydb.PrimitiveType.Int64)

    parameters={
        "$scores": (
            {"alice": 10, "bob": 20},
            ydb.DictType(ydb.PrimitiveType.Utf8, ydb.PrimitiveType.Int64),
        )
    }

StructType
^^^^^^^^^^

A named record — useful for passing rows as parameters:

.. code-block:: python

    row_type = (
        ydb.StructType()
        .add_member("id", ydb.PrimitiveType.Uint64)
        .add_member("name", ydb.PrimitiveType.Utf8)
    )

    pool.execute_with_retries(
        "DECLARE $row AS Struct<id:Uint64,name:Utf8>; "
        "INSERT INTO users (id, name) VALUES ($row.id, $row.name)",
        parameters={
            "$row": ({"id": 1, "name": "Alice"}, row_type)
        },
    )

Combine :class:`~ydb.ListType` + :class:`~ydb.StructType` for bulk inserts:

.. code-block:: python

    row_type = (
        ydb.StructType()
        .add_member("id", ydb.PrimitiveType.Uint64)
        .add_member("name", ydb.PrimitiveType.Utf8)
    )
    rows_type = ydb.ListType(row_type)

    rows = [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
    ]

    pool.execute_with_retries(
        "DECLARE $rows AS List<Struct<id:Uint64,name:Utf8>>; "
        "INSERT INTO users SELECT id, name FROM AS_TABLE($rows)",
        parameters={"$rows": (rows, rows_type)},
    )

TupleType
^^^^^^^^^

A positional (unnamed) record. Build it by chaining ``add_element``:

.. code-block:: python

    point_type = (
        ydb.TupleType()
        .add_element(ydb.PrimitiveType.Double)   # x
        .add_element(ydb.PrimitiveType.Double)   # y
    )

    parameters={"$point": ([1.0, 2.0], point_type)}

DecimalType
^^^^^^^^^^^

Fixed-precision decimal number:

.. code-block:: python

    # Decimal(22, 9) — 22 total digits, 9 after the decimal point (default)
    ydb.DecimalType()

    # Custom precision
    ydb.DecimalType(precision=10, scale=2)


Reading Values from Result Sets
--------------------------------

When you read from a result set, the SDK converts YDB values back to Python objects:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - YDB type
     - Python value returned
   * - ``Bool``
     - ``bool``
   * - ``Int*/Uint*``
     - ``int``
   * - ``Float`` / ``Double``
     - ``float``
   * - ``Utf8``, ``Json``, ``JsonDocument``
     - ``str``
   * - ``String``, ``Yson``
     - ``bytes``
   * - ``Date``
     - ``datetime.date``
   * - ``Datetime`` / ``Datetime64``
     - ``datetime.datetime``
   * - ``Timestamp`` / ``Timestamp64``
     - ``datetime.datetime``
   * - ``Interval`` / ``Interval64``
     - ``datetime.timedelta``
   * - ``UUID``
     - ``str`` (formatted as ``xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx``)
   * - ``Decimal``
     - ``decimal.Decimal``
   * - ``Optional<T>``
     - the inner value, or ``None``

.. code-block:: python

    result_sets = pool.execute_with_retries(
        "SELECT id, name, created_at, score FROM users WHERE id = 1"
    )
    row = result_sets[0].rows[0]

    row["id"]          # int
    row["name"]        # str  (Utf8 column)
    row["created_at"]  # datetime.datetime  (Timestamp column)
    row["score"]       # float  (Double column)

.. note::

   ``String`` columns return ``bytes``, not ``str``. If you store text in a
   ``String`` column, decode it explicitly: ``row["col"].decode("utf-8")``.
   Prefer ``Utf8`` for text data.
