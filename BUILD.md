## How to build and test ydb-python-sdk

This document has detailed instructions on how to build ydb-python-sdk from source and run style and unit tests.

### Pre-requisites

- Install [Docker](https://docs.docker.com/engine/install/).
- Install [Python](https://docs.python.org/3.8/)
- Install [pip](https://pip.pypa.io/en/latest/installation/)
- Install [Tox](https://tox.wiki/en/latest/installation.html)

### Clone the repository

```sh
git clone https://github.com/ydb-platform/ydb-python-sdk
```

### Run style tests

Use the command below to prepare `virtualenv` and to run style tests using `flake8`.

```sh
tox -e style
```

### Run formatting checks

Use the command below to prepare `virtualenv` and to run style tests using `black`.
See [documentation](https://black.readthedocs.io/en/stable/) about Black project.

```sh
tox -e black
```

To automatically format code using the `black` formatting style, use the command below.

```sh
tox -e black-format
```

### Run unit tests

Use the command below to run unit tests.

```sh
tox -e py -- ydb
```

### Run integration tests

Use the command below to run integration tests.

```sh
tox -e py -- tests
```

### Regenerate protobuf

Use the command below for regenerate protobuf code.

```sh
make protobuf
```