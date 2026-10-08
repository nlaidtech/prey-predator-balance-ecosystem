"""Headless simulation core for the predator-prey ecosystem.

Implements the pure simulation rules, step loop, deterministic PRNG,
spatial hashing queries for high performance, reproduction, and metrics logging.
Contains ZERO rendering or UI dependencies.
"""

from __future__ import annotations
import math
import random
from typing import Dict, List, Optional, Tuple

from dataclasses import dataclass
from src.config import Config
from src.entities import Animal, AnimalState, Prey, Predator
from src.metrics import SimulationMetrics


@dataclass(frozen=True)
class DeathEvent:
    species: str
    x: float
    y: float
    heading: float
    cause: str


class SpatialGrid:
    """Fast 2D grid partitioning for local spatial queries."""

    def __init__(self, cell_size: float = 120.0) -> None:
        self.cell_size = cell_size
        self.grid: Dict[Tuple[int, int], List[Animal]] = {}

    def clear(self) -> None:
        self.grid.clear()

    def insert(self, entity: Animal) -> None:
        cx = int(entity.x // self.cell_size)
        cy = int(entity.y // self.cell_size)
        cell = (cx, cy)
        if cell not in self.grid:
            self.grid[cell] = [entity]
        else:
            self.grid[cell].append(entity)

    def find_nearest_in_radius(
        self,
        x: float,
        y: float,
        radius: float,
    ) -> Optional[Animal]:
        cx = int(x // self.cell_size)
        cy = int(y // self.cell_size)
        cell_span = int(math.ceil(radius / self.cell_size))

        nearest: Optional[Animal] = None
        min_dist_sq = radius * radius

        for dx in range(-cell_span, cell_span + 1):
            for dy in range(-cell_span, cell_span + 1):
                cell_entities = self.grid.get((cx + dx, cy + dy))
                if not cell_entities:
                    continue
                for entity in cell_entities:
                    if not entity.alive:
                        continue
                    dist_sq = (entity.x - x) ** 2 + (entity.y - y) ** 2
                    if dist_sq < min_dist_sq:
                        min_dist_sq = dist_sq
                        nearest = entity

        return nearest


class Simulation:
    """Manages the ecosystem simulation state and rules."""

    def __init__(self, config: Optional[Config] = None, seed: Optional[int] = None) -> None:
        self.config = config if config is not None else Config()
        self.seed = self.config.default_seed if seed is None else seed
        self.rng = random.Random(self.seed)

        self.time: float = 0.0
        self._next_entity_id: int = 1

        self.prey_list: List[Prey] = []
        self.predator_list: List[Predator] = []
        self.metrics = SimulationMetrics()

        self.prey_grid = SpatialGrid(cell_size=120.0)
        self.predator_grid = SpatialGrid(cell_size=120.0)

        self._initialize_population()
        self.metrics.record_snapshot(0.0, len(self.prey_list), len(self.predator_list))

    def _next_id(self) -> int:
        eid = self._next_entity_id
        self._next_entity_id += 1
        return eid

    def _initialize_population(self) -> None:
        pad = self.config.boundary_padding
        w = self.config.world_width
        h = self.config.world_height

        for _ in range(self.config.initial_prey):
            x = self.rng.uniform(pad, w - pad)
            y = self.rng.uniform(pad, h - pad)
            heading = self.rng.uniform(0, 2.0 * math.pi)
            prey = Prey(
                entity_id=self._next_id(),
                x=x,
                y=y,
                heading=heading,
                speed=self.config.prey_wander_speed,
            )
            self.prey_list.append(prey)

        for _ in range(self.config.initial_predators):
            x = self.rng.uniform(pad, w - pad)
            y = self.rng.uniform(pad, h - pad)
            heading = self.rng.uniform(0, 2.0 * math.pi)
            predator = Predator(
                entity_id=self._next_id(),
                x=x,
                y=y,
                heading=heading,
                speed=self.config.predator_wander_speed,
                initial_energy=self.config.predator_initial_energy,
            )
            self.predator_list.append(predator)

    def _rebuild_spatial_grids(self) -> None:
        self.prey_grid.clear()
        for prey in self.prey_list:
            if prey.alive:
                self.prey_grid.insert(prey)

        self.predator_grid.clear()
        for pred in self.predator_list:
            if pred.alive:
                self.predator_grid.insert(pred)

    def step(self, dt: float) -> None:
        """Advances the simulation by dt seconds."""
        self.time += dt
        cfg = self.config

        # Build fast spatial lookup grids
        self._rebuild_spatial_grids()

        self.recent_deaths: List[DeathEvent] = []

        # 1. Update Prey behaviors
        for prey in self.prey_list:
            if not prey.alive:
                continue
            nearest_pred = self.predator_grid.find_nearest_in_radius(
                prey.x, prey.y, cfg.prey_vision_radius
            )
            prey.update_behavior(dt, cfg, self.rng, nearest_pred)  # type: ignore
            if not prey.alive and prey.state == AnimalState.DIE:
                self.metrics.total_prey_died_age += 1
                self.recent_deaths.append(
                    DeathEvent("rabbit", prey.x, prey.y, prey.heading, "age")
                )

        # 2. Update Predator behaviors & hunting
        for pred in self.predator_list:
            if not pred.alive:
                continue
            nearest_prey = self.prey_grid.find_nearest_in_radius(
                pred.x, pred.y, cfg.predator_vision_radius
            )
            caught = pred.update_behavior(dt, cfg, self.rng, nearest_prey)  # type: ignore
            if caught is not None and caught.alive:
                caught.alive = False
                caught.state = AnimalState.DIE
                self.metrics.total_prey_eaten += 1
                self.recent_deaths.append(
                    DeathEvent("rabbit", caught.x, caught.y, caught.heading, "eaten")
                )

            if not pred.alive:
                if pred.energy <= 0:
                    self.metrics.total_predators_starved += 1
                    self.recent_deaths.append(
                        DeathEvent("wolf", pred.x, pred.y, pred.heading, "starved")
                    )
                elif pred.age >= cfg.predator_max_age:
                    self.metrics.total_predators_died_age += 1
                    self.recent_deaths.append(
                        DeathEvent("wolf", pred.x, pred.y, pred.heading, "age")
                    )

        # 3. Reproduction phase
        current_prey_count = len([p for p in self.prey_list if p.alive])
        new_prey: List[Prey] = []
        for prey in self.prey_list:
            if prey.can_reproduce(cfg, current_prey_count, self.rng, dt):
                prey.reproduction_cooldown = cfg.prey_reproduction_cooldown
                offset_dist = self.rng.uniform(5.0, 15.0)
                offset_angle = self.rng.uniform(0, 2.0 * math.pi)
                child = Prey(
                    entity_id=self._next_id(),
                    x=prey.x + math.cos(offset_angle) * offset_dist,
                    y=prey.y + math.sin(offset_angle) * offset_dist,
                    heading=self.rng.uniform(0, 2.0 * math.pi),
                    speed=cfg.prey_wander_speed,
                )
                child.enforce_boundaries(cfg)
                child.reproduction_cooldown = cfg.prey_reproduction_cooldown * 0.5
                new_prey.append(child)
                self.metrics.total_prey_born += 1

        new_predators: List[Predator] = []
        for pred in self.predator_list:
            if pred.can_reproduce(cfg):
                pred.energy -= cfg.predator_reproduce_cost
                pred.reproduction_cooldown = cfg.predator_reproduction_cooldown
                offset_dist = self.rng.uniform(5.0, 15.0)
                offset_angle = self.rng.uniform(0, 2.0 * math.pi)
                child = Predator(
                    entity_id=self._next_id(),
                    x=pred.x + math.cos(offset_angle) * offset_dist,
                    y=pred.y + math.sin(offset_angle) * offset_dist,
                    heading=self.rng.uniform(0, 2.0 * math.pi),
                    speed=cfg.predator_wander_speed,
                    initial_energy=cfg.predator_reproduce_cost,
                )
                child.enforce_boundaries(cfg)
                child.reproduction_cooldown = cfg.predator_reproduction_cooldown * 0.5
                new_predators.append(child)
                self.metrics.total_predators_born += 1

        # 4. Integrate newborn animals
        if new_prey:
            self.prey_list.extend(new_prey)
        if new_predators:
            self.predator_list.extend(new_predators)

        # 5. Clean up dead entities
        self.prey_list = [p for p in self.prey_list if p.alive]
        self.predator_list = [p for p in self.predator_list if p.alive]

        # 6. Record metrics once per simulated second
        if self.metrics.should_record(self.time, cfg.metrics_interval):
            self.metrics.record_snapshot(self.time, len(self.prey_list), len(self.predator_list))

    @property
    def prey_count(self) -> int:
        return len(self.prey_list)

    @property
    def predator_count(self) -> int:
        return len(self.predator_list)

    @property
    def is_extinct(self) -> bool:
        return self.prey_count == 0 or self.predator_count == 0
