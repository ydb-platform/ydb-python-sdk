# -*- coding: utf-8 -*-
from kikimr.public.sdk.python.client import issues


class Operation(object):
    __slots__ = ()

    def __init__(self, operation, *args, **kwargs):
        # implement proper interface a bit later
        issues._process_response(operation)
