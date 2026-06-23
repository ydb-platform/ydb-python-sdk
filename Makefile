# protoc version (hence the generated gencode and, for protobuf >= 6, its embedded
# runtime-version floor) is determined SOLELY by the grpcio-tools version pinned via
# GRPCIO_VER below (see generate-protobuf.Dockerfile). Keep this table in sync:
#
#   v3: grpcio-tools 1.39.0 -> protoc 3.17 -> protobuf 3.x old-style  (runs on protobuf >= 3.13)
#   v4: grpcio-tools 1.50.0 -> protoc 21.x -> protobuf 4.21 builder   (no runtime floor)
#   v5: grpcio-tools 1.50.0 -> protoc 21.x -> protobuf 4.21 builder   (no runtime floor; serves 5.x)
#   v6: grpcio-tools 1.72.1 -> protoc 30.0 -> protobuf 6.30.0 gencode (floor 6.30.0, the lowest 6.x)
#
# v5 deliberately uses the same no-floor 4.21 gencode as v4: it maximizes the range of
# installed protobuf 5.x runtimes it tolerates. Raising it to a "true" 5.x gencode would
# only add a runtime-version floor and strand users below it.
protobuf: protobuf-3 protobuf-4 protobuf-5 protobuf-6

protobuf-3:
	docker build -f generate-protobuf.Dockerfile . -t ydb-python-sdk-proto-generator-env-3 --build-arg GRPCIO_VER=1.39.0
	docker run --rm -it -v $${PWD}:$${PWD} -w $${PWD} ydb-python-sdk-proto-generator-env-3 python generate_protoc.py --target-version=v3

protobuf-4:
	docker build -f generate-protobuf.Dockerfile . -t ydb-python-sdk-proto-generator-env-4 --build-arg GRPCIO_VER=1.50.0
	docker run --rm -it -v $${PWD}:$${PWD} -w $${PWD} ydb-python-sdk-proto-generator-env-4 python generate_protoc.py --target-version=v4

protobuf-5:
	docker build -f generate-protobuf.Dockerfile . -t ydb-python-sdk-proto-generator-env-5 --build-arg GRPCIO_VER=1.50.0
	docker run --rm -it -v $${PWD}:$${PWD} -w $${PWD} ydb-python-sdk-proto-generator-env-5 python generate_protoc.py --target-version=v5

protobuf-6:
	docker build -f generate-protobuf.Dockerfile . -t ydb-python-sdk-proto-generator-env-6 --build-arg GRPCIO_VER=1.72.1
	docker run --rm -it -v $${PWD}:$${PWD} -w $${PWD} ydb-python-sdk-proto-generator-env-6 python generate_protoc.py --target-version=v6
