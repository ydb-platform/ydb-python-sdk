import asyncio
import logging
from typing import Dict

from runners.base import BaseRunner
from runners.table_runner import TableRunner
from runners.topic_runner import TopicRunner

import ydb
import ydb.aio

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

        # Check if async mode is requested and command is 'run'
        if getattr(args, "async", False) and command == "run":
            asyncio.run(self._run_async_command(args, runner_instance, command))
        else:
            self._run_sync_command(args, runner_instance, command)

    def _run_sync_command(self, args, runner_instance, command):
        """Run command in synchronous mode"""
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
                    raise RuntimeError(f"Unknown command {command} for prefix {runner_instance.prefix}")
            except BaseException:
                logger.exception("Something went wrong")
                raise
            finally:
                driver.stop(timeout=getattr(args, "shutdown_time", 10))

    async def _run_async_command(self, args, runner_instance, command):
        """Run command in asynchronous mode"""
        driver_config = ydb.DriverConfig(
            args.endpoint,
            database=args.db,
            grpc_keep_alive_timeout=5000,
        )

        async with ydb.aio.Driver(driver_config) as driver:
            await driver.wait(timeout=300)
            try:
                runner_instance.set_driver(driver)
                if command == "run":
                    await runner_instance.run_async(args)
                else:
                    raise RuntimeError(f"Async mode only supports 'run' command, got '{command}'")
            except BaseException:
                logger.exception("Something went wrong in async mode")
                raise


def create_runner() -> SLORunner:
    runner = SLORunner()
    runner.register_runner("table", TableRunner)
    runner.register_runner("topic", TopicRunner)
    return runner


def run_from_args(args):
    runner = create_runner()
    runner.run_command(args)
