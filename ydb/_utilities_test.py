import hashlib
from pathlib import Path, PurePosixPath
import ssl
import subprocess
import sys
import tarfile
import zipfile

import pytest

import ydb
from ydb import default_pem

from ydb._utilities import check_module_exists
from ydb._utilities import get_first_message_with_timeout
from ydb._utilities import x_ydb_sdk_build_info_header
from .ydb_version import VERSION


@pytest.mark.parametrize(
    "fingerprint",
    [
        pytest.param(
            "d7a7a0fb5d7e2731d771e9484ebcdef71d5f0c3e0a2948782bc83ee0ea699ef4",
            id="aaa-certificate-services",
        ),
        pytest.param(
            "86a1ecba089c4a8d3bbe2734c612ba341d813e043cf9e8a862cd5c57a36bbe6b",
            id="emsign-ecc-root-ca-g3",
        ),
    ],
)
def test_default_ca_bundle_excludes_distrusted_roots(fingerprint):
    certificates = "\n".join(
        line for line in default_pem.load_default_pem().decode("utf-8").splitlines() if not line.startswith("#")
    )
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.load_verify_locations(cadata=certificates)
    fingerprints = {hashlib.sha256(cert).hexdigest() for cert in context.get_ca_certs(binary_form=True)}

    assert fingerprints
    assert fingerprint not in fingerprints


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


def test_get_first_message_with_timeout_returns_first_message():
    assert get_first_message_with_timeout(iter(["first", "second"]), timeout=5) == "first"


def test_get_first_message_with_timeout_reraises_stream_error():
    error = ydb.issues.Unavailable("Socket closed")

    def stream():
        raise error
        yield

    with pytest.raises(ydb.issues.Unavailable) as exc_info:
        get_first_message_with_timeout(stream(), timeout=5)
    assert exc_info.value is error


def test_convert_floats_to_embedding_bytes_encodes_float32_values():
    assert ydb.convert_floats_to_embedding_bytes([1, -2, 0.5]) == bytes.fromhex("0000803f000000c00000003f01")


def test_convert_floats_to_embedding_bytes_converts_integers_to_float32():
    assert ydb.convert_floats_to_embedding_bytes([16777217, -2]) == bytes.fromhex("0000804b000000c001")


def test_convert_floats_to_embedding_bytes_converts_float64_to_float32():
    assert ydb.convert_floats_to_embedding_bytes([1.00000001]) == bytes.fromhex("0000803f01")


def test_convert_floats_to_embedding_bytes_rejects_empty_values():
    with pytest.raises(ValueError, match="embedding must not be empty"):
        ydb.convert_floats_to_embedding_bytes([])


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
