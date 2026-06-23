# The *_pb2.py / *_pb2_grpc.py stubs are produced by the protoc that ships INSIDE
# grpcio-tools (generate_protoc.py -> grpc_tools.command.build_package_protos uses the
# bundled protoc, NOT a standalone one). Therefore GRPCIO_VER is the ONLY knob that
# controls the generated gencode version and, for protobuf >= 6, its embedded
# runtime-version floor. grpcio-tools pulls a compatible protobuf runtime transitively.
#
#   grpcio-tools 1.39.0 -> protoc 3.17 -> protobuf 3.x old-style gencode         (v3)
#   grpcio-tools 1.50.0 -> protoc 21.x -> protobuf 4.21 builder gencode          (v4, v5)
#   grpcio-tools 1.72.1 -> protoc 30.0 -> protobuf 6.30.0 gencode (floor 6.30.0) (v6)
FROM python:3.9.15
ARG GRPCIO_VER=1.50.0
RUN python -m pip install --upgrade pip && \
    python -m pip install "grpcio-tools==${GRPCIO_VER}"
# Surface the real protoc version that will generate the stubs (catches silent drift).
RUN python -m grpc_tools.protoc --version
