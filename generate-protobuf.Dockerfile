FROM python:3.9.15
RUN \
    python -m pip install --upgrade pip && \
    python -m pip install grpcio==1.39.0 && \
    python -m pip install grpclib && \
    python -m pip install protobuf==3.20.3 && \
    python -m pip install grpcio-tools==1.38.0

ENV PROTOC_VER=21.8
RUN wget https://github.com/protocolbuffers/protobuf/releases/download/v${PROTOC_VER}/protoc-${PROTOC_VER}-linux-x86_64.zip && \
    unzip protoc-*.zip && \
    rm -f protoc-*.zip && \
    mv bin/protoc /usr/local/bin/protoc && \
    mv include well-known-protos
