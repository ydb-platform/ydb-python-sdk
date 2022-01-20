PY23_LIBRARY()

OWNER(g:kikimr)

PY_SRCS(
    __init__.py
)

PEERDIR(
    kikimr/public/sdk/python/ydb/iam
)

END()
