YDB API Reference
=================

.. toctree::
   :caption: Contents:


.. module:: ydb

Driver
------

Driver object
~~~~~~~~~~~~~

.. autoclass:: ydb.Driver
    :members:
    :inherited-members:
    :undoc-members:


Driver object (AsyncIO)
~~~~~~~~~~~~~

.. autoclass:: ydb.aio.Driver
    :members:
    :inherited-members:
    :undoc-members:


DriverConfig
~~~~~~~~~~~~

.. autoclass:: ydb.DriverConfig
    :members:
    :inherited-members:
    :undoc-members:
    :exclude-members: database, ca_cert, channel_options, secure_channel, endpoint, endpoints, credentials, use_all_nodes, root_certificates, certificate_chain, private_key, grpc_keep_alive_timeout, table_client_settings, primary_user_agent

------------------------

Query Service
-------------

QuerySessionPool
~~~~~~~~~~~~~~~~

.. autoclass:: ydb.QuerySessionPool
    :members:
    :inherited-members:
    :undoc-members:

QuerySession
~~~~~~~~~~~~~~~~

.. autoclass:: ydb.QuerySession
    :members:
    :inherited-members:
    :undoc-members:

QueryTxContext
~~~~~~~~~~~~~~~~~~

.. autoclass:: ydb.QueryTxContext
    :members:
    :inherited-members:
    :undoc-members:

------------------------

Table Service
-------------

TableClient
~~~~~~~~~~~
.. autoclass:: ydb.TableClient
    :members:
    :inherited-members:
    :undoc-members:

TableClientSettings
~~~~~~~~~~~~~~~~~~~

.. autoclass:: ydb.TableClientSettings
    :members:
    :inherited-members:
    :undoc-members:

Session Pool
~~~~~~~~~~~~

.. autoclass:: ydb.SessionPool
   :members:
   :inherited-members:
   :undoc-members:

Session
~~~~~~~

.. autoclass:: ydb.Session
   :members:
   :inherited-members:
   :undoc-members:

Transaction Context
~~~~~~~~~~~~~~~~~~~

.. autoclass:: ydb.TxContext
   :members:
   :inherited-members:
   :undoc-members:

DataQuery
---------

.. autoclass:: ydb.DataQuery
   :members:
   :inherited-members:
   :undoc-members:

--------------------------

Scheme
------

SchemeClient
~~~~~~~~~~~~

.. autoclass:: ydb.SchemeClient
   :members:
   :inherited-members:
   :undoc-members:

------------------

Result Sets
-----------

.. autoclass:: ydb.convert._ResultSet
   :members:
   :inherited-members:
   :undoc-members:

-----------------------------
