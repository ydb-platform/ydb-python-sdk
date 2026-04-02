# syntax=docker/dockerfile:1

# This image packages the Python SLO workload runner.
#
# Connection and workload identity are configured via environment variables:
#   YDB_ENDPOINT          grpc://ydb:2136
#   YDB_DATABASE          /Root/testdb
#   WORKLOAD_DURATION     600
#   WORKLOAD_NAME         sync-query | sync-table | topic
#   WORKLOAD_REF          <branch/ref label for metrics>
#   OTEL_EXPORTER_OTLP_METRICS_ENDPOINT  http://ydb-prometheus:9090/api/v1/otlp/v1/metrics
#
# Additional tuning flags (read/write RPS, timeouts, thread counts) are passed via
# the Docker CMD, e.g.:
#   docker run --rm --env-file ... <image> --read-rps 1000 --write-rps 100
#
# Notes:
# - OpenTelemetry 1.39.x requires Python >= 3.9.

FROM python:3.11-slim AS build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /src
COPY . /src

# Install runtime deps into an isolated venv so we can copy it into the final stage.
RUN python -m venv /opt/venv \
    && /opt/venv/bin/python -m pip install --no-cache-dir --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir . \
    && /opt/venv/bin/pip install --no-cache-dir -r tests/slo/requirements.txt


FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:${PATH}"

WORKDIR /app

COPY --from=build /opt/venv /opt/venv
COPY --from=build /src/tests/slo/src /app/tests/slo/src

ENTRYPOINT ["python", "./tests/slo/src"]

CMD ["--read-rps", "1000", "--write-rps", "100"]
