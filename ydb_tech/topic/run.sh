#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python ydb_tech/topic/sync_example.py
python ydb_tech/topic/async_example.py
