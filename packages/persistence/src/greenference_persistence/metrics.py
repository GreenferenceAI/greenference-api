from __future__ import annotations

from collections import defaultdict
from threading import Lock


class MetricsStore:
    def __init__(self) -> None:
        self._counters: dict[str, float] = defaultdict(float)
        self._gauges: dict[str, float] = {}
        self._lock = Lock()

    def increment(self, name: str, value: float = 1.0) -> None:
        with self._lock:
            self._counters[name] += value

    def set_gauge(self, name: str, value: float) -> None:
        with self._lock:
            self._gauges[name] = value

    def snapshot(self) -> dict[str, dict[str, float]]:
        with self._lock:
            return {
                "counters": dict(sorted(self._counters.items())),
                "gauges": dict(sorted(self._gauges.items())),
            }


_stores: dict[str, MetricsStore] = {}


def get_metrics_store(service_name: str) -> MetricsStore:
    store = _stores.get(service_name)
    if store is None:
        store = MetricsStore()
        _stores[service_name] = store
    return store
