# Topic examples for ydb.tech

These applications supply the synchronous and asynchronous Python snippets in the
topic reference on ydb.tech. They use the SDK from this checkout.

From the repository root, with a local YDB instance:

```sh
python -m pip install -e .
python ydb_tech/topic/sync_example.py
python ydb_tech/topic/async_example.py
```

`YDB_ENDPOINT` defaults to `grpc://localhost:2136` and `YDB_DATABASE` to `/local`.
The applications create unique topics, verify payloads and metadata, exercise
commit variants and transactions, and remove their topics afterwards.
Read and write waits are bounded; errors cause a nonzero exit.
