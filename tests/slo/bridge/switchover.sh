#!/bin/sh
set -e
. /opt/ydb.tech/scripts/chaos/libchaos.sh

recovery_timeout="${BRIDGE_RECOVERY_TIMEOUT:-180}"
original_primary=$(get_bridge_pile_by_state PRIMARY)
new_primary=$(get_bridge_pile_by_state SYNCHRONIZED)
compute=$(get_bridge_pile_nodes "$original_primary" database)
fault_active=false

cleanup() {
    set +e
    docker start "$compute" >/dev/null
    restore_bridge_primary "$original_primary" "$recovery_timeout"
    if [ "$fault_active" = true ]; then
        chaos_recover "bridge-switchover" "$new_primary" "Original PRIMARY restored"
    fi
}

[ -n "$original_primary" ] && [ -n "$new_primary" ] && [ -n "$compute" ]
BRIDGE_CLI_PILE="$original_primary"
install_bridge_cleanup_traps

deadline=$(($(date +%s) + 120))
until docker exec ydb-bridge-probe test -f /tmp/bridge-probe-ready; do
    [ "$(date +%s)" -lt "$deadline" ] || exit 1
    sleep 2
done

log "PRIMARY_FALLBACK_BEGIN $original_primary"
docker stop -t 0 "$compute"
sleep 45
log "PRIMARY_FALLBACK_END $original_primary"
docker start "$compute" >/dev/null
wait_container_healthy "$compute" "$recovery_timeout"

log "PRIMARY_WINDOW_BEGIN initial $original_primary"
sleep 160
log "PRIMARY_WINDOW_END initial $original_primary"

chaos_inject "bridge-switchover" "$new_primary"
fault_active=true
bridge_cli switchover --new-primary "$new_primary"
wait_bridge_pile_state "$new_primary" PRIMARY "$recovery_timeout"
BRIDGE_CLI_PILE="$new_primary"
log "PRIMARY_WINDOW_BEGIN switched $new_primary"
sleep 160
log "PRIMARY_WINDOW_END switched $new_primary"

restore_bridge_primary "$original_primary" "$recovery_timeout"
BRIDGE_CLI_PILE="$original_primary"
wait_bridge_pile_state "$new_primary" SYNCHRONIZED "$recovery_timeout"
log "PRIMARY_WINDOW_BEGIN restored $original_primary"
sleep 160
log "PRIMARY_WINDOW_END restored $original_primary"
chaos_recover "bridge-switchover" "$new_primary" "Original PRIMARY restored"
fault_active=false
clear_bridge_cleanup_traps
