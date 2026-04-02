import argparse
import os


def parse_options():
    """
    Parse CLI arguments (passed via Docker CMD section).
    Connection, duration, and workload identity are configured via environment variables:
      YDB_ENDPOINT          — YDB endpoint (e.g. grpc://ydb:2136)
      YDB_DATABASE          — YDB database path (e.g. /Root/testdb)
      WORKLOAD_DURATION     — total run duration in seconds (default: 600)
    """
    parser = argparse.ArgumentParser(
        description="YDB Python SLO workload",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    # Table params
    parser.add_argument("--table-name", default="key_value", help="Table name")
    parser.add_argument("--min-partitions-count", default=6, type=int)
    parser.add_argument("--max-partitions-count", default=1000, type=int)
    parser.add_argument(
        "--partition-size", default=100, type=int, help="Partition size [mb]"
    )
    parser.add_argument(
        "--initial-data-count",
        default=1000,
        type=int,
        help="Number of rows to pre-fill",
    )
    parser.add_argument(
        "--batch-size", default=100, type=int, help="Rows per insert batch"
    )
    parser.add_argument(
        "--threads", default=10, type=int, help="Threads for initial data fill"
    )

    # Run params
    parser.add_argument("--read-rps", default=100, type=int, help="Read RPS limit")
    parser.add_argument(
        "--read-timeout", default=10000, type=int, help="Read timeout [ms]"
    )
    parser.add_argument("--write-rps", default=10, type=int, help="Write RPS limit")
    parser.add_argument(
        "--write-timeout", default=20000, type=int, help="Write timeout [ms]"
    )
    parser.add_argument(
        "--read-threads", default=8, type=int, help="Read worker threads"
    )
    parser.add_argument(
        "--write-threads", default=4, type=int, help="Write worker threads"
    )
    parser.add_argument(
        "--shutdown-time", default=10, type=int, help="Graceful shutdown time [s]"
    )
    parser.add_argument(
        "--report-period", default=1000, type=int, help="Metrics push period [ms]"
    )

    # Topic params (used when WORKLOAD_NAME contains 'topic')
    parser.add_argument("--topic-path", default="/local/slo_topic", help="Topic path")
    parser.add_argument(
        "--topic-consumer", default="slo_consumer", help="Topic consumer name"
    )
    parser.add_argument(
        "--topic-partitions", default=1, type=int, help="Topic partition count"
    )
    parser.add_argument(
        "--message-size", default=100, type=int, help="Topic message size [bytes]"
    )

    args = parser.parse_args()

    # Inject env-var-driven config as attributes so the rest of the code can use args.* uniformly
    args.endpoint = os.environ.get("YDB_ENDPOINT", "grpc://localhost:2136")
    args.db = os.environ.get("YDB_DATABASE", "/local")
    args.time = int(os.environ.get("WORKLOAD_DURATION", "600"))

    # Aliases used by topic runner
    args.path = args.topic_path
    args.consumer = args.topic_consumer
    args.partitions_count = args.topic_partitions

    return args
