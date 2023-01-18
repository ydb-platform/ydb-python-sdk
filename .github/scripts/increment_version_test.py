import pytest

from .increment_version import VersionLine

@pytest.mark.parametrize(
    "source,inc_type,with_beta,result",
    [
        ("0.0.0", 'patch', False, "0.0.1"),
        ("0.0.1", 'patch', False, "0.0.2"),
        ("0.0.1a1", 'patch', False, "0.0.1"),
        ("0.0.0", 'patch', True, "0.0.1a1"),
        ("0.0.1", 'patch', True, "0.0.2a1"),
        ("0.0.2a1", 'patch', True, "0.0.2a2"),
        ("0.0.1", 'minor', False, "0.1.0"),
        ("0.0.1a1", 'minor', False, "0.1.0"),
        ("0.1.0a1", 'minor', False, "0.1.0"),
        ("0.1.0", 'minor', True, "0.2.0a1"),
        ("0.1.0a1", 'minor', True, "0.1.0a2"),
        ("0.1.1a1", 'minor', True, "0.2.0a1"),
    ]
)
def test_increment_version(source, inc_type, with_beta, result):
    version = VersionLine("", source)
    version.increment(inc_type, with_beta)
    incremented = str(version)
    assert incremented == result

