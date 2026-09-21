import asyncio

import ydb
import ydb.aio.oidc

from _smoke_common import (
    approve_keycloak_device,
    approve_keycloak_device_async,
    execute_async,
    execute_sync,
    oidc_settings,
    required_env,
)


def sync_credentials():
    callbacks = []

    def callback(info):
        callbacks.append(info)
        print("Device verification URL: {}".format(info.verification_uri_complete or info.verification_uri))
        print("Device user code: {}".format(info.user_code))
        approve_keycloak_device(info)

    return (
        ydb.oidc.OAuth2DeviceCredentials(
            client_id=required_env("YDB_OIDC_DEVICE_CLIENT_ID"),
            device_authorization_callback=callback,
            **oidc_settings(),
        ),
        callbacks,
    )


def async_credentials():
    callbacks = []

    async def callback(info):
        callbacks.append(info)
        print("Async device verification URL: {}".format(info.verification_uri_complete or info.verification_uri))
        print("Async device user code: {}".format(info.user_code))
        await approve_keycloak_device_async(info)

    return (
        ydb.aio.oidc.OAuth2DeviceCredentials(
            client_id=required_env("YDB_OIDC_DEVICE_CLIENT_ID"),
            device_authorization_callback=callback,
            **oidc_settings(),
        ),
        callbacks,
    )


async def run_async() -> None:
    credentials, callbacks = async_credentials()
    await execute_async(credentials, "Device Authorization")
    credentials._expires_in = 0
    await execute_async(credentials, "Device Authorization refresh")
    if len(callbacks) != 1:
        raise RuntimeError("Device Authorization callback ran again instead of using refresh_token")


def main() -> None:
    credentials, callbacks = sync_credentials()
    execute_sync(credentials, "Device Authorization")
    credentials._expires_in = 0
    execute_sync(credentials, "Device Authorization refresh")
    if len(callbacks) != 1:
        raise RuntimeError("Device Authorization callback ran again instead of using refresh_token")

    asyncio.run(run_async())


if __name__ == "__main__":
    main()
