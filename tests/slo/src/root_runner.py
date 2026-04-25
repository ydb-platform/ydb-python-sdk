import asyncio
import logging

from runners.table_runner import TableRunner
from runners.topic_runner import TopicRunner

import ydb
import ydb.aio

logger = logging.getLogger(__name__)

_RUNNERS = {
    "sync-table": TableRunner,
    "sync-query": TableRunner,
    "topic": TopicRunner,
}


def _get_runner(workload_name: str):
    runner_cls = _RUNNERS.get(workload_name)
    if runner_cls is None:
        raise ValueError(f"Unknown workload_name: {workload_name!r}. Known: {list(_RUNNERS)}")
    return runner_cls()


def run_all(args):
    """Create infrastructure, run the workload, then clean up — all in one go."""
    if args.async_mode:
        asyncio.run(_run_all_async(args))
    else:
        _run_all_sync(args)


def _run_all_sync(args):
    workload_name = args.workload_name
    runner = _get_runner(workload_name)

    driver_config = ydb.DriverConfig(
        args.endpoint,
        database=args.db,
        grpc_keep_alive_timeout=5000,
    )

    with ydb.Driver(driver_config) as driver:
        driver.wait(timeout=300)
        runner.set_driver(driver)

        try:
            logger.info("[%s] Creating resources", workload_name)
            runner.create(args)

            logger.info("[%s] Running workload for %d s", workload_name, args.time)
            runner.run(args)
        finally:
            logger.info("[%s] Cleaning up resources", workload_name)
            try:
                runner.cleanup(args)
            except Exception:
                logger.exception("Cleanup failed — ignoring")

        driver.stop(timeout=args.shutdown_time)


async def _run_all_async(args):
    workload_name = args.workload_name
    runner = _get_runner(workload_name)

    driver_config = ydb.DriverConfig(
        args.endpoint,
        database=args.db,
        grpc_keep_alive_timeout=5000,
    )

    async with ydb.aio.Driver(driver_config) as driver:
        await driver.wait(timeout=300)
        runner.set_driver(driver)

        try:
            logger.info("[%s][async] Creating resources", workload_name)
            await runner.create_async(args)

            logger.info("[%s][async] Running workload for %d s", workload_name, args.time)
            await runner.run_async(args)
        finally:
            logger.info("[%s][async] Cleaning up resources", workload_name)
            try:
                await runner.cleanup_async(args)
            except Exception:
                logger.exception("Cleanup failed — ignoring")
