import argparse
import os
import sys

_WORKLOADS = {"sync-table", "sync-query", "topic"}

_TABLE_OPTIONS = {
    "--table-name",
    "--min-partitions-count",
    "--max-partitions-count",
    "--partition-size",
    "--initial-data-count",
    "--batch-size",
    "--threads",
}

_TOPIC_OPTIONS = {
    "--topic-path",
    "--topic-consumer",
    "--topic-partitions",
    "--message-size",
}


def _provided_options(argv):
    options = set()
    for arg in argv:
        option = arg.split("=", 1)[0]
        if option.startswith("--"):
            options.add(option)
    return options


def _validate_options(parser, args, provided_options):
    if args.workload_name not in _WORKLOADS:
        parser.error(f"Unknown workload-name: {args.workload_name}. Expected one of: {', '.join(sorted(_WORKLOADS))}")

    if args.workload_name == "topic":
        invalid_options = sorted(provided_options & _TABLE_OPTIONS)
    else:
        invalid_options = sorted(provided_options & _TOPIC_OPTIONS)

    if invalid_options:
        parser.error(f"{args.workload_name} workload does not accept options: {', '.join(invalid_options)}")

    if args.async_mode and args.workload_name != "topic":
        parser.error("--async is supported only for topic workload")


def parse_options():
    """
    Parse CLI arguments.

    Every flag supports a fallback chain: CLI arg > environment variable > hardcoded default.
    """
    parser = argparse.ArgumentParser(
        description="YDB Python SLO workload",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "endpoint",
        nargs="?",
        default=os.environ.get("YDB_ENDPOINT", "grpc://localhost:2136"),
        help="YDB endpoint (default: $YDB_ENDPOINT)",
    )
    parser.add_argument(
        "db",
        nargs="?",
        default=os.environ.get("YDB_DATABASE", "/local"),
        help="YDB database (default: $YDB_DATABASE)",
    )
    parser.add_argument(
        "--time",
        default=int(os.environ.get("WORKLOAD_DURATION", "600")),
        type=int,
        help="Workload duration in seconds (default: $WORKLOAD_DURATION or 600)",
    )
    parser.add_argument(
        "--workload-name",
        default=os.environ.get("WORKLOAD_NAME", os.environ.get("WORKLOAD", "sync-query")),
        help="Workload type: sync-table, sync-query, topic (default: $WORKLOAD_NAME or sync-query)",
    )
    parser.add_argument(
        "--workload-ref",
        default=os.environ.get("WORKLOAD_REF", os.environ.get("REF", "main")),
        help="Reference label for metrics (default: $WORKLOAD_REF or main)",
    )
    parser.add_argument(
        "--otlp-endpoint",
        default=os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:9090/api/v1/otlp"),
        help="OTLP endpoint (default: $OTEL_EXPORTER_OTLP_ENDPOINT or http://localhost:9090/api/v1/otlp)",
    )

    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--async",
        dest="async_mode",
        action="store_true",
        help="Run workload in async mode",
    )

    # Table params
    parser.add_argument("--table-name", default="key_value", help="Table name")
    parser.add_argument("--min-partitions-count", default=6, type=int)
    parser.add_argument("--max-partitions-count", default=1000, type=int)
    parser.add_argument("--partition-size", default=100, type=int, help="Partition size [mb]")
    parser.add_argument(
        "--initial-data-count",
        default=1000,
        type=int,
        help="Number of rows to pre-fill",
    )
    parser.add_argument("--batch-size", default=100, type=int, help="Rows per insert batch")
    parser.add_argument("--threads", default=10, type=int, help="Threads for initial data fill")

    # Run params
    parser.add_argument("--read-rps", default=100, type=int, help="Read RPS limit")
    parser.add_argument("--read-timeout", default=10000, type=int, help="Read timeout [ms]")
    parser.add_argument("--write-rps", default=10, type=int, help="Write RPS limit")
    parser.add_argument("--write-timeout", default=20000, type=int, help="Write timeout [ms]")
    parser.add_argument("--read-threads", default=8, type=int, help="Read worker threads")
    parser.add_argument("--write-threads", default=4, type=int, help="Write worker threads")
    parser.add_argument("--shutdown-time", default=10, type=int, help="Graceful shutdown time [s]")
    parser.add_argument("--report-period", default=1000, type=int, help="Metrics push period [ms]")

    # Topic params (used when --workload-name is 'topic')
    parser.add_argument("--topic-path", default="/local/slo_topic", help="Topic path")
    parser.add_argument("--topic-consumer", default="slo_consumer", help="Topic consumer name")
    parser.add_argument("--topic-partitions", default=1, type=int, help="Topic partition count")
    parser.add_argument("--message-size", default=100, type=int, help="Topic message size [bytes]")

    args = parser.parse_args()
    provided_options = _provided_options(sys.argv[1:])
    _validate_options(parser, args, provided_options)

    return args
