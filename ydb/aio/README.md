## Module to integrate ydb python sdk with asyncio

### Preparation
To run code or tests, you must copy directory `kikimr` from [python sdk repo](https://github.com/yandex-cloud/ydb-python-sdk)
and paste it to this directory.

### Tests
During the test run, the docker container with ydb will be launched.
You must install `docker` and `docker-compose` to run this tests

To run test, install test_requirements and run command:
```bash
$ python -m pytest --docker-compose=docker-compose.yml -v
```
