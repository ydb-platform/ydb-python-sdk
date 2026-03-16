import argparse

import ydb
import ydb.oauth2_token_exchange


def parse_args():
    parser = argparse.ArgumentParser(
        usage="%(prog)s options", description="Oauth 2.0 token exchange credentials example"
    )
    parser.add_argument("-d", "--database", required=True, help="Name of the database to use")
    parser.add_argument("-e", "--endpoint", required=True, help="Endpoint url to use")
    parser.add_argument("--token-endpoint", required=True, help="Token endpoint url to use")
    parser.add_argument("--private-key-file", required=True, help="Private key file path in pem format")
    parser.add_argument("--key-id", help="Key id")
    parser.add_argument("--audience", help="Audience")
    parser.add_argument("--issuer", help="Jwt token issuer")
    parser.add_argument("--subject", help="Jwt token subject")

    return parser.parse_args()


def execute_query(session):
    # Create the transaction and execute the `select 1` query.
    # All transactions must be committed using the `commit_tx` flag in the last
    # statement. The either way to commit transaction is using `commit` method of `TxContext` object, which is
    # not recommended.
    return session.transaction().execute(
        "select 1 as cnt;",
        commit_tx=True,
        settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2),
    )


def main():
    args = parse_args()

    # Example demonstrates how to initializate driver instance
    # using the oauth 2.0 token exchange credentials provider.
    driver = ydb.Driver(
        endpoint=args.endpoint,
        database=args.database,
        root_certificates=ydb.load_ydb_root_certificate(),
        credentials=ydb.oauth2_token_exchange.Oauth2TokenExchangeCredentials(
            token_endpoint=args.token_endpoint,
            audience=args.audience,
            subject_token_source=ydb.oauth2_token_exchange.JwtTokenSource(
                signing_method="RS256",
                private_key_file=args.private_key_file,
                key_id=args.key_id,
                issuer=args.issuer,
                subject=args.subject,
                audience=args.audience,
            ),
        ),
    )

    # Start driver context manager.
    # The recommended way of using Driver object is using `with`
    # clause, because the context manager automatically stops the driver.
    with driver:
        # wait until driver become initialized
        driver.wait(fail_fast=True, timeout=5)

        # Initialize the session pool instance and enter the context manager.
        # The context manager automatically stops the session pool.
        # On the session pool termination all YDB sessions are closed.
        with ydb.SessionPool(driver) as pool:
            # Execute the query with the `retry_operation_helper` the.
            # The `retry_operation_sync` helper used to help developers
            # to retry YDB specific errors like locks invalidation.
            # The first argument of the `retry_operation_sync` is a function to retry.
            # This function must have session as the first argument.
            result = pool.retry_operation_sync(execute_query)
            assert result[0].rows[0].cnt == 1


main()
