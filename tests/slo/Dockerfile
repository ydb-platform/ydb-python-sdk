FROM python:3.8-slim
COPY . /src
WORKDIR /src
RUN python -m pip install --no-cache-dir --upgrade pip && \
    python -m pip install --no-cache-dir -e . && \
    python -m pip install --no-cache-dir -r tests/slo/requirements.txt
WORKDIR tests/slo
ARG SDK_SERVICE
ENV SDK_SERVICE=$SDK_SERVICE

ENTRYPOINT ["python", "src"]
