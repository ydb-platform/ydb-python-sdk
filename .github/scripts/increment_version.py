#!/bin/env python
import argparse
from dataclasses import dataclass

from packaging.version import Version

SETUP_PY_PATH = "setup.py"
DEFAULT_CHANGELOG_PATH = "CHANGELOG.md"
MARKER = "# AUTOVERSION"


@dataclass(init=False)
class VersionLine:
    old_line: str
    major: int
    minor: int
    patch: int
    pre: int

    def __init__(self, old_line: str, version_str: str):
        self.old_line = old_line

        version = Version(version_str)
        self.major = version.major
        self.minor = version.minor
        self.micro = version.micro

        if version.pre is None:
            self.pre = 0
        else:
            self.pre = version.pre[1]

    def increment(self, part_name: str, with_beta: bool):
        if part_name == 'minor':
            self.increment_minor(with_beta)
        elif part_name == 'patch' or part_name == 'micro':
            self.increment_micro(with_beta)
        else:
            raise Exception("unexpected increment type: '%s'" % part_name)

    def increment_minor(self, with_beta: bool):
        if with_beta:
            if self.pre == 0 or self.micro != 0:
                self.increment_minor(False)
            self.pre += 1
            return

        if self.micro == 0 and self.pre > 0:
            self.pre = 0
            return

        self.minor += 1
        self.micro = 0
        self.pre = 0

    def increment_micro(self, with_beta: bool):
        if with_beta:
            if self.pre == 0:
                self.increment_micro(False)
            self.pre += 1
            return

        if self.pre > 0:
            self.pre = 0
            return

        self.micro += 1

    def __str__(self):
        if self.pre > 0:
            pre = "b%s" % self.pre
        else:
            pre = ""

        return "%s.%s.%s%s" % (self.major, self.minor, self.micro, pre)

    def version_line_with_mark(self):
        return 'version="%s",  %s' % (str(self), MARKER)


def extract_version(setup_py_content: str):
    version_line = ""
    for line in setup_py_content.splitlines():
        if MARKER in line:
            version_line = line
            break

    if version_line == "":
        raise Exception("Not found version line")

    version_line = version_line.strip()

    parts = version_line.split('"')
    version_part = parts[1]

    return VersionLine(old_line=version_line, version_str=version_part)


def increment_version_at_setup_py(setup_py_path: str, inc_type: str, with_beta: bool) -> str:
    with open(setup_py_path, "rt") as f:
        setup_content = f.read()

    version = extract_version(setup_content)
    version.increment(inc_type, with_beta)
    setup_content = setup_content.replace(version.old_line, version.version_line_with_mark())

    with open(setup_py_path, "w") as f:
        f.write(setup_content)

    return str(version)


def add_changelog_version(changelog_path, version: str):
    with open(changelog_path, "rt") as f:
        content = f.read()
        content = content.strip()

    if content.startswith("##"):
        return

    content = """## %s ##
%s
""" % (version, content)
    with open(changelog_path, "w") as f:
        f.write(content)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inc-type",
        default="minor",
        help="increment version type: patch or minor",
        choices=["minor", "patch"],
    )
    parser.add_argument(
        "--beta",
        choices=["true", "false"],
        help="is beta version"
    )
    parser.add_argument("--changelog-path", default=DEFAULT_CHANGELOG_PATH, help="path to changelog", type=str)
    parser.add_argument("--setup-py-path", default=SETUP_PY_PATH)

    args = parser.parse_args()

    is_beta = args.beta == "true"

    new_version = increment_version_at_setup_py(args.setup_py_path, args.inc_type, is_beta)
    add_changelog_version(args.changelog_path, new_version)
    print(new_version)


if __name__ == '__main__':
    main()

