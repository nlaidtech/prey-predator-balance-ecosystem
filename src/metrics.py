"""Simulation metrics collection and time-series history.

Records rolling multi-species population history over a 90–120s buffer,
calculates real-time species population trends, evaluates ecological equilibrium,
and stores historical snapshots for plotting.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class MetricSnapshot:
    time: float
    prey_count: int
    predator_count: int


@dataclass(frozen=True)
class DetailedSpeciesSnapshot:
    time: float
    counts: Dict[str, int]
    total_herbivores: int
    total_carnivores: int


@dataclass
class SimulationMetrics:
    snapshots: List[MetricSnapshot] = field(default_factory=list)
    detailed_history: List[DetailedSpeciesSnapshot] = field(default_factory=list)
    history_window: float = 120.0  # Rolling buffer duration in seconds

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
        """Legacy recorder preserving full backward-compatibility for tests and benchmarks."""
        self.snapshots.append(MetricSnapshot(
            time=current_time,
            prey_count=prey_count,
            predator_count=predator_count,
        ))
        self.last_record_time = current_time

    def record_detailed_snapshot(self, current_time: float, animals_or_counts: any) -> None:
        """Records per-second counts for all individual species into the rolling buffer."""
        if isinstance(animals_or_counts, dict):
            counts = {
                "rabbit": animals_or_counts.get("rabbit", 0),
                "deer": animals_or_counts.get("deer", 0),
                "goat": animals_or_counts.get("goat", 0),
                "fox": animals_or_counts.get("fox", 0),
                "wolf": animals_or_counts.get("wolf", 0),
                "bear": animals_or_counts.get("bear", 0),
            }
        else:
            counts = {
                "rabbit": 0,
                "deer": 0,
                "goat": 0,
                "fox": 0,
                "wolf": 0,
                "bear": 0,
            }
            for a in animals_or_counts:
                if getattr(a, "alive", False):
                    sp_name = getattr(a.profile, "name", "")
                    if sp_name in counts:
                        counts[sp_name] += 1

        herbivores = counts["rabbit"] + counts["deer"] + counts["goat"]
        carnivores = counts["fox"] + counts["wolf"] + counts["bear"]

        # Record detailed entry
        self.detailed_history.append(DetailedSpeciesSnapshot(
            time=current_time,
            counts=counts,
            total_herbivores=herbivores,
            total_carnivores=carnivores,
        ))

        # Also maintain legacy snapshots
        self.record_snapshot(current_time, counts["rabbit"], counts["wolf"])

        # Prune rolling window buffer older than history_window
        min_time = current_time - self.history_window
        while self.detailed_history and self.detailed_history[0].time < min_time:
            self.detailed_history.pop(0)

    def get_species_trend(self, species_name: str, window_seconds: float = 15.0) -> Tuple[str, int]:
        """Calculates population trend (rising, declining, stable) and delta over window."""
        if not self.detailed_history:
            return ("stable", 0)

        latest = self.detailed_history[-1]
        latest_count = latest.counts.get(species_name, 0)
        target_time = latest.time - window_seconds

        # Find earliest snapshot within window
        past_snapshot = self.detailed_history[0]
        for snap in self.detailed_history:
            if snap.time >= target_time:
                past_snapshot = snap
                break

        past_count = past_snapshot.counts.get(species_name, 0)
        delta = latest_count - past_count

        if delta > 1:
            return ("rising", delta)
        elif delta < -1:
            return ("declining", delta)
        return ("stable", delta)

    def get_equilibrium_status(self) -> Tuple[bool, str]:
        """Evaluates whether both prey and predators have stable non-zero coexistences."""
        if not self.detailed_history:
            return (True, "EQUILIBRIUM STABLE")

        latest = self.detailed_history[-1]
        counts = latest.counts

        if latest.total_herbivores == 0:
            return (False, "PREY EXTINCTION COLLAPSE")
        if latest.total_carnivores == 0:
            return (False, "PREDATOR EXTINCTION DETECTED")

        # Check for critical thresholds
        if counts.get("rabbit", 0) < 10 or counts.get("wolf", 0) < 2:
            return (False, "VOLATILE POPULATION DIP")

        return (True, "DYNAMIC EQUILIBRIUM")

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
