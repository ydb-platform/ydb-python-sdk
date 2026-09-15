from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile
import zipfile

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


@pytest.fixture(scope="module")
def built_distributions(tmp_path_factory):
    dist_dir = tmp_path_factory.mktemp("dist")
    subprocess.run(
        [sys.executable, "-m", "build", "--outdir", str(dist_dir)],
        cwd=Path(__file__).resolve().parent.parent,
        check=True,
    )
    return dist_dir


def test_py_typed_is_in_wheel(built_distributions):
    wheel_path = next(built_distributions.glob("*.whl"))
    with zipfile.ZipFile(wheel_path) as wheel:
        assert "ydb/py.typed" in wheel.namelist()


def test_py_typed_is_in_sdist(built_distributions):
    sdist_path = next(built_distributions.glob("*.tar.gz"))
    with tarfile.open(sdist_path) as sdist:
        assert any(PurePosixPath(member.name).parts[-2:] == ("ydb", "py.typed") for member in sdist.getmembers())
