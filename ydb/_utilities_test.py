import pytest

from ydb._utilities import check_module_exists
from ydb._utilities import x_ydb_sdk_build_info_header
from .ydb_version import VERSION


@pytest.mark.parametrize(
    "path,result",
    [("sys", True), ("ydb", True), ("ydb.some.module.unexisted.test", False)],
)
def test_check_module_exists(path, result):
    assert check_module_exists(path) == result


def test_x_ydb_sdk_build_info_header():
    assert x_ydb_sdk_build_info_header(()) == ("x-ydb-sdk-build-info", "ydb-python-sdk/" + VERSION)
    assert x_ydb_sdk_build_info_header(("lib1/0.1.0",)) == (
        "x-ydb-sdk-build-info",
        "ydb-python-sdk/" + VERSION + ";lib1/0.1.0",
    )
    assert x_ydb_sdk_build_info_header(("lib1/0.1.0", "lib2/0.2.0")) == (
        "x-ydb-sdk-build-info",
        "ydb-python-sdk/" + VERSION + ";lib1/0.1.0;lib2/0.2.0",
    )
