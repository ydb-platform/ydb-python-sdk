# Local YDB and Keycloak OIDC environment

This directory provides a self-contained development environment for the OIDC authentication contract shared by YDB SDKs. It runs Keycloak and a trunk build of local YDB in one Compose project.

The generated credentials and self-signed certificate are for local development only.

## Generate local configuration

Run the preparation step once:

```shell
tests/oidc/prepare.sh
```

It generates two ignored files:

- `.state/oidc.env` is the source of truth for container and SDK settings;
- `.state/keycloak/ydb-realm.json` is the Keycloak realm import assembled from the same generated credentials.

No client secret or test-user password is stored in the repository. Load the generated variables before running a host-side test:

```shell
set -a
source tests/oidc/.state/oidc.env
set +a
```

The relevant flow variables are:

| Flow | Variables |
| --- | --- |
| Static token | `YDB_ENDPOINT`, `YDB_DATABASE`; set the access token returned by either flow in the SDK's static-token input |
| Client Credentials | `YDB_OIDC_ISSUER`, `YDB_OIDC_AUDIENCE`, `YDB_OIDC_CLIENT_ID`, `YDB_OIDC_CLIENT_SECRET`, `YDB_OIDC_CA_FILE` |
| Device Authorization | `YDB_OIDC_ISSUER`, `YDB_OIDC_AUDIENCE`, `YDB_OIDC_DEVICE_CLIENT_ID`, `YDB_OIDC_DEVICE_USERNAME`, `YDB_OIDC_DEVICE_PASSWORD`, `YDB_OIDC_CA_FILE` |

The public device client intentionally has no client secret.

## Start and verify

From the repository root:

```shell
docker compose \
  --env-file tests/oidc/.state/oidc.env \
  -f tests/oidc/compose.yaml \
  up -d --wait
```

With the project virtual environment activated and the generated variables loaded, run the three smoke tests:

```shell
PYTHONPATH=. python tests/oidc/static_token_smoke.py
PYTHONPATH=. python tests/oidc/client_credentials_smoke.py
PYTHONPATH=. python tests/oidc/device_authorization_smoke.py
```

Every script exercises both the synchronous and asynchronous drivers. The Client Credentials and Device Authorization scripts also force token expiry and verify refresh. The static-token script verifies that YDB rejects an invalid bearer token.

The Device Authorization smoke test automatically completes Keycloak login and consent using the generated local test user. This automation belongs only to the test; production applications receive the verification URI and user code through `device_authorization_callback` and leave authentication to the user.

The public API exercised by the scripts is:

```python
import ydb.oidc

ydb.oidc.OAuth2TokenCredentials(access_token)
ydb.oidc.OAuth2ClientCredentials(
    issuer=issuer,
    client_id=client_id,
    client_secret=client_secret,
    audience="ydb",
    ca_file=ca_file,
)
ydb.oidc.OAuth2DeviceCredentials(
    issuer=issuer,
    client_id=device_client_id,
    device_authorization_callback=show_verification_url_and_code,
    audience="ydb",
    ca_file=ca_file,
)
```

The non-blocking equivalents use the same names under `ydb.aio.oidc`.

The stack uses non-default host ports:

- YDB gRPC: `grpc://localhost:22136`
- YDB monitoring: <http://localhost:28765>
- Keycloak: <https://localhost:28443>

## Device Authorization

Request a device code with the generated public client ID:

```shell
curl --cacert "$YDB_OIDC_CA_FILE" \
  --request POST \
  --data "client_id=$YDB_OIDC_DEVICE_CLIENT_ID" \
  "$YDB_OIDC_ISSUER/protocol/openid-connect/auth/device"
```

Open the returned `verification_uri_complete` and sign in with `YDB_OIDC_DEVICE_USERNAME` and `YDB_OIDC_DEVICE_PASSWORD`. Poll the token endpoint using the returned `device_code` and grant type `urn:ietf:params:oauth:grant-type:device_code`.

## Stop and reset

Stop the stack while preserving the imported Keycloak realm:

```shell
docker compose \
  --env-file tests/oidc/.state/oidc.env \
  -f tests/oidc/compose.yaml \
  down
```

To rotate all local credentials, remove the Keycloak volume and regenerate the state:

```shell
docker compose \
  --env-file tests/oidc/.state/oidc.env \
  -f tests/oidc/compose.yaml \
  down --volumes
tests/oidc/prepare.sh --force
```

YDB uses in-memory pdisks and intentionally has no data volume. Keycloak keeps its imported realm in a named volume, so `down --volumes` is required before importing newly generated credentials.

## Configuration notes

YDB currently requires an HTTPS issuer for external IdP discovery. Compose creates a self-signed Keycloak certificate on first start, and `.state/oidc.env` points clients to its CA file.

YDB and Keycloak share a network namespace so both YDB inside Docker and an SDK on the host see the exact issuer `https://localhost:28443/realms/ydb`. OIDC issuer matching includes the scheme, hostname, port, and path.

`enforce_user_token_check_requirement` is enabled in `ydb.yaml`, so a supplied invalid token is rejected instead of falling back to anonymous access. Anonymous requests remain available for local YDB initialization and health checks.
