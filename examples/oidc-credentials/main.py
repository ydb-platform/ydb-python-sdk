import argparse

import ydb
import ydb.oidc


def parse_args():
    parser = argparse.ArgumentParser(description="OIDC and OAuth 2.0 credentials example")
    parser.add_argument("--endpoint", required=True, help="YDB endpoint")
    parser.add_argument("--database", required=True, help="YDB database")
    parser.add_argument("--mode", required=True, choices=("token", "client", "device"))
    parser.add_argument("--access-token", help="Existing OAuth 2.0 access token")
    parser.add_argument("--issuer", help="OIDC issuer URL")
    parser.add_argument("--client-id", help="OAuth 2.0 client ID")
    parser.add_argument("--client-secret", help="OAuth 2.0 client secret")
    parser.add_argument("--scope", action="append", help="OAuth 2.0 scope; may be repeated")
    parser.add_argument("--audience", help="OAuth 2.0 token audience")
    parser.add_argument("--ca-file", help="CA certificate for the identity provider")
    args = parser.parse_args()

    if args.mode == "token" and not args.access_token:
        parser.error("--access-token is required in token mode")
    if args.mode in ("client", "device") and (not args.issuer or not args.client_id):
        parser.error("--issuer and --client-id are required in client and device modes")
    if args.mode == "client" and not args.client_secret:
        parser.error("--client-secret is required in client mode")

    return args


def device_authorization_callback(info):
    print("Open {}".format(info.verification_uri_complete or info.verification_uri))
    print("Enter code {}".format(info.user_code))


def create_credentials(args):
    if args.mode == "token":
        return ydb.oidc.OAuth2TokenCredentials(args.access_token)

    common = {
        "issuer": args.issuer,
        "client_id": args.client_id,
        "audience": args.audience,
        "ca_file": args.ca_file,
    }
    if args.scope is not None:
        common["scope"] = args.scope
    if args.mode == "client":
        return ydb.oidc.OAuth2ClientCredentials(client_secret=args.client_secret, **common)
    return ydb.oidc.OAuth2DeviceCredentials(
        device_authorization_callback=device_authorization_callback,
        **common,
    )


def main():
    args = parse_args()
    with ydb.Driver(
        endpoint=args.endpoint,
        database=args.database,
        credentials=create_credentials(args),
    ) as driver:
        driver.wait(timeout=10, fail_fast=True)
        with ydb.QuerySessionPool(driver) as pool:
            result_sets = pool.execute_with_retries("SELECT 42 AS answer")
    print(result_sets[0].rows[0].answer)


if __name__ == "__main__":
    main()
