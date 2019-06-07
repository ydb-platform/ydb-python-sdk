# -*- coding: utf-8 -*-
from . import issues


class Operation(object):
    __slots__ = ()

    def __init__(self, rpc_state, operation, *args, **kwargs):
        # implement proper interface a bit later
        issues._process_response(operation)
