# Isolated image for the OpenTelemetry demo. Build context is the repository root.
#
#   docker compose -f examples/opentelemetry/compose-e2e.yaml build otel-example
#
# A separate ``.dockerignore`` at the repo root keeps the context small.

FROM python:3.11-slim

WORKDIR /app

# Dependency layer: copy only what setup.py needs so changes to the demo script do
# not bust the cached pip install.
COPY setup.py pyproject.toml README.md requirements.txt ./
COPY ydb ./ydb
COPY examples/opentelemetry/requirements.txt ./examples/opentelemetry/requirements.txt
RUN pip install --no-cache-dir -e '.[opentelemetry]' -r examples/opentelemetry/requirements.txt

# Demo script.
COPY examples/opentelemetry/otel_example.py ./examples/opentelemetry/otel_example.py

CMD ["python", "examples/opentelemetry/otel_example.py"]
