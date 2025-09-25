docker compose -f playground/configs/compose.yaml down -v
docker compose -f playground/configs/compose.yaml up -d --wait

EXECUTOR="../../.venv/bin/python ./src"


# $EXECUTOR topic-create grpc://localhost:2135 /Root/testdb --path /Root/testdb/slo_topic
# $EXECUTOR topic-run grpc://localhost:2135 /Root/testdb --path /Root/testdb/slo_topic --prom-pgw "" --read-threads 0 --write-rps 1 --time 120

$EXECUTOR topic-create grpc://localhost:2135 /Root/testdb --path /Root/testdb/slo_topic
$EXECUTOR topic-run grpc://localhost:2135 /Root/testdb --path /Root/testdb/slo_topic --prom-pgw "" --read-threads 0 --write-rps 5 --time 60
$EXECUTOR topic-run grpc://localhost:2135 /Root/testdb --path /Root/testdb/slo_topic --prom-pgw "" --write-threads 0 --read-rps 1 --time 60

# $EXECUTOR table-create grpc://localhost:2135 /Root/testdb
# $EXECUTOR table-run grpc://localhost:2135 /Root/testdb --prom-pgw "" --read-rps 10 --write-threads 0 --read-threads 5 --time 600 --session-pool-size 1
# $EXECUTOR table-cleanup grpc://localhost:2135 /Root/testdb