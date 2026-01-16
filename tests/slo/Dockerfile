# syntax=docker/dockerfile:1

# This image packages the Python SLO workload runner.
# It expects to be run with arguments like:
#   docker run --rm <image> table-run <endpoint> <db> --otlp-endpoint http://prometheus:9090/api/v1/otlp/v1/metrics ...
#
# Notes:
# - OpenTelemetry 1.39.x requires Python >= 3.9.
# - The entrypoint is `python ./tests/slo/src`, i.e. it runs the `__main__.py`
#   from that directory (same as `python tests/slo/src ...` in CI).

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
