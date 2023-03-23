import pytest

from ydb._utilities import check_module_exists


@pytest.mark.parametrize(
    "path,result",
    [("sys", True), ("ydb", True), ("ydb.some.module.unexisted.test", False)],
)
def test_check_module_exists(path, result):
    assert check_module_exists(path) == result
