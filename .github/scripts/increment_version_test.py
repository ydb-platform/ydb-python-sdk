import pytest

from .increment_version import VersionLine

@pytest.mark.parametrize(
    "source,inc_type,with_beta,result",
    [
        ("0.0.0", 'patch', False, "0.0.1"),
        ("0.0.1", 'patch', False, "0.0.2"),
        ("0.0.1b1", 'patch', False, "0.0.1"),
        ("0.0.0", 'patch', True, "0.0.1b1"),
        ("0.0.1", 'patch', True, "0.0.2b1"),
        ("0.0.2b1", 'patch', True, "0.0.2b2"),
        ("0.0.1", 'minor', False, "0.1.0"),
        ("0.0.1b1", 'minor', False, "0.1.0"),
        ("0.1.0b1", 'minor', False, "0.1.0"),
        ("0.1.0", 'minor', True, "0.2.0b1"),
        ("0.1.0b1", 'minor', True, "0.1.0b2"),
        ("0.1.1b1", 'minor', True, "0.2.0b1"),
        ("3.0.0b1", 'patch', True, "3.0.0b2"),
    ]
)
def test_increment_version(source, inc_type, with_beta, result):
    version = VersionLine("", source)
    version.increment(inc_type, with_beta)
    incremented = str(version)
    assert incremented == result

