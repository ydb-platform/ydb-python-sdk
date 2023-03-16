## 2.13.0 ##
* fixed in to make compressed backups possible
* Add snapshot to read table responses

## 2.12.4 ##
* Added functions for global change behaviour for compatible with future sdk version: ydb.global_allow_truncated_result and global_allow_split_transactions

## 2.12.3 ##
* Flag for deny split transaction
* Add six package to requirements
* Fixed error while passing date parameter in execute

## 2.12.2 ##
* Fix error of check retriable error for idempotent operations (error exist since 2.12.1)

## 2.12.1 ##
* Supported `TYPE_UNSPECIFIED` item type to scheme ls
* Fixed error while request iam token with bad content type in metadata

## 2.12.0 ##
* Fixed error message while get token from metadata with asyncio iam
* Add `SnapshotReadOnly` transaction mode support to `session.transaction`

## 2.11.1 ##
* Regenerate protobuf code from public api protos (some private protobufs was removed)
* Remove internal S3 client code

## 2.11.0 ##

* removed unused experimental client from ydb python sdk.

## 2.10.0 ##

* fixed double quoting issue in sqlalchemy

## 2.9.0 ##

* fixed minor issue in SDK imports for Python 2.

## 2.7.0 ##

* fixes in TxContext in ydb.aio module.

## 2.6.0 ##

* support `with_native_interval_in_result_sets` flag in the table client.
* support `with_native_timestamp_in_result_sets` flag in the table client.

## 2.4.0 ##

* support query stats in scan query

## 2.2.0 ##

* allow to refer endpoints by node id
* support null type in queries
* support session balancer feature

## 2.1.0 ##

* add compression support to ydb sdk

## 1.1.16 ##

* alias `kikimr.public.sdk.python.client` is deprecated. use `import ydb` instead.
* alias `kikimr.public.api` is deprecated, use `ydb.public.api` instead.
* method `construct_credentials_from_environ` is now deprecated and will be removed in the future.

## 1.1.15 ##

* override the default load balancing policy for discovery endpoint to the `round_robin` policy.

## 1.1.14 ##

* support session graceful shutdown protocol.

## 1.1.11 ##

* speedup driver initialization and first driver.wait

## 1.1.10 ##

 * add methods to request `_apis.TableService.RenameTables` call
 * by now the call is disabled at the server side
 * it will be enabled soon

## 1.1.0 ##

* remove useless `from_bytes` for PY3
* improve performance of column parser

## 1.0.27 ##

* fix bug with prepare in aio

## 1.0.26 ##

* allow specifying column labels in group by in the sqlalchemy dialect

## 1.0.25 ##

* add SEQUENCE to known schema types

## 1.0.22 ##

* add `retry_operation` to `aio.SessionPool`

## 1.0.21 ##

* ydb.aio supports retry operation helper.

## 1.0.20 ##

* storage class support

## 1.0.19 ##

* add async `SessionPool` support

## 1.0.18 ##

* minor change in dbapi

## 1.0.17 ##

* add asyncio support

## 1.0.14 ##

* add some custom datatypes for sqlalchemy

## 1.0.13 ##

* change error format for sqlalchemy

## 1.0.12 ##

* add ``ValueSinceUnixEpochModeSettings`` support to ``TtlSettings``

## 1.0.11 ##

* add default credentials constructor

## 1.0.10 ##

* pass issues to dbapi errors

## 1.0.9 ##

* allow custom user agent

## 1.0.8 ##

* load YDB certificates by default

## 1.0.7 ##

* allow to fail fast on driver wait

## 1.0.6 ##

* disable client query cache by default

## 1.0.3 ##

* support uuid type

## 1.0.1 ##

* Support ``store_size`` in describe of table.

## 1.0.0 ##

* Start initial changelog.
