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

from src.activity_feed import ActivityEvent
from src.config import Config
from src.entities import Animal, AnimalState
from src.flocking import share_pack_kill
from src.metrics import SimulationMetrics
from src.species import SPECIES_REGISTRY, SpeciesProfile
from src.terrain import BiomeType, TerrainMap, TerrainZone


BIOME_DISPLAY_NAMES = {
    BiomeType.HIGHLANDS: "Rocky Highlands",
    BiomeType.DENSE_FOREST: "Dense Forest",
    BiomeType.RIVER: "Central River",
    BiomeType.THICKETS: "Briar Thickets",
    BiomeType.MEADOW: "Meadow Plains",
}


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

    def find_all_candidates(
        self,
        x: float,
        y: float,
        radius: float,
        predicate=None,
    ) -> List[Animal]:
        """Finds all living animals within radius satisfying predicate."""
        cx = int(x // self.cell_size)
        cy = int(y // self.cell_size)
        cell_span = int(math.ceil(radius / self.cell_size))
        rad_sq = radius * radius
        candidates: List[Animal] = []

        for dx in range(-cell_span, cell_span + 1):
            for dy in range(-cell_span, cell_span + 1):
                cell_entities = self.grid.get((cx + dx, cy + dy))
                if not cell_entities:
                    continue
                for entity in cell_entities:
                    if not entity.alive:
                        continue
                    if predicate is not None and not predicate(entity):
                        continue
                    dist_sq = (entity.x - x) ** 2 + (entity.y - y) ** 2
                    if dist_sq <= rad_sq:
                        candidates.append(entity)

        return candidates


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
        self.recent_activity_events: List[ActivityEvent] = []
        self._last_birth_event_time: Dict[str, float] = {}
        self._last_exhaustion_time: Dict[int, float] = {}
        self.spatial_grid = SpatialGrid(cell_size=120.0)

        self._spawn_initial_populations()
        # Record initial population state in metrics
        self.metrics.record_detailed_snapshot(0.0, self.animals)

    def _next_id(self) -> int:
        eid = self._next_entity_id
        self._next_entity_id += 1
        return eid

    def _spawn_initial_populations(self) -> None:
        # Dynamically scale population with world area (sqrt scaling ensures natural density)
        base_area = 1200.0 * 800.0
        curr_area = self.terrain.width * self.terrain.height
        area_scale = max(1.0, math.sqrt(curr_area / base_area))

        spawn_counts = {
            "rabbit": int(80 * area_scale),
            "deer": int(18 * area_scale),
            "goat": int(16 * area_scale),
            "fox": int(10 * area_scale),
            "wolf": int(12 * area_scale),
            "bear": int(4 * area_scale),
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

    def spawn_animal(self, species_name: str, x: Optional[float] = None, y: Optional[float] = None) -> Optional[Animal]:
        """Injects an animal of species_name into the reserve at (x, y) or home zone."""
        if species_name not in SPECIES_REGISTRY:
            return None

        profile = SPECIES_REGISTRY[species_name]
        zone = self.terrain.get_home_zone_for(species_name)
        pad = 25.0

        if x is None or y is None:
            x = self.rng.uniform(zone.min_x + pad, zone.max_x - pad)
            y = self.rng.uniform(zone.min_y + pad, zone.max_y - pad)
        else:
            x = max(pad, min(self.terrain.width - pad, float(x)))
            y = max(pad, min(self.terrain.height - pad, float(y)))

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
        self.spatial_grid.insert(animal)
        return animal

    def reset(self, seed: Optional[int] = None) -> None:
        """Resets the simulation to initial state with fresh or existing seed."""
        if seed is not None:
            self.seed = seed
        self.rng = random.Random(self.seed)
        self.time = 0.0
        self._next_entity_id = 1
        self.terrain = TerrainMap(self.config.world_width, self.config.world_height)
        self.animals = []
        self.metrics = SimulationMetrics()
        self.recent_deaths = []
        self.recent_activity_events = []
        self._last_birth_event_time = {}
        self._last_exhaustion_time = {}
        self.spatial_grid = SpatialGrid(cell_size=120.0)
        self._spawn_initial_populations()
        self.metrics.record_detailed_snapshot(0.0, self.animals)

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
        self.recent_activity_events = []

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

            # Query nearby allies for collective herd flocking & wolf pack tactics
            allies = self.spatial_grid.find_all_candidates(
                a.x, a.y, a.profile.vision_radius,
                predicate=lambda candidate: candidate.profile.name == a.profile.name
            )

            caught = a.update_behavior(
                dt=dt,
                terrain=self.terrain,
                rng=self.rng,
                threat=threat,
                quarry=quarry,
                world_width=self.config.world_width,
                world_height=self.config.world_height,
                nearby_allies=allies,
            )

            if caught is not None and caught.alive:
                caught.alive = False
                caught.state = AnimalState.DIE
                self.recent_deaths.append(
                    DeathEvent(caught.profile.name, caught.x, caught.y, caught.heading, "eaten")
                )
                if caught.profile.name == "rabbit":
                    self.metrics.total_prey_eaten += 1

                b_type = self.terrain.get_biome_at(caught.x, caught.y)
                b_name = BIOME_DISPLAY_NAMES.get(b_type, "the Wilds")
                pred_name = a.profile.name.capitalize()
                prey_name = caught.profile.name.capitalize()
                self.recent_activity_events.append(
                    ActivityEvent(
                        time=self.time,
                        message=f"{pred_name} caught a {prey_name} in {b_name}",
                        category="kill",
                        species=a.profile.name,
                        biome_name=b_name,
                        x=caught.x,
                        y=caught.y,
                    )
                )

                # Pack feasting for wolves
                if a.profile.name == "wolf":
                    feasters = share_pack_kill(a, caught, allies, feasting_radius=65.0)
                    if feasters:
                        self.recent_activity_events.append(
                            ActivityEvent(
                                time=self.time,
                                message=f"Wolf pack ({len(feasters) + 1} wolves) feasted together in {b_name}",
                                category="kill",
                                species="wolf",
                                biome_name=b_name,
                                x=caught.x,
                                y=caught.y,
                            )
                        )

            if not a.alive:
                cause = "starved" if a.energy <= 0 else "age"
                self.recent_deaths.append(
                    DeathEvent(a.profile.name, a.x, a.y, a.heading, cause)
                )

            # Exhaustion tracking
            if a.alive and a.stamina < 10.0 and a.state in [AnimalState.CHASE, AnimalState.FLEE]:
                if self.time - self._last_exhaustion_time.get(a.entity_id, -10.0) >= 12.0:
                    b_type = self.terrain.get_biome_at(a.x, a.y)
                    b_name = BIOME_DISPLAY_NAMES.get(b_type, "the Wilds")
                    self.recent_activity_events.append(
                        ActivityEvent(
                            time=self.time,
                            message=f"{a.profile.name.capitalize()} exhausted from sprint",
                            category="exhaustion",
                            species=a.profile.name,
                            biome_name=b_name,
                            x=a.x,
                            y=a.y,
                        )
                    )
                    self._last_exhaustion_time[a.entity_id] = self.time

            # Escape tracking
            if a.state == AnimalState.FLEE:
                a.was_fleeing = True
            elif getattr(a, "was_fleeing", False) and a.state == AnimalState.WANDER:
                a.was_fleeing = False
                b_type = self.terrain.get_biome_at(a.x, a.y)
                b_name = BIOME_DISPLAY_NAMES.get(b_type, "the Wilds")
                self.recent_activity_events.append(
                    ActivityEvent(
                        time=self.time,
                        message=f"{a.profile.name.capitalize()} escaped into {b_name}",
                        category="escape",
                        species=a.profile.name,
                        biome_name=b_name,
                        x=a.x,
                        y=a.y,
                    )
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
            for child in newborns:
                sp_name = child.profile.name
                if self.time - self._last_birth_event_time.get(sp_name, -10.0) >= 4.0:
                    b_type = self.terrain.get_biome_at(child.x, child.y)
                    b_name = BIOME_DISPLAY_NAMES.get(b_type, "the Wilds")
                    self.recent_activity_events.append(
                        ActivityEvent(
                            time=self.time,
                            message=f"{sp_name.capitalize()} offspring born in {b_name}",
                            category="birth",
                            species=sp_name,
                            biome_name=b_name,
                            x=child.x,
                            y=child.y,
                        )
                    )
                    self._last_birth_event_time[sp_name] = self.time
                    break

        # 5. Clean up dead entities
        self.animals = [a for a in self.animals if a.alive]

        # 6. Record snapshots
        if self.metrics.should_record(self.time, self.config.metrics_interval):
            self.metrics.record_detailed_snapshot(self.time, self.animals)
