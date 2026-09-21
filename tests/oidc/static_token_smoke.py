import asyncio

import ydb
import ydb.aio.oidc

from _smoke_common import assert_token_claims, execute_async, execute_sync, raw_access_token


def main() -> None:
    access_token = raw_access_token()
    assert_token_claims(access_token)

    execute_sync(ydb.oidc.OAuth2TokenCredentials(access_token), "Static token")
    asyncio.run(execute_async(ydb.aio.oidc.OAuth2TokenCredentials(access_token), "Static token"))

    try:
        execute_sync(ydb.oidc.OAuth2TokenCredentials("this-is-not-a-jwt"), "Invalid static token")
    except ydb.ConnectionFailure:
        print("Invalid static token rejected by YDB")
    else:
        raise RuntimeError("YDB unexpectedly accepted an invalid static token")


if __name__ == "__main__":
    main()
