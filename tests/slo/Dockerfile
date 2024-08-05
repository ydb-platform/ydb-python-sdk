FROM python:3.8
COPY . /src
WORKDIR /src
RUN python -m pip install --upgrade pip && python -m pip install -e . && python -m pip install -r tests/slo/requirements.txt
WORKDIR tests/slo
ARG SDK_SERVICE

ENTRYPOINT ["python", "src"]
