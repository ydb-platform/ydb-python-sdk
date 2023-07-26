import argparse


def add_common_options(parser):
    parser.add_argument("endpoint", help="YDB endpoint")
    parser.add_argument("db", help="YDB database name")
    parser.add_argument("-t", "--table-name", default="key_value", help="Table name")


def make_create_parser(subparsers):
    create_parser = subparsers.add_parser("create", help="Create tables and fill with initial content")
    add_common_options(create_parser)

    create_parser.add_argument(
        "-p-min", "--min-partitions-count", default=6, type=int, help="Minimum amount of partitions in table"
    )
    create_parser.add_argument(
        "-p-max", "--max-partitions-count", default=1000, type=int, help="Maximum amount of partitions in table"
    )
    create_parser.add_argument("-p-size", "--partition-size", default=100, type=int, help="Partition size [mb]")
    create_parser.add_argument(
        "-c", "--initial-data-count", default=1000, type=int, help="Total number of records to generate"
    )

    create_parser.add_argument("--write-timeout", default=20000, type=int, help="Write requests execution timeout [ms]")

    create_parser.add_argument(
        "--batch-size", default=100, type=int, help="Number of new records in each create request"
    )
    create_parser.add_argument("--threads", default=10, type=int, help="Number of threads to use")


def make_run_parser(subparsers, name="run"):
    run_parser = subparsers.add_parser(name, help="Run measurable workload")
    add_common_options(run_parser)

    run_parser.add_argument("--read-rps", default=100, type=int, help="Read request rps")
    run_parser.add_argument("--read-timeout", default=10000, type=int, help="Read requests execution timeout [ms]")

    run_parser.add_argument("--write-rps", default=10, type=int, help="Write request rps")
    run_parser.add_argument("--write-timeout", default=20000, type=int, help="Write requests execution timeout [ms]")

    run_parser.add_argument("--time", default=10, type=int, help="Time to run in seconds")
    run_parser.add_argument("--shutdown-time", default=10, type=int, help="Graceful shutdown time in seconds")

    run_parser.add_argument("--prom-pgw", default="localhost:9091", type=str, help="Prometheus push gateway")
    run_parser.add_argument("--report-period", default=1000, type=int, help="Prometheus push period [ms]")

    run_parser.add_argument("--read-threads", default=8, type=int, help="Number of threads to use for write")
    run_parser.add_argument("--write-threads", default=4, type=int, help="Number of threads to use for read")


def make_cleanup_parser(subparsers):
    cleanup_parser = subparsers.add_parser("cleanup", help="Drop tables")
    add_common_options(cleanup_parser)


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

    make_create_parser(subparsers)
    make_run_parser(subparsers)
    make_cleanup_parser(subparsers)

    return parser


def parse_options():
    parser = get_root_parser()
    return parser.parse_args()
