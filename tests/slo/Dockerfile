# syntax=docker/dockerfile:1

# This image packages the Python SLO workload runner.
#
# All settings are CLI arguments with env-var fallback (CLI arg > env var > default):
#   endpoint              $YDB_ENDPOINT                 grpc://ydb:2136
#   db                    $YDB_DATABASE                 /Root/testdb
#   --workload-name       $WORKLOAD_NAME                sync-query
#   --workload-ref        $WORKLOAD_REF / $REF          main
#   --otlp-endpoint       $OTEL_EXPORTER_OTLP_ENDPOINT  http://ydb-prometheus:9090/api/v1/otlp
#   --time                $WORKLOAD_DURATION            600
#
# Example:
#   docker run --rm <image> grpc://ydb:2136 /Root/testdb --workload-name topic --time 120
#
# Notes:
# - OpenTelemetry 1.39.x requires Python >= 3.9.

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

# 3. Workload source
COPY tests/slo/src /src/tests/slo/src

ENTRYPOINT ["python", "./tests/slo/src"]

CMD ["--read-rps", "1000", "--write-rps", "100"]
