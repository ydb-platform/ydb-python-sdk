Authentication
==============

There are several ways to authenticate through YDB Python SDK.

Anonymous Credentials
---------------------

Full executable example `here <https://github.com/ydb-platform/ydb-python-sdk/tree/main/examples/anonymous-credentials>`_.

.. code-block:: python

    driver = ydb.Driver(
        endpoint=os.getenv("YDB_ENDPOINT"),
        database=os.getenv("YDB_DATABASE"),
        credentials=ydb.AnonymousCredentials(),
    )


Access Token Credentials
------------------------

Full executable example `here <https://github.com/ydb-platform/ydb-python-sdk/tree/main/examples/access-token-credentials>`_.

.. code-block:: python

    driver = ydb.Driver(
        endpoint=os.getenv("YDB_ENDPOINT"),
        database=os.getenv("YDB_DATABASE"),
        credentials=ydb.AccessTokenCredentials(os.getenv("YDB_ACCESS_TOKEN_CREDENTIALS")),
    )


Static Credentials (Legacy)
---------------------------
This method is legacy, use UserPasswordCredentials instead.

Full executable example `here <https://github.com/ydb-platform/ydb-python-sdk/tree/main/examples/static-credentials>`_.


.. code-block:: python

    driver_config = ydb.DriverConfig(
        endpoint=endpoint,
        database=database,
    )
    creds = ydb.StaticCredentials(
        driver_config=driver_config,
        user=user,
        password=password,
    )

    driver = ydb.Driver(
        driver_config=driver_config,
        credentials=creds,
    )


User Password Credentials
-------------------------

Full executable example `here <https://github.com/ydb-platform/ydb-python-sdk/tree/main/examples/static-credentials>`_.

.. code-block:: python

    driver_config = ydb.DriverConfig(
        endpoint=endpoint,
        database=database,
        credentials=ydb.UserPasswordCredentials(
            user=user,
            password=password,
            endpoint=endpoint,
            database=database,
        ),
    )

    driver = ydb.Driver(driver_config=driver_config)


Service Accaount Credentials
----------------------------

Full executable example `here <https://github.com/ydb-platform/ydb-python-sdk/tree/main/examples/service-account-credentials>`_.

.. code-block:: python

    driver = ydb.Driver(
        endpoint=os.getenv("YDB_ENDPOINT"),
        database=os.getenv("YDB_DATABASE"),
        credentials=ydb.iam.ServiceAccountCredentials.from_file(
            os.getenv("SA_KEY_FILE"),
        ),
    )


OAuth 2.0 Token Exchange Credentials
------------------------------------

Full executable example `here <https://github.com/ydb-platform/ydb-python-sdk/tree/main/examples/oauth2-token-exchange-credentials>`_.

.. code-block:: python

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


Metadata Credentials
--------------------

Full executable example `here <https://github.com/ydb-platform/ydb-python-sdk/tree/main/examples/metadata-credentials>`_.

.. code-block:: python

    driver = ydb.Driver(
        endpoint=os.getenv("YDB_ENDPOINT"),
        database=os.getenv("YDB_DATABASE"),
        credentials=ydb.iam.MetadataUrlCredentials(),
    )
