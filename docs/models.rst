Typed Python Models
===================

The SDK can map dataclasses and Pydantic models to YDB structures. A model can be
used as a Query service parameter, as a row for ``bulk_upsert``, or as a key for
``read_rows``. Any value-format ``ResultSet`` can be converted back to model
instances with ``rows_as`` or ``iter_rows_as``.

Pydantic is optional. The SDK imports it only when a Pydantic model is used, and
supports both Pydantic v1 and v2 without adding it as an SDK dependency.


Defining a Model
----------------

Use ordinary Python annotations for fields whose default mapping is sufficient.
Use ``typing.Annotated`` with ``ydb.ModelField`` to change a YDB type or column
name:

.. code-block:: python

    import datetime
    from dataclasses import dataclass
    from decimal import Decimal
    from typing import Annotated

    import ydb


    @dataclass
    class Order:
        order_id: Annotated[
            int,
            ydb.ModelField(
                ydb_type=ydb.PrimitiveType.Uint64,
                column_name="id",
            ),
        ]
        customer: str
        amount: Annotated[
            Decimal,
            ydb.ModelField(ydb_type=ydb.DecimalType(22, 2)),
        ]
        created_at: datetime.datetime


The built-in mapping is:

.. list-table::
   :header-rows: 1
   :widths: 40 40

   * - Python annotation
     - Default YDB type
   * - ``bool``
     - ``Bool``
   * - ``int``
     - ``Int64``
   * - ``float``
     - ``Double``
   * - ``str``
     - ``Utf8``
   * - ``bytes``
     - ``String``
   * - ``datetime.date``
     - ``Date``
   * - ``datetime.datetime``
     - ``Timestamp``
   * - ``datetime.timedelta``
     - ``Interval``
   * - ``uuid.UUID``
     - ``UUID``

``Optional[T]``, ``list[T]``, ``dict[K, V]``, and nested dataclass or Pydantic
models are mapped recursively. Other annotations, such as ``Decimal``, need an
explicit ``ModelField(ydb_type=...)`` or a driver-level mapping.

The mapping priority is:

#. ``ModelField.ydb_type`` on the model field;
#. ``DriverConfig.type_mapping``;
#. the SDK built-in mapping shown above.


Driver-wide Type Mapping
------------------------

Use ``DriverConfig.type_mapping`` when an application wants the same mapping for
all of its models. For example, this makes every ``datetime.datetime`` field a
YDB ``Datetime64`` unless a field has its own ``ModelField`` override:

.. code-block:: python

    import datetime
    import ydb

    config = ydb.DriverConfig(
        endpoint="grpc://localhost:2136",
        database="/local",
        type_mapping={
            datetime.datetime: ydb.PrimitiveType.Datetime64,
        },
    )
    driver = ydb.Driver(config)

The mapping is copied when the configuration is created, so later changes to the
source dictionary do not change a running driver.


Query Parameters and Results
----------------------------

A model instance or a non-empty list of models can be passed directly as a Query
service parameter. The SDK infers the corresponding ``Struct`` or
``List<Struct<...>>`` type:

.. code-block:: python

    orders = [
        Order(1, "alice", Decimal("10.50"), datetime.datetime.now()),
        Order(2, "bob", Decimal("20.00"), datetime.datetime.now()),
    ]

    result_sets = pool.execute_with_retries(
        """
        DECLARE $orders AS List<Struct<
            id: Uint64,
            customer: Utf8,
            amount: Decimal(22, 2),
            created_at: Timestamp
        >>;
        SELECT * FROM AS_TABLE($orders) ORDER BY id;
        """,
        parameters={"$orders": orders},
    )

    loaded = result_sets[0].rows_as(Order)

An empty list has no runtime element from which to infer its item type. Wrap it in
``ModelValue`` and provide the Python annotation:

.. code-block:: python

    parameters={
        "$orders": ydb.ModelValue([], list[Order]),
    }

``rows_as(Model)`` returns a list. ``iter_rows_as(Model)`` converts rows lazily.
By default, result columns that are not present in the model are ignored. Pass
``strict_columns=True`` to reject such columns. Missing required model fields and
``NULL`` values for non-optional fields raise ``ModelConversionError``.

Arrow result sets cannot be converted with these helpers; decode Arrow data first.


Table Service
-------------

``bulk_upsert`` infers its column types from the first model when ``column_types``
is omitted:

.. code-block:: python

    driver.table_client.bulk_upsert("/local/orders", orders)

For an empty batch, pass the model explicitly:

.. code-block:: python

    driver.table_client.bulk_upsert("/local/orders", [], model=Order)

Do not pass ``column_types`` and ``model`` together.

``read_rows`` supports the same pattern for primary-key models:

.. code-block:: python

    @dataclass
    class OrderKey:
        order_id: Annotated[
            int,
            ydb.ModelField(
                ydb_type=ydb.PrimitiveType.Uint64,
                column_name="id",
            ),
        ]

    result = driver.table_client.read_rows(
        "/local/orders",
        [OrderKey(1)],
    )
    orders = result.rows_as(Order)

Use ``key_model=OrderKey`` when the key list is empty. ``read_table`` keeps its
existing signature; each returned ``ResultSet`` supports ``rows_as`` and
``iter_rows_as``.

All APIs have the same model behaviour in ``ydb.aio``. Query model parameters are
supported by the Query service. The legacy ``execute_yql`` and input parameters of
``scan_query`` do not perform model inference. Topic serialization is outside this
feature.


Pydantic
--------

Pydantic models use the same annotations and ``ModelField`` metadata:

.. code-block:: python

    from pydantic import BaseModel

    class OrderModel(BaseModel):
        order_id: Annotated[
            int,
            ydb.ModelField(
                ydb_type=ydb.PrimitiveType.Uint64,
                column_name="id",
            ),
        ]
        customer: str
        created_at: datetime.datetime

    orders = result_set.rows_as(OrderModel)

See ``examples/typed-models`` in the source distribution for a complete local
example.
