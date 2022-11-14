import sys

import google.protobuf
from packaging.version import Version

# generated files are incompatible between 3 and 4 protobuf versions
# import right generated version for current protobuf lib
# sdk code must always import from ydb._grpc.common
protobuf_version = Version(google.protobuf.__version__)

if protobuf_version < Version("4.0"):
    from ydb._grpc.v3 import * # noqa
    from ydb._grpc.v3 import protos # noqa
    sys.modules["ydb._grpc.common"] = sys.modules["ydb._grpc.v3"]
    sys.modules["ydb._grpc.common.protos"] = sys.modules["ydb._grpc.v3.protos"]
else:
    from ydb._grpc.v4 import * # noqa
    from ydb._grpc.v4 import protos # noqa
    sys.modules["ydb._grpc.common"] = sys.modules["ydb._grpc.v4"]
    sys.modules["ydb._grpc.common.protos"] = sys.modules["ydb._grpc.v4.protos"]
