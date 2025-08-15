#!/bin/bash
set -e


# Install dependencies
pip install -r requirements.txt
# Install ydb package
pip install -e .
# Install tox for CI
pip install tox

