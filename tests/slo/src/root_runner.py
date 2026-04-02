import asyncio
import logging

from core.metrics import WORKLOAD_NAME
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


def _get_runner():
    runner_cls = _RUNNERS.get(WORKLOAD_NAME)
    if runner_cls is None:
        raise ValueError(
            f"Unknown WORKLOAD_NAME: {WORKLOAD_NAME!r}. Known: {list(_RUNNERS)}"
        )
    return runner_cls()


def run_all(args):
    """Create infrastructure, run the workload, then clean up — all in one go."""
    runner = _get_runner()

    driver_config = ydb.DriverConfig(
        args.endpoint,
        database=args.db,
        grpc_keep_alive_timeout=5000,
    )

    with ydb.Driver(driver_config) as driver:
        driver.wait(timeout=300)
        runner.set_driver(driver)

        try:
            logger.info("[%s] Creating resources", WORKLOAD_NAME)
            runner.create(args)

            logger.info("[%s] Running workload for %d s", WORKLOAD_NAME, args.time)
            runner.run(args)
        finally:
            logger.info("[%s] Cleaning up resources", WORKLOAD_NAME)
            try:
                runner.cleanup(args)
            except Exception:
                logger.exception("Cleanup failed — ignoring")

        driver.stop(timeout=args.shutdown_time)
