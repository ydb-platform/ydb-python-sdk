# Isolated image for the OpenTelemetry demo scripts. Build context is the repository root.
#
#   docker compose -f examples/opentelemetry/compose-e2e.yaml build
#
# A separate ``.dockerignore`` at the repo root keeps the context small.

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Dependency layer: copy only what setup.py needs so changes to the demo script do
# not bust the cached pip install.
COPY setup.py pyproject.toml README.md requirements.txt ./
COPY ydb ./ydb
COPY examples/opentelemetry/requirements.txt ./examples/opentelemetry/requirements.txt
RUN pip install --no-cache-dir -e '.[opentelemetry]' -r examples/opentelemetry/requirements.txt

# Demo scripts.
COPY examples/opentelemetry/otel_example.py ./examples/opentelemetry/otel_example.py
COPY examples/opentelemetry/load_tank.py ./examples/opentelemetry/load_tank.py
COPY examples/opentelemetry/metrics_views.py ./examples/opentelemetry/metrics_views.py
