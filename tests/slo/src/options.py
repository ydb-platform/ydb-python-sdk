import argparse


def add_common_options(parser):
    parser.add_argument("endpoint", help="YDB endpoint")
    parser.add_argument("db", help="YDB database name")
    parser.add_argument("-t", "--table-name", default="key_value", help="Table name")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")


def make_table_create_parser(subparsers):
    table_create_parser = subparsers.add_parser("table-create", help="Create tables and fill with initial content")
    add_common_options(table_create_parser)

    table_create_parser.add_argument(
        "-p-min", "--min-partitions-count", default=6, type=int, help="Minimum amount of partitions in table"
    )
    table_create_parser.add_argument(
        "-p-max", "--max-partitions-count", default=1000, type=int, help="Maximum amount of partitions in table"
    )
    table_create_parser.add_argument("-p-size", "--partition-size", default=100, type=int, help="Partition size [mb]")
    table_create_parser.add_argument(
        "-c", "--initial-data-count", default=1000, type=int, help="Total number of records to generate"
    )

    table_create_parser.add_argument(
        "--write-timeout", default=20000, type=int, help="Write requests execution timeout [ms]"
    )

    table_create_parser.add_argument(
        "--batch-size", default=100, type=int, help="Number of new records in each create request"
    )
    table_create_parser.add_argument("--threads", default=10, type=int, help="Number of threads to use")


def make_table_run_parser(subparsers):
    table_run_parser = subparsers.add_parser("table-run", help="Run table SLO workload")
    add_common_options(table_run_parser)

    table_run_parser.add_argument("--read-rps", default=100, type=int, help="Read request rps")
    table_run_parser.add_argument(
        "--read-timeout", default=10000, type=int, help="Read requests execution timeout [ms]"
    )

    table_run_parser.add_argument("--write-rps", default=10, type=int, help="Write request rps")
    table_run_parser.add_argument(
        "--write-timeout", default=20000, type=int, help="Write requests execution timeout [ms]"
    )

    table_run_parser.add_argument("--time", default=10, type=int, help="Time to run in seconds")
    table_run_parser.add_argument("--shutdown-time", default=10, type=int, help="Graceful shutdown time in seconds")

    table_run_parser.add_argument("--prom-pgw", default="localhost:9091", type=str, help="Prometheus push gateway")
    table_run_parser.add_argument("--report-period", default=1000, type=int, help="Prometheus push period in [ms]")

    table_run_parser.add_argument("--read-threads", default=8, type=int, help="Number of threads to use for write")
    table_run_parser.add_argument("--write-threads", default=4, type=int, help="Number of threads to use for read")


def make_table_cleanup_parser(subparsers):
    table_cleanup_parser = subparsers.add_parser("table-cleanup", help="Drop tables")
    add_common_options(table_cleanup_parser)


def make_topic_create_parser(subparsers):
    topic_create_parser = subparsers.add_parser("topic-create", help="Create topic with consumer")
    add_common_options(topic_create_parser)

    topic_create_parser.add_argument("--path", default="/local/slo_topic", type=str, help="Topic path")
    topic_create_parser.add_argument("--consumer", default="slo_consumer", type=str, help="Topic consumer name")
    topic_create_parser.add_argument("--partitions-count", default=1, type=int, help="Partition count")


def make_topic_run_parser(subparsers):
    topic_parser = subparsers.add_parser("topic-run", help="Run topic SLO workload")
    add_common_options(topic_parser)

    topic_parser.add_argument("--path", default="/local/slo_topic", type=str, help="Topic path")
    topic_parser.add_argument("--consumer", default="slo_consumer", type=str, help="Topic consumer name")
    topic_parser.add_argument("--partitions-count", default=1, type=int, help="Partition count")
    topic_parser.add_argument("--read-rps", default=100, type=int, help="Topic read request rps")
    topic_parser.add_argument("--read-timeout", default=5000, type=int, help="Topic read timeout [ms]")
    topic_parser.add_argument("--write-rps", default=100, type=int, help="Topic write request rps")
    topic_parser.add_argument("--write-timeout", default=5000, type=int, help="Topic write timeout [ms]")
    topic_parser.add_argument("--read-threads", default=1, type=int, help="Number of threads for topic reading")
    topic_parser.add_argument("--write-threads", default=1, type=int, help="Number of threads for topic writing")
    topic_parser.add_argument("--message-size", default=100, type=int, help="Topic message size in bytes")

    topic_parser.add_argument("--time", default=10, type=int, help="Time to run in seconds")
    topic_parser.add_argument("--shutdown-time", default=10, type=int, help="Graceful shutdown time in seconds")
    topic_parser.add_argument(
        "--prom-pgw", default="localhost:9091", type=str, help="Prometheus push gateway (empty to disable)"
    )
    topic_parser.add_argument("--report-period", default=1000, type=int, help="Prometheus push period in [ms]")


def make_topic_cleanup_parser(subparsers):
    topic_cleanup_parser = subparsers.add_parser("topic-cleanup", help="Drop topic")
    add_common_options(topic_cleanup_parser)

    topic_cleanup_parser.add_argument("--path", default="/local/slo_topic", type=str, help="Topic path")


def get_root_parser():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="YDB Python SLO application",
    )

    subparsers = parser.add_subparsers(
        title="subcommands",
        dest="subcommand",
        help="List of subcommands",
    )

    make_table_create_parser(subparsers)
    make_table_run_parser(subparsers)
    make_table_cleanup_parser(subparsers)

    make_topic_create_parser(subparsers)
    make_topic_run_parser(subparsers)
    make_topic_cleanup_parser(subparsers)

    return parser


def parse_options():
    parser = get_root_parser()
    return parser.parse_args()
