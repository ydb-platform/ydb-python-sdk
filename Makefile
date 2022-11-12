protobuf:
	docker build -f generate-protobuf.Dockerfile . -t ydb-python-sdk-proto-generator-env
	docker run --rm -it -v $${PWD}:$${PWD} -w $${PWD} ydb-python-sdk-proto-generator-env python generate_protoc.py
