OWNER(komels g:logbroker)

PY2_PROGRAM(producer_example)
PY_SRCS(
    __main__.py
)
PEERDIR(
    kikimr/public/sdk/python/persqueue
)
END()
