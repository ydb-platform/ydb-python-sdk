# YDB Python SDK Example: jsondemo

This example shows how to run the queries which read and write JSON data.

## Running the example

Obtain the YDB authentication token:

```bash
export YDB_ACCESS_TOKEN_CREDENTIALS=`ydb -p ydb1 auth get-token -f`
```

In the command above `ydb1` is the name of the configuration profile configured for the YDB database.

Run the example using the following command:

```bash
python3 __main__.py -e ENDPOINT -d DATABASE -p DIRNAME
```

In the command above the following values must be substituted with their actual values:
* `ENDPOINT` - connection endpoint, `grpcs://ydb.serverless.yandexcloud.net:2135` for the YDB serverless service in Yandex Cloud;
* `DATABASE` - database path, like `/ru-central1/b1gfvslmokutuvt2g019/etnuogblap3e7dok6tf5`;
* `DIRNAME` - directory name to store the sample table, for example, `python-examples/jsondemo`

