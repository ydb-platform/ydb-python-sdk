YDB API Reference
=================

.. toctree::
   :caption: Contents:


.. module:: ydb

Driver
------

DriverConfig
^^^^^^^^^^^^

.. autoclass:: ydb.DriverConfig
    :members:
    :inherited-members:
    :undoc-members:
    :exclude-members: database, ca_cert, channel_options, secure_channel, endpoint, endpoints, credentials, use_all_nodes, root_certificates, certificate_chain, private_key, grpc_keep_alive_timeout, table_client_settings, primary_user_agent


Driver
^^^^^^

.. autoclass:: ydb.Driver
    :members:
    :inherited-members:
    :undoc-members:


Driver (AsyncIO)
^^^^^^^^^^^^^^^^

.. autoclass:: ydb.aio.Driver
    :members:
    :inherited-members:
    :undoc-members:

------------------------

Credentials
-----------

AnonymousCredentials
^^^^^^^^^^^^^^^^^^^^

.. autoclass:: ydb.AnonymousCredentials
   :members:
   :undoc-members:

AccessTokenCredentials
^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: ydb.AccessTokenCredentials
   :members:
   :undoc-members:

StaticCredentials
^^^^^^^^^^^^^^^^^

.. autoclass:: ydb.StaticCredentials
   :members:
   :undoc-members:

------------------------

Common
------

BaseRequestSettings
^^^^^^^^^^^^^^^^^^^

.. autoclass:: ydb.BaseRequestSettings
    :members:
    :inherited-members:
    :undoc-members:
    :exclude-members: trace_id, request_type, timeout, cancel_after, operation_timeout, compression, need_rpc_auth, headers, make_copy, tracer


RetrySettings
^^^^^^^^^^^^^

.. autoclass:: ydb.RetrySettings
    :members:
    :inherited-members:
    :undoc-members:


BackoffSettings
^^^^^^^^^^^^^^^

.. autoclass:: ydb.BackoffSettings
   :members:
   :undoc-members:


Result Sets
^^^^^^^^^^^

.. autoclass:: ydb.convert._ResultSet
   :members:
   :inherited-members:
   :undoc-members:


------------------------

Types
-----

PrimitiveType
^^^^^^^^^^^^^

.. autoclass:: ydb.PrimitiveType
   :members:
   :undoc-members:

TypedValue
^^^^^^^^^^

.. autoclass:: ydb.TypedValue
   :members:
   :undoc-members:

OptionalType
^^^^^^^^^^^^

.. autoclass:: ydb.OptionalType
   :members:
   :undoc-members:

ListType
^^^^^^^^

.. autoclass:: ydb.ListType
   :members:
   :undoc-members:

DictType
^^^^^^^^

.. autoclass:: ydb.DictType
   :members:
   :undoc-members:

StructType
^^^^^^^^^^

.. autoclass:: ydb.StructType
   :members:
   :undoc-members:

TupleType
^^^^^^^^^

.. autoclass:: ydb.TupleType
   :members:
   :undoc-members:

DecimalType
^^^^^^^^^^^

.. autoclass:: ydb.DecimalType
   :members:
   :undoc-members:

------------------------

Query Service
-------------

QueryClientSettings
^^^^^^^^^^^^^^^^^^^

.. autoclass:: ydb.QueryClientSettings
    :members:
    :inherited-members:
    :undoc-members:


QuerySessionPool
^^^^^^^^^^^^^^^^

.. autoclass:: ydb.QuerySessionPool
    :members:
    :inherited-members:
    :undoc-members:

QuerySession
^^^^^^^^^^^^

.. autoclass:: ydb.QuerySession
    :members:
    :inherited-members:
    :undoc-members:


QueryTxContext
^^^^^^^^^^^^^^

.. autoclass:: ydb.QueryTxContext
    :members:
    :inherited-members:
    :undoc-members:


QuerySessionPool (AsyncIO)
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: ydb.aio.QuerySessionPool
    :members:
    :inherited-members:
    :undoc-members:


