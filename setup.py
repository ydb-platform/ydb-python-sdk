# -*- coding: utf-8 -*-
import setuptools

with open("README.md", "r") as r:
    long_description = r.read()

with open("requirements.txt") as r:
    requirements = []
    for line in r.readlines():
        line = line.strip()
        if line != "":
            requirements.append(line)

setuptools.setup(
    name="ydb",
    version="3.26.5",  # AUTOVERSION
    description="YDB Python SDK",
    author="Yandex LLC",
    author_email="ydb@yandex-team.ru",
    url="http://github.com/ydb-platform/ydb-python-sdk",
    license="Apache 2.0",
    package_dir={"": "."},
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=setuptools.find_packages("."),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3 :: Only",
    ],
    install_requires=requirements,  # requirements.txt
    options={"bdist_wheel": {"universal": True}},
    extras_require={
        "yc": ["yandexcloud", ],
    }
)
