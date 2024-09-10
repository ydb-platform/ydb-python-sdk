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
^^^^^^^^^^^^^^^

.. autoclass:: ydb.aio.Driver
    :members:
    :inherited-members:
    :undoc-members:

------------------------

Common
-------------

BaseRequestSettings
^^^^^^^^^^^^^^^^^^^

.. autoclass:: ydb.BaseRequestSettings
    :members:
    :inherited-members:
    :undoc-members:
    :exclude-members: trace_id, request_type, timeout, cancel_after, operation_timeout, compression, need_rpc_auth, headers, make_copy, tracer


Result Sets
^^^^^^^^^^^

.. autoclass:: ydb.convert._ResultSet
   :members:
   :inherited-members:
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


Query Tx Mode
^^^^^^^^^^^^^

.. autoclass:: ydb.BaseQueryTxMode
    :members:
    :inherited-members:
    :undoc-members:
    :exclude-members: name, to_proto


.. autoclass:: ydb.QueryOnlineReadOnly
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


.. autoclass:: ydb.QueryStaleReadOnly
    :members:
    :inherited-members:
    :undoc-members:
    :exclude-members: name, to_proto


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

--------------------------

Scheme
------

SchemeClient
^^^^^^^^^^^^

.. autoclass:: ydb.SchemeClient
   :members:
   :inherited-members:
   :undoc-members:

------------------

