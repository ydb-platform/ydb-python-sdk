docker compose -f playground/configs/compose.yaml down -v
docker compose -f playground/configs/compose.yaml up -d --wait

../../.venv/bin/python ./src topic-create grpc://localhost:2135 /Root/testdb --path /Root/testdb/slo_topic

../../.venv/bin/python ./src topic-run grpc://localhost:2135 /Root/testdb --path /Root/testdb/slo_topic --prom-pgw "" --read-threads 0 --write-rps 1 --time 120

# ../../.venv/bin/python ./src topic-run grpc://localhost:2135 /Root/testdb --path /Root/testdb/slo_topic --prom-pgw "" --read-threads 0 --time 5
# ../../.venv/bin/python ./src topic-run grpc://localhost:2135 /Root/testdb --path /Root/testdb/slo_topic --prom-pgw "" --write-threads 0 --read-rps 1 --time 200