QuerySession (AsyncIO)
^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: ydb.aio.QuerySession
    :members:
    :inherited-members:
    :undoc-members:


QueryTxContext (AsyncIO)
^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: ydb.aio.QueryTxContext
    :members:
    :inherited-members:
    :undoc-members:


Transaction Modes
^^^^^^^^^^^^^^^^^

.. autoclass:: ydb.BaseQueryTxMode
    :members:
    :inherited-members:
    :undoc-members:
    :exclude-members: name, to_proto

.. autoclass:: ydb.QuerySerializableReadWrite
    :members:
    :inherited-members:
    :undoc-members:
    :exclude-members: name, to_proto

.. autoclass:: ydb.QuerySnapshotReadOnly
    :members:
    :inherited-members:
    :undoc-members:
    :exclude-members: name, to_proto

.. autoclass:: ydb.QuerySnapshotReadWrite
    :members:
    :inherited-members:
    :undoc-members:
    :exclude-members: name, to_proto

.. autoclass:: ydb.QueryOnlineReadOnly
    :members:
    :inherited-members:
    :undoc-members:
    :exclude-members: name, to_proto

.. autoclass:: ydb.QueryStaleReadOnly
    :members:
    :inherited-members:
    :undoc-members:
    :exclude-members: name, to_proto


Query Settings
^^^^^^^^^^^^^^

.. autoclass:: ydb.QueryStatsMode
   :members:
   :undoc-members:

.. autoclass:: ydb.QueryResultSetFormat
   :members:
   :undoc-members:

.. autoclass:: ydb.QueryExplainResultFormat
   :members:
   :undoc-members:

.. autoclass:: ydb.ArrowFormatSettings
   :members:
   :undoc-members:

------------------------

Table Service
-------------

TableClient
^^^^^^^^^^^

.. autoclass:: ydb.TableClient
    :members:
    :inherited-members:
    :undoc-members:

TableClientSettings
^^^^^^^^^^^^^^^^^^^

.. autoclass:: ydb.TableClientSettings
    :members:
    :inherited-members:
    :undoc-members:

Session Pool
^^^^^^^^^^^^

.. autoclass:: ydb.SessionPool
   :members:
   :inherited-members:
   :undoc-members:

Session
^^^^^^^

.. autoclass:: ydb.Session
   :members:
   :inherited-members:
   :undoc-members:

Transaction Context
^^^^^^^^^^^^^^^^^^^

.. autoclass:: ydb.TxContext
   :members:
   :inherited-members:
   :undoc-members:

DataQuery
^^^^^^^^^

.. autoclass:: ydb.DataQuery
   :members:
   :inherited-members:
   :undoc-members:

TableDescription
^^^^^^^^^^^^^^^^

.. autoclass:: ydb.TableDescription
   :members:
   :undoc-members:

Column
^^^^^^

.. autoclass:: ydb.Column
   :members:
   :undoc-members:

TableIndex
^^^^^^^^^^

.. autoclass:: ydb.TableIndex
   :members:
   :undoc-members:

TableSchemeEntry
^^^^^^^^^^^^^^^^

.. autoclass:: ydb.TableSchemeEntry
   :members:
   :undoc-members:

DescribeTableSettings
^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: ydb.DescribeTableSettings
   :members:
   :undoc-members:

KeyRange
^^^^^^^^

.. autoclass:: ydb.KeyRange
   :members:
   :undoc-members:

KeyBound
^^^^^^^^

.. autoclass:: ydb.KeyBound
   :members:
   :undoc-members:

BulkUpsertColumns
^^^^^^^^^^^^^^^^^

.. autoclass:: ydb.BulkUpsertColumns
   :members:
   :undoc-members:

TtlSettings
^^^^^^^^^^^

.. autoclass:: ydb.TtlSettings
   :members:
   :undoc-members:

PartitioningSettings
^^^^^^^^^^^^^^^^^^^^

.. autoclass:: ydb.PartitioningSettings
   :members:
   :undoc-members:

ColumnFamily
^^^^^^^^^^^^

