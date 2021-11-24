from ydb.iam import *  # noqa
import sys

sys.modules['kikimr.public.sdk.python.iam.auth'] = sys.modules['ydb.iam.auth']
