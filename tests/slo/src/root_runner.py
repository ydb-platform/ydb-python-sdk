import asyncio
import ydb
import ydb.aio
import logging
from typing import Dict

from core.metrics import WORKLOAD
from runners.topic_runner import TopicRunner
from runners.table_runner import TableRunner
from runners.rmw_runner import RmwRunner
from runners.base import BaseRunner

logger = logging.getLogger(__name__)


def _is_async_workload(args) -> bool:
    """Async mode is driven by the workload label (``async-*``); the ``--async``
    CLI flag is kept as a manual override. RMW has only an async Query adapter."""
    return args.subcommand == "rmw-run" or getattr(args, "async", False) or str(WORKLOAD).startswith("async-")


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

        # Async mode (driven by the workload label, e.g. async-query / async-topic)
        # only applies to the long-running `run` command; create/cleanup stay sync.
        if _is_async_workload(args) and command == "run":
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

        failure = None
        try:
            with ydb.Driver(driver_config) as driver:
                try:
                    driver.wait(timeout=300)
                    runner_instance.set_driver(driver)
                    if command == "create":
                        runner_instance.create(args)
                    elif command == "run":
                        runner_instance.run(args)
                    elif command == "cleanup":
                        runner_instance.cleanup(args)
                    else:
                        raise RuntimeError(f"Unknown command {command} for prefix {runner_instance.prefix}")
                except BaseException as error:
                    failure = error
                    logger.exception("Something went wrong")
                    raise
                finally:
                    driver.stop(timeout=getattr(args, "shutdown_time", 10))
        except BaseException as error:
            if failure is not None and error is not failure:
                raise failure from error
            raise

    async def _run_async_command(self, args, runner_instance, command):
        """Run command in asynchronous mode"""
        driver_config = ydb.DriverConfig(
            args.endpoint,
            database=args.db,
            grpc_keep_alive_timeout=5000,
        )

        failure = None
        try:
            async with ydb.aio.Driver(driver_config) as driver:
                try:
                    await driver.wait(timeout=300)
                    runner_instance.set_driver(driver)
                    if command == "run":
                        await runner_instance.run_async(args)
                    else:
                        raise RuntimeError(f"Async mode only supports 'run' command, got '{command}'")
                except BaseException as error:
                    failure = error
                    logger.exception("Something went wrong in async mode")
                    raise
        except BaseException as error:
            if failure is not None and error is not failure:
                raise failure from error
            raise


def create_runner() -> SLORunner:
    runner = SLORunner()
    runner.register_runner("table", TableRunner)
    runner.register_runner("topic", TopicRunner)
    runner.register_runner("rmw", RmwRunner)
    return runner


def run_from_args(args):
    runner = create_runner()
    runner.run_command(args)
