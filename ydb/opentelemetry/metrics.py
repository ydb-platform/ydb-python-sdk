"""No-op-safe helpers for YDB OpenTelemetry metrics."""

from typing import Any, Dict, Optional

QUERY_SESSION_COUNT = "ydb.query.session.count"


class MetricsRegistry:
    def __init__(self) -> None:
        self._instruments: Dict[str, Any] = {}

    def set_meter(self, meter: Any) -> None:
        self._instruments = {
            QUERY_SESSION_COUNT: meter.create_up_down_counter(
                QUERY_SESSION_COUNT,
                unit="{connection}",
                description="Number of open YDB query sessions.",
            )
        }

    def clear(self) -> None:
        self._instruments = {}

    def add(self, name: str, value: int, attributes: Optional[Dict[str, str]] = None) -> None:
        instrument = self._instruments.get(name)
        if instrument is not None:
            instrument.add(value, attributes=attributes or {})


_metrics_registry = MetricsRegistry()


def record_query_session_count(delta: int) -> None:
    _metrics_registry.add(QUERY_SESSION_COUNT, delta)
