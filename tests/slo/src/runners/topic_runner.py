from .base import BaseRunner
from workloads.topic_workload import TopicWorkload
from core.metrics import Metrics
from core.dummy_metrics import DummyMetrics


class TopicRunner(BaseRunner):
    @property
    def prefix(self) -> str:
        return "topic"

    def create(self, args):
        workload = TopicWorkload(self.driver, args)
        workload.create()

    def run(self, args):
        workload = TopicWorkload(self.driver, args)

        if args.prom_pgw:
            metrics = Metrics(args.prom_pgw)
        else:
            self.logger.info("Prometheus disabled, creating dummy metrics")
            metrics = DummyMetrics()

        workload.run_slo(metrics)

        if hasattr(metrics, "reset"):
            metrics.reset()

    def cleanup(self, args):
        workload = TopicWorkload(self.driver, args)
        workload.cleanup()
