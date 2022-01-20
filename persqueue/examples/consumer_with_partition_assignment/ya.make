OWNER(komels g:logbroker)

PY2_PROGRAM(manual_assignment_consumer_example)
PY_SRCS(
    __main__.py
)
PEERDIR(
    kikimr/public/sdk/python/persqueue
)
END()
