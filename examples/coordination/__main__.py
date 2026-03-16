import argparse
import asyncio
import logging

from example import run as run_sync
from example_async import run as run_async

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\033[92mYDB coordination example.\x1b[0m\n""",
    )
    parser.add_argument("-e", "--endpoint", help="Endpoint url to use", default="grpc://localhost:2136")
    parser.add_argument("-d", "--database", help="Name of the database to use", default="/local")
    parser.add_argument("-v", "--verbose", default=False, action="store_true")
    parser.add_argument("-m", "--mode", default="sync", help="Mode of example: sync or async")

    args = parser.parse_args()

    if args.verbose:
        logger = logging.getLogger("ydb")
        logger.setLevel(logging.INFO)
        logger.addHandler(logging.StreamHandler())

    if args.mode == "sync":
        print("Running sync example")
        run_sync(
            args.endpoint,
            args.database,
        )
    elif args.mode == "async":
        print("Running async example")
        asyncio.run(
            run_async(
                args.endpoint,
                args.database,
            )
        )
    else:
        raise ValueError(f"Unsupported mode: {args.mode}, use one of sync|async")
