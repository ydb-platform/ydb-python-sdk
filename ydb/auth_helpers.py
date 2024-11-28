# -*- coding: utf-8 -*-
import os


def read_bytes(f):
    with open(f, "rb") as fr:
        return fr.read()


def load_ydb_root_certificate(path:str = None):
    if path is not None and os.path.exists(path):
        return read_bytes(path)
    return None
