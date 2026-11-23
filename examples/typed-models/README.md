# Typed models example

This example uses dataclasses as Query service parameters, `bulk_upsert` rows,
`read_rows` keys, and `ResultSet` output models. If Pydantic is installed, it also
converts the same query result to a Pydantic model.

From the repository root, start the provided local single-node YDB instance:

```bash
docker compose up -d --wait
```

Then run the example:

```bash
export YDB_ANONYMOUS_CREDENTIALS=1
export YDB_ENDPOINT=grpc://localhost:2136
export YDB_DATABASE=/local

python3 -m pip install -e ../..
# Optional Pydantic part:
python3 -m pip install pydantic

python3 main.py
```

The script recreates `/local/typed_models_orders`. Stop the local database when
you are done:

```bash
cd ../..
docker compose down
```
