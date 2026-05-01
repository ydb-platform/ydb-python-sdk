import subprocess
import sys

import pytest

import ydb

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


def test_iam_is_available_from_ydb_package():
    assert ydb.iam.ServiceAccountCredentials is not None


def test_iam_is_loaded_lazily():
    code = (
        "import sys, ydb; "
        "print('iam' in dir(ydb)); "
        "print(hasattr(ydb, 'importlib')); "
        "print('ydb.iam' in sys.modules); "
        "ydb.iam; "
        "print('ydb.iam' in sys.modules)"
    )
    output = subprocess.check_output([sys.executable, "-c", code], text=True)

    assert output.splitlines() == ["True", "False", "False", "True"]
