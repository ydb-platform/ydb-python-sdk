OWNER(komels g:logbroker)

PY2_PROGRAM(simple_consumer_example)
PY_SRCS(
    __main__.py
)
PEERDIR(
    kikimr/public/sdk/python/persqueue
)
END()
