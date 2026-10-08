"""Simulation metrics collection.

Records time-series snapshots of population counts and lifetime statistics
for headless balance tuning, evaluation, and plotting.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class MetricSnapshot:
    time: float
    prey_count: int
    predator_count: int


@dataclass
class SimulationMetrics:
    snapshots: List[MetricSnapshot] = field(default_factory=list)
    total_prey_born: int = 0
    total_prey_eaten: int = 0
    total_prey_died_age: int = 0
    total_predators_born: int = 0
    total_predators_starved: int = 0
    total_predators_died_age: int = 0
    last_record_time: float = -1.0

    def should_record(self, current_time: float, interval: float, tolerance: float = 1e-5) -> bool:
        if self.last_record_time < 0:
            return True
        return (current_time - self.last_record_time) >= (interval - tolerance)

    def record_snapshot(self, current_time: float, prey_count: int, predator_count: int) -> None:
        self.snapshots.append(MetricSnapshot(
            time=current_time,
            prey_count=prey_count,
            predator_count=predator_count
        ))
        self.last_record_time = current_time

    @property
    def survived_seconds(self) -> float:
        if not self.snapshots:
            return 0.0
        return self.snapshots[-1].time

    def is_extinct(self) -> bool:
        if not self.snapshots:
            return False
        latest = self.snapshots[-1]
        return latest.prey_count == 0 or latest.predator_count == 0
