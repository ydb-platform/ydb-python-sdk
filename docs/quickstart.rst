Quick Start
===========

Installation
------------

Prerequisites
^^^^^^^^^^^^^

* Python 3.8 or higher;
* ``pip`` version 9.0.1 or higher;

If necessary, upgrade your version of ``pip``::

    python -m pip install --upgrade pip

If you cannot upgrade `pip` due to a system-owned installation, you can run the example in a virtualenv::

    python -m pip install virtualenv
    virtualenv venv
    source venv/bin/activate
    python -m pip install --upgrade pip

Installation via Pypi
^^^^^^^^^^^^^^^^^^^^^

To install YDB Python SDK through Pypi execute the following command::

    pip install ydb

Usage
-----

Import ydb package:

.. code-block:: python

    import ydb

Driver initialization:

.. code-block:: python

    endpoint = "grpc://localhost:2136"  # your ydb endpoint
    database = "/local"  # your ydb database

    with ydb.Driver(
        endpoint=endpoint,
        database=database,
        credentials=ydb.credentials_from_env_variables(),
    ) as driver:
        driver.wait(timeout=5, fail_fast=True)


>>> print("hello world")
hello world
