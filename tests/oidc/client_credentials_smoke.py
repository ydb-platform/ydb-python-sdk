import asyncio

import ydb.aio.oidc

from _smoke_common import client_credentials, execute_async, execute_sync, oidc_settings, required_env


async def run_async() -> None:
    credentials = ydb.aio.oidc.OAuth2ClientCredentials(
        client_id=required_env("YDB_OIDC_CLIENT_ID"),
        client_secret=required_env("YDB_OIDC_CLIENT_SECRET"),
        **oidc_settings(),
    )
    await execute_async(credentials, "Client Credentials")
    credentials._expires_in = 0
    await execute_async(credentials, "Client Credentials refresh")


def main() -> None:
    credentials = client_credentials()
    execute_sync(credentials, "Client Credentials")
    credentials._expires_in = 0
    execute_sync(credentials, "Client Credentials refresh")

    asyncio.run(run_async())


if __name__ == "__main__":
    main()
