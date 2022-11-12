from ydb._grpc.protos import *  # noqa
import sys
import warnings

sys.modules["ydb.public.api.grpc"] = sys.modules["ydb._grpc"]
warnings.warn(
    "using ydb.public.api.grpc module is deprecated. Don't use direct grpc dependencies."
)
