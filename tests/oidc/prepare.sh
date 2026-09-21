#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
state_dir="${script_dir}/.state"
env_file="${state_dir}/oidc.env"
realm_file="${state_dir}/keycloak/ydb-realm.json"
force=false

if [[ "${1:-}" == "--force" ]]; then
  force=true
elif [[ $# -ne 0 ]]; then
  echo "Usage: $0 [--force]" >&2
  exit 2
fi

if [[ -f "${env_file}" && -f "${realm_file}" && "${force}" == false ]]; then
  echo "OIDC test configuration already exists: ${env_file}"
  exit 0
fi

if [[ "${force}" == false && ( -e "${env_file}" || -e "${realm_file}" ) ]]; then
  echo "OIDC test state is incomplete; rerun with --force to replace it" >&2
  exit 1
fi

if ! command -v openssl >/dev/null 2>&1; then
  echo "openssl is required to generate local test credentials" >&2
  exit 1
fi

umask 077
mkdir -p "${state_dir}/certs" "${state_dir}/keycloak"
rm -f "${state_dir}/certs/keycloak.p12" "${state_dir}/certs/keycloak-ca.pem"

keycloak_admin_password="$(openssl rand -hex 24)"
keycloak_keystore_password="$(openssl rand -hex 24)"
client_secret="$(openssl rand -hex 32)"
device_user_password="$(openssl rand -hex 24)"

{
  printf '%s\n' \
    "KEYCLOAK_ADMIN_USERNAME=admin" \
    "KEYCLOAK_ADMIN_PASSWORD=${keycloak_admin_password}" \
    "KEYCLOAK_KEYSTORE_PASSWORD=${keycloak_keystore_password}" \
    "YDB_ENDPOINT=grpc://localhost:22136" \
    "YDB_DATABASE=/local" \
    "YDB_OIDC_ISSUER=https://localhost:28443/realms/ydb" \
    "YDB_OIDC_AUDIENCE=ydb" \
    "YDB_OIDC_CA_FILE=${state_dir}/certs/keycloak-ca.pem" \
    "YDB_OIDC_CLIENT_ID=ydb-client-credentials" \
    "YDB_OIDC_CLIENT_SECRET=${client_secret}" \
    "YDB_OIDC_DEVICE_CLIENT_ID=ydb-device" \
    "YDB_OIDC_DEVICE_USERNAME=developer" \
    "YDB_OIDC_DEVICE_PASSWORD=${device_user_password}"
} >"${env_file}"

{
  printf '%s\n' \
    '{' \
    '  "realm": "ydb",' \
    '  "enabled": true,' \
    '  "displayName": "YDB local OIDC",' \
    '  "accessTokenLifespan": 300,' \
    '  "oauth2DeviceCodeLifespan": 600,' \
    '  "oauth2DevicePollingInterval": 5,' \
    '  "groups": [{"name": "developers"}],' \
    '  "users": [' \
    '    {' \
    '      "username": "developer",' \
    '      "enabled": true,' \
    '      "email": "developer@example.test",' \
    '      "emailVerified": true,' \
    '      "firstName": "YDB",' \
    '      "lastName": "Developer",' \
    "      \"credentials\": [{\"type\": \"password\", \"value\": \"${device_user_password}\", \"temporary\": false}]," \
    '      "groups": ["/developers"]' \
    '    }' \
    '  ],' \
    '  "clients": [' \
    '    {' \
    '      "clientId": "ydb-client-credentials",' \
    '      "name": "YDB client credentials",' \
    '      "enabled": true,' \
    '      "protocol": "openid-connect",' \
    '      "publicClient": false,' \
    "      \"secret\": \"${client_secret}\"," \
    '      "serviceAccountsEnabled": true,' \
    '      "standardFlowEnabled": false,' \
    '      "directAccessGrantsEnabled": false,' \
    '      "protocolMappers": [' \
    '        {' \
    '          "name": "ydb-audience",' \
    '          "protocol": "openid-connect",' \
    '          "protocolMapper": "oidc-audience-mapper",' \
    '          "config": {' \
    '            "included.custom.audience": "ydb",' \
    '            "id.token.claim": "false",' \
    '            "access.token.claim": "true"' \
    '          }' \
    '        }' \
    '      ]' \
    '    },' \
    '    {' \
    '      "clientId": "ydb-device",' \
    '      "name": "YDB device authorization",' \
    '      "enabled": true,' \
    '      "protocol": "openid-connect",' \
    '      "publicClient": true,' \
    '      "standardFlowEnabled": false,' \
    '      "directAccessGrantsEnabled": false,' \
    '      "attributes": {' \
    '        "oauth2.device.authorization.grant.enabled": "true"' \
    '      },' \
    '      "protocolMappers": [' \
    '        {' \
    '          "name": "ydb-audience",' \
    '          "protocol": "openid-connect",' \
    '          "protocolMapper": "oidc-audience-mapper",' \
    '          "config": {' \
    '            "included.custom.audience": "ydb",' \
    '            "id.token.claim": "false",' \
    '            "access.token.claim": "true"' \
    '          }' \
    '        },' \
    '        {' \
    '          "name": "groups",' \
    '          "protocol": "openid-connect",' \
    '          "protocolMapper": "oidc-group-membership-mapper",' \
    '          "config": {' \
    '            "claim.name": "groups",' \
    '            "full.path": "false",' \
    '            "id.token.claim": "false",' \
    '            "access.token.claim": "true"' \
    '          }' \
    '        }' \
    '      ]' \
    '    }' \
    '  ]' \
    '}'
} >"${realm_file}"

chmod 0600 "${env_file}" "${realm_file}"
echo "Generated OIDC test configuration: ${env_file}"
echo "Load it with: set -a; source '${env_file}'; set +a"
