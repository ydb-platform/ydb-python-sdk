from ydb._grpc import *  # noqa
import sys
import warnings

sys.modules["ydb.public.api.protos"] = sys.modules["ydb._grpc.protos"]
warnings.warn(
    "using ydb.public.api.protos module is deprecated. Don't use direct grpc dependencies."
)
