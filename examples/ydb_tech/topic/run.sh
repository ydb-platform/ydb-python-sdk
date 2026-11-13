#!/usr/bin/env bash
set -euo pipefail
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
python examples/ydb_tech/topic/sync_example.py
python examples/ydb_tech/topic/async_example.py
