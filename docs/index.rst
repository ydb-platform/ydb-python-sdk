YDB Python SDK
==============

Python client for `YDB <https://ydb.tech/>`_ — a fault-tolerant distributed SQL database.

.. toctree::
   :hidden:
   :caption: Getting Started

   overview
   quickstart

.. toctree::
   :hidden:
   :caption: Connecting

   driver

.. toctree::
   :hidden:
   :caption: Services

   query
   topic
   table
   coordination
   scheme

.. toctree::
   :hidden:
   :caption: Reference

   types
   errors
   apireference


New to the SDK?
---------------

Start with :doc:`quickstart` — it shows how to install the package, connect to a
database, and run your first query in under five minutes.

Then read :doc:`driver` to understand how to configure the connection: which endpoint
and database to use, how to authenticate, and how to set up TLS. Every service in the
SDK is accessed through a ``Driver`` instance, so this page is the foundation for
everything else.


Running Queries
---------------

The :doc:`query` page covers the Query service — the primary API for executing YQL
statements. It explains ``QuerySessionPool``, how to run DDL and DML, how to pass
parameters safely, and how to work with transactions. Start here if you want to read
or write data.

The :doc:`types` page is a companion to query: it shows how Python values map to YDB
types and how to specify types explicitly when the automatic mapping is not enough.


Messaging
---------

The :doc:`topic` page covers the Topic service — a persistent message queue similar to
Kafka. It explains how to create topics, write messages, read and commit them, and how
topics integrate with transactions. Both synchronous and asynchronous patterns are
covered.


Table Service
-------------

The :doc:`table` page covers ``driver.table_client`` — the lower-level API for
operations that cannot be expressed in YQL: creating tables with custom partitioning,
TTL, secondary indexes, and column families; bulk loading data with ``bulk_upsert``;
and streaming full-table reads with ``read_table`` or ``scan_query``. Use this
alongside the Query service when you need fine-grained schema or data-loading control.


Distributed Coordination
------------------------

The :doc:`coordination` page covers distributed semaphores and leader election. If you
need to limit concurrent access to a shared resource across multiple processes or hosts,
this is the service to use.

Schema Management
-----------------

The :doc:`scheme` page covers ``driver.scheme_client`` — creating and removing
directories, listing directory contents, and describing any path in the YDB hierarchy
(tables, topics, coordination nodes, etc.).


Error Handling and Retries
--------------------------

The :doc:`errors` page is important reading before going to production. YDB returns
structured error codes, and the SDK's retry logic depends on them. This page explains
which errors are safe to retry, which are not, how to tune backoff settings, and how to
use the ``@ydb_retry`` decorator. Skipping this section is a common source of production
incidents.


API Reference
-------------

The :doc:`apireference` page contains auto-generated documentation for all public
classes and methods.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
