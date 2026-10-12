# syntax=docker/dockerfile:1

# This image packages the Python SLO workload runner for ydb-slo-action v2.
#
# The action launches the same image for `current` and `baseline` workloads
# in parallel and injects these env vars (see tests/slo/docker-entrypoint.sh):
#
#   WORKLOAD_NAME             sync-table | sync-query | topic
#   WORKLOAD_REF              "current" / "main" — used as the `ref` metric label
#   WORKLOAD_DURATION         seconds
#   YDB_ENDPOINT              grpc://ydb:2136
#   YDB_DATABASE              /Root/testdb
#   OTEL_EXPORTER_OTLP_ENDPOINT / _METRICS_ENDPOINT
#
# `workload_current_command` from the action is appended to the `*-run` call
# as tuning flags (--read-rps, --write-rps, ...).
#
# Notes:
# - OpenTelemetry 1.39.x requires Python >= 3.9.
# - gcc/libc6-dev are needed to build hdrhistogram from sdist.

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /src

# 1. YDB SDK
COPY setup.py pyproject.toml README.md requirements.txt ./
COPY ydb/ ydb/
RUN pip install --no-cache-dir .

# 2. SLO deps
COPY tests/slo/requirements.txt tests/slo/requirements.txt
RUN pip install --no-cache-dir -r tests/slo/requirements.txt

# 3. Workload source + entrypoint
COPY tests/slo/src /src/tests/slo/src
COPY tests/slo/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
