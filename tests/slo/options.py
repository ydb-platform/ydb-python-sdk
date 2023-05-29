import argparse


def add_common_options(parser):
    parser.add_argument("endpoint", help="YDB endpoint")
    parser.add_argument("db", help="YDB database name")
    parser.add_argument("-t", "--table_name", default="key_value", help="Table name")
    parser.add_argument("--write_timeout", default=20000, type=int, help="Read requests execution timeout [ms]")


def make_create_parser(subparsers):
    create_parser = subparsers.add_parser("create", help="Create tables and fill with initial content")
    add_common_options(create_parser)
    create_parser.add_argument("-p", "--partitions_count", default=64, type=int, help="Number of partition in table")
    create_parser.add_argument(
        "-c", "--initial-data-count", default=1000, type=int, help="Total number of records to generate"
    )
    create_parser.add_argument(
        "--pack_size", default="100", type=int, help="Number of new records in each create request"
    )


def make_run_parser(subparsers, name="run"):
    run_parser = subparsers.add_parser(name, help="Run measurable workload")
    add_common_options(run_parser)
    run_parser.add_argument("--write_rps", default=10, type=int, help="Write request rps")
    run_parser.add_argument("--read_rps", default=100, type=int, help="Read request rps")
    run_parser.add_argument("--no_write", default=False, action="store_true")
    run_parser.add_argument("--no_read", default=False, action="store_true")
    run_parser.add_argument("--time", default=10, type=int, help="Time to run (Seconds)")
    run_parser.add_argument("--read_timeout", default=70, type=int, help="Read requests execution timeout [ms]")
    run_parser.add_argument("--save_result", default=False, action="store_true", help="Save result to file")
    run_parser.add_argument("--result_file_name", default="slo_result.json", help="Result json file name")
    run_parser.add_argument("--no_prepare", default=False, action="store_true", help="Do not prepare requests")


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
