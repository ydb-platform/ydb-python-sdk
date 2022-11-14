FROM python:3.9.15
ENV GRPCLIB_VER=0.4.3
ARG GRPCIO_VER=1.50.0
ARG PY_PROTOBUF_VER=4.21.9
RUN \
    python -m pip install --upgrade pip && \
    python -m pip install grpcio==${GRPCIO_VER} && \
    python -m pip install grpclib==${GRPCLIB_VER} && \
    python -m pip install grpcio-tools==${GRPCIO_VER} && \
    python -m pip install protobuf==${PY_PROTOBUF_VER}

ENV PROTOC_VER=21.8
RUN wget https://github.com/protocolbuffers/protobuf/releases/download/v${PROTOC_VER}/protoc-${PROTOC_VER}-linux-x86_64.zip && \
    unzip protoc-*.zip && \
    rm -f protoc-*.zip && \
    mv bin/protoc /usr/local/bin/protoc && \
    mv include well-known-protos
