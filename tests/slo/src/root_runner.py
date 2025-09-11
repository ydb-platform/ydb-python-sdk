import ydb
import logging
from typing import Dict

from runners.topic_runner import TopicRunner
from runners.table_runner import TableRunner
from runners.base import BaseRunner

logger = logging.getLogger(__name__)


class SLORunner:
    def __init__(self):
        self.runners: Dict[str, type(BaseRunner)] = {}

    def register_runner(self, prefix: str, runner_cls: type(BaseRunner)):
        self.runners[prefix] = runner_cls

    def run_command(self, args):
        subcommand_parts = args.subcommand.split("-", 1)
        if len(subcommand_parts) < 2:
            raise ValueError(f"Invalid subcommand format: {args.subcommand}. Expected 'prefix-command'")

        prefix, command = subcommand_parts
        if prefix not in self.runners:
            raise ValueError(f"Unknown prefix: {prefix}. Available: {list(self.runners.keys())}")

        runner_instance = self.runners[prefix]()
        driver_config = ydb.DriverConfig(
            args.endpoint,
            database=args.db,
            grpc_keep_alive_timeout=5000,
        )

        with ydb.Driver(driver_config) as driver:
            driver.wait(timeout=300)
            try:
                runner_instance.set_driver(driver)
                if command == "create":
                    runner_instance.create(args)
                elif command == "run":
                    runner_instance.run(args)
                elif command == "cleanup":
                    runner_instance.cleanup(args)
                else:
                    raise RuntimeError(f"Unknown command {command} for prefix {prefix}")
            except BaseException:
                logger.exception("Something went wrong")
                raise
            finally:
                driver.stop(timeout=getattr(args, "shutdown_time", 10))


def create_runner() -> SLORunner:
    runner = SLORunner()
    runner.register_runner("table", TableRunner)
    runner.register_runner("topic", TopicRunner)
    return runner


def run_from_args(args):
    runner = create_runner()
    runner.run_command(args)
