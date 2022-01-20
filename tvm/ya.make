PY23_LIBRARY()
OWNER(g:kikimr)

PY_SRCS(
    __init__.py
    auth.py
)

PEERDIR(
    kikimr/public/sdk/python/ydb
    library/python/tvmauth
)

END()
