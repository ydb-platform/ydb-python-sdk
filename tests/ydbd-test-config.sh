#!/usr/bin/env bash
set -euo pipefail

# local-ydb generates the cluster config before launching the server.
if [[ "${1:-}" == server ]]; then
    for arg in "$@"; do
        if [[ "$arg" == --yaml-config=* ]]; then
            config=${arg#*=}
            sed -i -e '/^  enable_strict_serializable_isolation:/d' \
                -e '/^table_service_config:$/a\  enable_strict_serializable_isolation: true' "$config"
            grep -qx '  enable_strict_serializable_isolation: true' "$config"
            break
        fi
    done
fi

exec /ydbd "$@"
