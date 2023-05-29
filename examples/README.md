# YDB Python SDK Examples

This directory contains the example code for [YDB](https://ydb.tech) Python SDK.

In order to develop and run this examples the following Python dependencies are required:

```bash
# Date and time formatting functions used in some examples
python3 -m pip install iso8601
# YDB Python SDK
python3 -m pip install ydb
# Yandex Cloud Python SDK (for running the examples on YDB Managed Services)
python3 -m pip install yandexcloud
```

## Running the examples on local single node YDB instance

(1) Configure and run the local YDB cluster

Follow the quickstart instructions in the [documentation](https://ydb.tech/en/docs/administration/quickstart).

(2) Run the example

```bash
# Change the directory for the particular example, e.g. basic_example_v1
EXAMPLE=basic_example_v1
cd $EXAMPLE
# Enable the anonymous authentication mode
export YDB_ANONYMOUS_CREDENTIALS=1
# Set the database path and its endpoint
export YDB_ENDPOINT=grpc://localhost:2136
export YDB_DATABASE=/local
# Run the script
python3 __main__.py -e $YDB_ENDPOINT -d $YDB_DATABASE -p python-examples/$EXAMPLE
```

## Running the examples on the self-hosted YDB cluster

(1) Obtain the credentials for the self-hosted YDB cluster

Typical parameters for the clusters deployed according to the [documentation](https://ydb.tech/en/docs/deploy/manual/deploy-ydb-on-premises):
* endpoint: `grpcs://cluster-endpoint.domain.com:2136`, where the node name should match the balancer name or the address of one of the cluster nodes;
* database: `/Root/testdb`, or another database name as configured;
* username, password: the credentials of the user with [read-write privileges](https://ydb.tech/en/docs/cluster/access), created according to the [documentation](https://ydb.tech/en/docs/yql/reference/syntax/create-user).

(2) Run the example

```bash
# Change the directory for the particular example, e.g. basic_example_v1
EXAMPLE=basic_example_v1
cd $EXAMPLE
# Obtain the YDB authentication token
export YDB_ACCESS_TOKEN_CREDENTIALS=`ydb -p ydb1 auth get-token -f`
# Set the database path and its endpoint
export YDB_ENDPOINT=grpcs://cluster-endpoint.domain.com:2136
export YDB_DATABASE=/Root/testdb
# Run the script
python3 __main__.py -e $YDB_ENDPOINT -d $YDB_DATABASE -p python-examples/$EXAMPLE
```


## Running the examples with the managed YDB instance in Yandex Cloud

(1) Install the yc command line tool

https://cloud.yandex.ru/docs/cli/operations/install-cli

(2) Create the service account using the YC Web Console, and assign it the ydb.editor role.

Alternatively use the following shell snippet:

```bash
# Specify the Yandex Cloud folder and service account name
export YC_FOLDER=mzinal
export SA_NAME=ydb-sa-0
# Create the service account
yc iam service-account create $SA_NAME
# Obtain the service account id
export SA_ID=`yc iam service-account get --name $SA_NAME | sed -n 's/^id: \(.*\)$/\1/p'`
# Assign the ydb.editor role for the specified YC folder to the service account just created
yc resource-manager folder add-access-binding $YC_FOLDER --role ydb.editor --subject serviceAccount:$SA_ID 
```

(3) Generate the service account key to be used for authentication.

Note: unfortunately, right now YC Web Console does not offer a way to generate the SA key
with its Web interface.

```bash
yc iam key create --service-account-name $SA_NAME --output $HOME/key-ydb-sa-0.json
```

(4) Obtain the endpoint and database path from the Web Console.

Alternatively, use the following command to grab the required data in the shell:

```bash
yc ydb db get --name ydb1
```

`ydb1` value in the command above is the logical name of the YDB managed database.

(5) Run the example:

```bash
# Change the directory for the particular example, e.g. basic_example_v1
EXAMPLE=basic_example_v1
cd $EXAMPLE
# Set the path to the service account key file
export YDB_SERVICE_ACCOUNT_KEY_FILE_CREDENTIALS=$HOME/key-ydb-sa-0.json
# Set the database path and its endpoint
export YDB_ENDPOINT=grpcs://ydb.serverless.yandexcloud.net:2135
export YDB_DATABASE=/ru-central1/b1gfvslmokutuvt2g019/etnvbffeqegu1ub2rg2o
# Run the script
python3 __main__.py -e $YDB_ENDPOINT -d $YDB_DATABASE -p python-examples/$EXAMPLE
```
