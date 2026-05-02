# OpenTelemetry example (YDB Python SDK)

Async demo in [`otel_example.py`](otel_example.py): OTLP export, `enable_tracing()`,
`app_startup` and `example_tli` application spans, bank table, Serializable transactions (TLI-style load).

Most steps assume the **repository root** as the current directory; the install step also shows the variant from this folder.

## 1. Start YDB (or the full stack) with Docker **first**

Without running containers, the example has nothing to connect to.

**Only YDB** (minimal `docker-compose.yml` in the repo root — enough for the script on the host):

```sh
cd /path/to/ydb-python-sdk
docker compose up -d
# wait until the ydb container is healthy / port 2136 is open, then continue
```

**Full stack** (YDB + OTLP collector + Tempo + Grafana; the `otel-example` service is built from a `Dockerfile` and runs the script once inside Compose). The compose file is `compose-e2e.yaml` next to this README.

```sh
cd /path/to/ydb-python-sdk
docker compose -f examples/opentelemetry/compose-e2e.yaml up --build
```

From this folder the build context is still resolved correctly (it is `../..` relative to the compose file):

```sh
cd /path/to/ydb-python-sdk/examples/opentelemetry
docker compose -f compose-e2e.yaml up --build
```

The first run builds the `otel-example` image from the local SDK source (`Dockerfile` in this folder, `.dockerignore` at the repo root keeps the context small). Subsequent runs reuse the cached image; pass `--build` if you change the SDK or the demo script.

Grafana: http://localhost:3000

**Logs for `otel-example`:** the container name is prefixed (e.g. `opentelemetry-otel-example-1`); use `docker compose -f examples/opentelemetry/compose-e2e.yaml ps` or `docker ps -a` to find it. The service is one-shot (`restart: "no"`) — it may already have exited.

## 2. Install dependencies (on the host, for a local `python` run)

**From the repository root** (editable SDK + pins from this example):

```sh
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e '.[opentelemetry]' -r examples/opentelemetry/requirements.txt
```

**If your shell is already in** `examples/opentelemetry/` (same result):

```sh
pip install -e '../..[opentelemetry]' -r requirements.txt
```

`requirements.txt` includes a merge of the repository’s core `requirements.txt` (grpc, ``packaging``, …) plus the OpenTelemetry lines. The `-e` install is only needed to register the package; otherwise this example prepends the repo to ``sys.path``.

**Without** `pip -e` (``ydb`` from the checkout via `sys.path`): from this directory run `pip install -r requirements.txt`, then ``python otel_example.py``.

## 3. Run the example (after YDB from step 1 is up)

```sh
python examples/opentelemetry/otel_example.py
```

Defaults: YDB `grpc://localhost:2136`, OTLP `http://localhost:4317` (for a local collector, if you use one).

## Environment (Docker / overrides)

| Variable | Meaning |
|----------|---------|
| `YDB_ENDPOINT` | e.g. `grpc://ydb:2136` inside the Compose network |
| `YDB_DATABASE` | default `/local` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | e.g. `http://otel-collector:4317` |
