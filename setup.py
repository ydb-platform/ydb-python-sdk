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
    version="2.13.5",  # AUTOVERSION
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
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
    ],
    install_requires=requirements,  # requirements.txt
    options={"bdist_wheel": {"universal": True}},
    extras_require={
        "yc": ["yandexcloud", ],
    }
)
