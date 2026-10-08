"""Headless simulation core for the multi-species wildlife ecosystem.

Coordinates 6 wildlife species across 5 territorial biomes, manages spatial queries,
vegetation regeneration, reproduction, and death event streams.
ZERO graphics dependencies.
"""

from __future__ import annotations
import math
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from src.config import Config
from src.entities import Animal, AnimalState
from src.metrics import SimulationMetrics
from src.species import SPECIES_REGISTRY, SpeciesProfile
from src.terrain import BiomeType, TerrainMap, TerrainZone


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

    def find_nearest_candidate(
        self,
        x: float,
        y: float,
        radius: float,
        predicate,
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
                    if not predicate(entity):
                        continue
                    dist_sq = (entity.x - x) ** 2 + (entity.y - y) ** 2
                    if dist_sq < min_dist_sq:
                        min_dist_sq = dist_sq
                        nearest = entity

        return nearest


class Simulation:
    """Multi-species wildlife simulation manager."""

    def __init__(self, config: Optional[Config] = None, seed: Optional[int] = None) -> None:
        self.config = config if config is not None else Config()
        self.seed = self.config.default_seed if seed is None else seed
        self.rng = random.Random(self.seed)

        self.time: float = 0.0
        self._next_entity_id: int = 1

        self.terrain = TerrainMap(self.config.world_width, self.config.world_height)
        self.animals: List[Animal] = []
        self.metrics = SimulationMetrics()
        self.recent_deaths: List[DeathEvent] = []
        self.spatial_grid = SpatialGrid(cell_size=120.0)

        self._spawn_initial_populations()
        # Compatibility lists for legacy metrics and tests
        self.metrics.record_snapshot(0.0, self.prey_count, self.predator_count)

    def _next_id(self) -> int:
        eid = self._next_entity_id
        self._next_entity_id += 1
        return eid

    def _spawn_initial_populations(self) -> None:
        """Spawns each species strictly inside its designated native territory."""
        spawn_counts = {
            "rabbit": 80,
            "deer": 18,
            "goat": 16,
            "fox": 10,
            "wolf": 12,
            "bear": 4,
        }

        pad = 25.0
        for sp_name, count in spawn_counts.items():
            profile = SPECIES_REGISTRY[sp_name]
            zone = self.terrain.get_home_zone_for(sp_name)

            for _ in range(count):
                x = self.rng.uniform(zone.min_x + pad, zone.max_x - pad)
                y = self.rng.uniform(zone.min_y + pad, zone.max_y - pad)
                heading = self.rng.uniform(0, 2.0 * math.pi)
                animal = Animal(
                    entity_id=self._next_id(),
                    profile=profile,
                    x=x,
                    y=y,
                    heading=heading,
                    home_zone=zone,
                )
                self.animals.append(animal)

    @property
    def prey_list(self) -> List[Animal]:
        return [a for a in self.animals if a.profile.name == "rabbit"]

    @property
    def predator_list(self) -> List[Animal]:
        return [a for a in self.animals if a.profile.name == "wolf"]

    @property
    def prey_count(self) -> int:
        return len(self.prey_list)

    @property
    def predator_count(self) -> int:
        return len(self.predator_list)

    @property
    def is_extinct(self) -> bool:
        return len(self.animals) == 0

    def step(self, dt: float) -> None:
        """Advances ecosystem simulation by dt seconds."""
        self.time += dt
        self.recent_deaths = []

        # 1. Update terrain vegetation regrowth
        self.terrain.update_regrowth(dt)

        # 2. Build spatial partition
        self.spatial_grid.clear()
        for a in self.animals:
            if a.alive:
                self.spatial_grid.insert(a)

        # 3. Behavioral updates & predation
        for a in self.animals:
            if not a.alive:
                continue

            # Threat detection: find any nearby predator that hunts this animal's species
            threat = self.spatial_grid.find_nearest_candidate(
                a.x, a.y, a.profile.vision_radius,
                predicate=lambda candidate: a.profile.name in candidate.profile.diet_prey
            )

            # Quarry detection: find nearest prey that this animal eats
            quarry = None
            if a.profile.diet_prey:
                quarry = self.spatial_grid.find_nearest_candidate(
                    a.x, a.y, a.profile.vision_radius,
                    predicate=lambda candidate: candidate.profile.name in a.profile.diet_prey
                )

            caught = a.update_behavior(
                dt=dt,
                terrain=self.terrain,
                rng=self.rng,
                threat=threat,
                quarry=quarry,
                world_width=self.config.world_width,
                world_height=self.config.world_height,
            )

            if caught is not None and caught.alive:
                caught.alive = False
                caught.state = AnimalState.DIE
                self.recent_deaths.append(
                    DeathEvent(caught.profile.name, caught.x, caught.y, caught.heading, "eaten")
                )
                if caught.profile.name == "rabbit":
                    self.metrics.total_prey_eaten += 1

            if not a.alive:
                cause = "starved" if a.energy <= 0 else "age"
                self.recent_deaths.append(
                    DeathEvent(a.profile.name, a.x, a.y, a.heading, cause)
                )

        # 4. Reproduction phase
        species_counts: Dict[str, int] = {}
        for a in self.animals:
            if a.alive:
                species_counts[a.profile.name] = species_counts.get(a.profile.name, 0) + 1

        newborns: List[Animal] = []
        for a in self.animals:
            curr_cnt = species_counts.get(a.profile.name, 0)
            cap = 160 if a.profile.name == "rabbit" else (40 if a.profile.name in ["wolf", "fox"] else 30)

            if a.can_reproduce(curr_cnt, carrying_capacity=cap):
                a.energy -= a.profile.reproduce_cost
                a.reproduction_cooldown = a.profile.reproduction_cooldown
                off_dist = self.rng.uniform(6.0, 16.0)
                off_angle = self.rng.uniform(0, 2.0 * math.pi)

                child = Animal(
                    entity_id=self._next_id(),
                    profile=a.profile,
                    x=a.x + math.cos(off_angle) * off_dist,
                    y=a.y + math.sin(off_angle) * off_dist,
                    heading=self.rng.uniform(0, 2.0 * math.pi),
                    home_zone=a.home_zone,
                )
                child.enforce_world_bounds(self.config.world_width, self.config.world_height)
                child.reproduction_cooldown = a.profile.reproduction_cooldown * 0.5
                newborns.append(child)

        if newborns:
            self.animals.extend(newborns)

        # 5. Clean up dead entities
        self.animals = [a for a in self.animals if a.alive]

        # 6. Record snapshots
        if self.metrics.should_record(self.time, self.config.metrics_interval):
            self.metrics.record_snapshot(self.time, self.prey_count, self.predator_count)
