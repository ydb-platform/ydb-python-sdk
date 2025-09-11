from .base import BaseRunner
from workloads.table_workload import TableWorkload
from core.metrics import Metrics
from core.dummy_metrics import DummyMetrics


class TableRunner(BaseRunner):
    @property
    def prefix(self) -> str:
        return "table"

    def create(self, args):
        workload = TableWorkload(self.driver, args)
        workload.create()

    def run(self, args):
        workload = TableWorkload(self.driver, args)

        if args.prom_pgw:
            metrics = Metrics(args.prom_pgw)
        else:
            self.logger.info("Prometheus disabled, creating dummy metrics")
            metrics = DummyMetrics()

        workload.run_slo(metrics)

        if hasattr(metrics, "reset"):
            metrics.reset()

    def cleanup(self, args):
        workload = TableWorkload(self.driver, args)
        workload.cleanup()
