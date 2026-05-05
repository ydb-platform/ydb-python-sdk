# AGENTS.md — YDB Python SDK

Official Python client for [YDB](https://ydb.tech/) — a fault-tolerant distributed SQL DBMS.

---

## Project Structure

| Path | Purpose |
|------|---------|
| `ydb/` | Synchronous client — canonical implementation |
| `ydb/aio/` | Async client — mirrors `ydb/` API exactly |
| `ydb/_grpc/v3/` … `v6/` | **Auto-generated protobuf stubs — never edit** |
| `ydb/*_test.py` | Unit tests (fast, no Docker required) |
| `tests/` | Integration tests (require Docker, auto-started by pytest) |
| `examples/` | Usage examples |
| `docs/` | User-facing documentation |

## Development Environment

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -e . tox
```

**Always activate the virtual environment before running any project commands.**

## Code Quality

```sh
# Auto-fix formatting
tox -e black-format

# Check formatting
tox -e black

# Style (flake8)
tox -e style

# Type checking
tox -e mypy
```

Before submitting a PR, run all checks and unit tests:
```sh
tox -e black && tox -e style && tox -e mypy && tox -e py -- ydb -v
```

## Testing

```sh
# Unit tests — fast, no Docker needed
source .venv/bin/activate && tox -e py -- ydb -v

# Integration tests — Docker started automatically by pytest-docker, do NOT start it manually
source .venv/bin/activate && tox -e py -- tests -v

# Single test file
source .venv/bin/activate && tox -e py -- tests/path/to/test_file.py -v
```

**Always run the relevant tests after implementing a feature or fix.**

## Key Rules

1. **Backward compatibility** — never break the public API; only extend it.
2. **Sync/async parity** — every change in `ydb/` must be mirrored in `ydb/aio/`.
3. **Tests required** — all changes must have tests; add to existing test files, do not create new ones.
4. **No new dependencies** — the current dependency set is intentionally minimal.
5. **No excessive comments** — do not comment self-evident code.
6. **English only** — code, comments, docstrings, commit messages.
7. **Python 3.8+** — do not use language or stdlib features beyond that baseline.

## Documentation & Examples

- Update `docs/` for any user-facing changes; create new sections if needed.
- Extend `examples/` when adding new features.
- **After every change to `docs/`**, rebuild the HTML output and verify there are no new errors:
  ```sh
  source .venv/bin/activate && sphinx-build -b html docs docs/_build/html -q
  ```

## Auto-generated Files — Do NOT Edit

```
ydb/_grpc/v3/
ydb/_grpc/v4/
ydb/_grpc/v5/
ydb/_grpc/v6/
```

To regenerate protobuf stubs: see `Makefile` and `generate-protobuf.Dockerfile`.

---

## Topic Chaos Testing (SLO)

Run this only for changes that affect topic reader/writer reconnection logic.

**1. Start YDB with chaos** (kills a DB node every ~20 seconds):
```sh
docker compose -f tests/slo/playground/configs/compose.yaml up -d
```

**2. Wait until YDB is healthy:**
```sh
docker ps --format "table {{.Names}}\t{{.Status}}" | grep ydb
```

**3. Activate virtual environment** (from `tests/slo/` directory):
```sh
source ../../.venv/bin/activate
```

**4. Test writer** (60 sec):
```sh
python ./src grpc://localhost:2135 /Root/testdb \
    --workload-name topic --topic-path /Root/testdb/slo_topic \
    --otlp-endpoint "" --read-threads 0 --write-rps 1 \
    --time 60 --debug
```

**5. Test reader** (60 sec):
```sh
python ./src grpc://localhost:2135 /Root/testdb \
    --workload-name topic --topic-path /Root/testdb/slo_topic \
    --otlp-endpoint "" --read-rps 1 --write-rps 1 \
    --time 60 --debug
```

**6. Tear down:**
```sh
docker compose -f tests/slo/playground/configs/compose.yaml down
```

**Success criteria:** writer and reader reconnect automatically during node restarts with no fatal errors.
