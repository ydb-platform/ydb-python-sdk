import time
from typing import Iterable, Optional, Sequence, Tuple
from threading import Lock

from prometheus_client import Summary as _Summary, CollectorRegistry, REGISTRY
from prometheus_client.utils import floatToGoString
from prometheus_client.samples import Sample

from quantile_estimator import TimeWindowEstimator


class Summary(_Summary):
    DEFAULT_OBJECTIVES = (
        (0.5, 0.01),
        (0.99, 0.001),
        (1.0, 0.0001),
    )

    def __init__(
        self,
        name: str,
        documentation: str,
        labelnames: Iterable[str] = (),
        namespace: str = "",
        subsystem: str = "",
        unit: str = "",
        registry: Optional[CollectorRegistry] = REGISTRY,
        _labelvalues: Optional[Sequence[str]] = None,
        objectives: Sequence[Tuple[float, float]] = DEFAULT_OBJECTIVES,
    ):
        self._objectives = objectives
        super().__init__(
            name=name,
            documentation=documentation,
            labelnames=labelnames,
            namespace=namespace,
            subsystem=subsystem,
            unit=unit,
            registry=registry,
            _labelvalues=_labelvalues,
        )
        self._kwargs["objectives"] = objectives
        self._lock = Lock()

    def _metric_init(self) -> None:
        super()._metric_init()

        self._estimator = TimeWindowEstimator(*self._objectives)
        self._created = time.time()

    def observe(self, amount: float) -> None:
        super().observe(amount)
        with self._lock:
            self._estimator.observe(amount)

    def _child_samples(self) -> Iterable[Sample]:
        samples = []
        for q, _ in self._objectives:
            with self._lock:
                value = self._estimator.query(q)
            samples.append(Sample("", {"quantile": floatToGoString(q)}, value, None, None))

        samples.extend(super()._child_samples())
        return tuple(samples)