.. autoclass:: ydb.ColumnFamily
   :members:
   :undoc-members:

FeatureFlag
^^^^^^^^^^^

.. autoclass:: ydb.FeatureFlag
   :members:
   :undoc-members:

ColumnUnit
^^^^^^^^^^

.. autoclass:: ydb.ColumnUnit
   :members:
   :undoc-members:

Compression
^^^^^^^^^^^

.. autoclass:: ydb.Compression
   :members:
   :undoc-members:

--------------------------

Topic Service
-------------

TopicClient
^^^^^^^^^^^

.. autoclass:: ydb.TopicClient
   :members:
   :inherited-members:
   :undoc-members:

TopicClientSettings
^^^^^^^^^^^^^^^^^^^

.. autoclass:: ydb.TopicClientSettings
   :members:
   :inherited-members:
   :undoc-members:

TopicConsumer
^^^^^^^^^^^^^

.. autoclass:: ydb.TopicConsumer
   :members:
   :undoc-members:

TopicCodec
^^^^^^^^^^

.. autoclass:: ydb.TopicCodec
   :members:
   :undoc-members:

TopicWriterMessage
^^^^^^^^^^^^^^^^^^

.. autoclass:: ydb.TopicWriterMessage
   :members:
   :undoc-members:

TopicReaderSelector
^^^^^^^^^^^^^^^^^^^

.. autoclass:: ydb.TopicReaderSelector
   :members:
   :undoc-members:

TopicAutoPartitioningSettings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: ydb.TopicAutoPartitioningSettings
   :members:
   :undoc-members:

TopicAutoPartitioningStrategy
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: ydb.TopicAutoPartitioningStrategy
   :members:
   :undoc-members:

--------------------------

Coordination Service
--------------------

NodeConfig
^^^^^^^^^^

.. autoclass:: ydb.coordination.NodeConfig
   :members:
   :undoc-members:

ConsistencyMode
^^^^^^^^^^^^^^^

.. autoclass:: ydb.coordination.ConsistencyMode
   :members:
   :undoc-members:

RateLimiterCountersMode
^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: ydb.coordination.RateLimiterCountersMode
   :members:
   :undoc-members:

--------------------------

Scheme
------

SchemeClient
^^^^^^^^^^^^

.. autoclass:: ydb.SchemeClient
   :members:
   :inherited-members:
   :undoc-members:

SchemeEntry
^^^^^^^^^^^

.. autoclass:: ydb.SchemeEntry
   :members:
   :undoc-members:

SchemeEntryType
^^^^^^^^^^^^^^^

.. autoclass:: ydb.SchemeEntryType
   :members:
   :undoc-members:

--------------------------

Errors
------

.. autoclass:: ydb.Error
   :members:
   :undoc-members:

.. autoclass:: ydb.BadRequest
   :undoc-members:

.. autoclass:: ydb.Unauthorized
   :undoc-members:

.. autoclass:: ydb.Unauthenticated
   :undoc-members:

.. autoclass:: ydb.Aborted
   :undoc-members:

.. autoclass:: ydb.Unavailable
   :undoc-members:

.. autoclass:: ydb.Overloaded
   :undoc-members:

.. autoclass:: ydb.SchemeError
   :undoc-members:

.. autoclass:: ydb.GenericError
   :undoc-members:

.. autoclass:: ydb.Timeout
   :undoc-members:

.. autoclass:: ydb.BadSession
   :undoc-members:

.. autoclass:: ydb.AlreadyExists
   :undoc-members:

.. autoclass:: ydb.NotFound
   :undoc-members:

.. autoclass:: ydb.Undetermined
   :undoc-members:

.. autoclass:: ydb.ConnectionError
   :undoc-members:

.. autoclass:: ydb.ConnectionFailure
   :undoc-members:

.. autoclass:: ydb.ConnectionLost
   :undoc-members:

.. autoclass:: ydb.SessionPoolEmpty
   :undoc-members:

.. autoclass:: ydb.DeadlineExceed
   :undoc-members:
