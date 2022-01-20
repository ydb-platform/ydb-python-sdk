PY23_LIBRARY()

OWNER(g:kikimr)

PY_SRCS(
    __init__.py
    _core.py
    _events.py
    _grpc.py
    _protobuf.py
    _util.py
    auth.py
    errors.py
    channel.py
    grpc_pq_streaming_api.py
    pq_control_plane_client.py
)

IF (PYTHON2)
    PEERDIR(
        contrib/python/enum34
        contrib/python/futures
    )
ENDIF()

PEERDIR(
    contrib/python/protobuf
    contrib/python/six
    kikimr/public/sdk/python/ydb
    kikimr/public/sdk/python/iam
    kikimr/yndx/api/grpc
    kikimr/yndx/api/protos
    ydb/public/api/grpc
    ydb/public/api/grpc/draft
    ydb/public/api/protos
)

END()

RECURSE(
    examples
)
