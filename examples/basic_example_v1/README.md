Running this sample with the managed YDB instance in Yandex Cloud
---

(0) Install the yc command line tool

https://cloud.yandex.ru/docs/cli/operations/install-cli

(1) Create the service account using the YC Web Console, and assign it the ydb.editor role.

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

(2) Generate the service account key to be used for authentication.

Note: unfortunately, right now YC Web Console does not offer a way to generate the SA key
with its Web interface.

```bash
yc iam key create --service-account-name $SA_NAME --output $HOME/key-ydb-sa-0.json
```

(3) Obtain the endpoint and database path from the Web Console.

Alternatively, use the following command to grab the required data in the shell:

```bash
yc ydb db get --name ydb1
```

`ydb1` value in the command above is the logical name of the YDB managed database.

(4) Run the sample:

```bash
# Set the path to the service account key file
export YDB_SERVICE_ACCOUNT_KEY_FILE_CREDENTIALS=$HOME/key-ydb-sa-0.json
# Set the database path and its endpoint
export YDB_ENDPOINT=grpcs://ydb.serverless.yandexcloud.net:2135
export YDB_DATABASE=/ru-central1/b1gfvslmokutuvt2g019/etnvbffeqegu1ub2rg2o
# Run the script
python3 __main__.py -e $YDB_ENDPOINT -d $YDB_DATABASE
```
