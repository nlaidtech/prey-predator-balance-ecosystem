"""Wildlife agent entities for the multi-species ecosystem.

Implements the general Animal agent driven by SpeciesProfile, with terrain-aware
biome physics, territorial home-range leash, stamina curves, and predator-prey hunting.
Completely headless.
"""

from __future__ import annotations
import math
import random
from enum import Enum
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from src.config import Config
    from src.terrain import TerrainZone

from src.species import SPECIES_REGISTRY, SpeciesProfile, TrophicRole
from src.terrain import TerrainMap

try:
    import pygame
    BaseSprite = pygame.sprite.Sprite
except ImportError:
    class BaseSprite:
        def __init__(self, *groups):
            pass


class AnimalState(str, Enum):
    WANDER = "wander"
    CHASE = "chase"
    FLEE = "flee"
    DRINK = "drink"
    EAT = "eat"
    DIE = "die"


class Animal(BaseSprite):
    """General wildlife agent driven by data-defined species profiles."""

    def __init__(
        self,
        entity_id: int,
        profile: Optional[SpeciesProfile] = None,
        x: float = 0.0,
        y: float = 0.0,
        heading: float = 0.0,
        home_zone: Optional[TerrainZone] = None,
        species_name: Optional[str] = None,
        initial_energy: Optional[float] = None,
        speed: Optional[float] = None,
    ) -> None:
        super().__init__()
        if profile is None:
            name = species_name or "rabbit"
            profile = SPECIES_REGISTRY[name]
        self.profile = profile
        self.entity_id = entity_id
        self.x = float(x)
        self.y = float(y)
        self.heading = float(heading)
        self.speed = profile.wander_speed if speed is None else float(speed)
        self.home_zone = home_zone

        # Biological meters
        self.age = 0.0
        self.alive = True
        self.state = AnimalState.WANDER
        self.energy = profile.initial_energy if initial_energy is None else float(initial_energy)
        self.stamina = 100.0
        self.thirst = 0.0
        self.reproduction_cooldown = 0.0
        self.eat_timer = 0.0
        self.target_prey_id: Optional[int] = None

    @property
    def pos(self) -> Tuple[float, float]:
        return (self.x, self.y)

    def distance_to(self, other: Animal) -> float:
        return math.hypot(other.x - self.x, other.y - self.y)

    def angle_to(self, target_x: float, target_y: float) -> float:
        return math.atan2(target_y - self.y, target_x - self.x)

    def _move_forward(self, dt: float, speed_mult: float = 1.0) -> None:
        actual_speed = self.speed * speed_mult
        self.x += math.cos(self.heading) * actual_speed * dt
        self.y += math.sin(self.heading) * actual_speed * dt

    def enforce_world_bounds(self, width: float, height: float, padding: float = 20.0) -> None:
        if self.x < padding:
            self.x = padding
            self.heading = 0.0
        elif self.x > width - padding:
            self.x = width - padding
            self.heading = math.pi

        if self.y < padding:
            self.y = padding
            self.heading = math.pi / 2.0
        elif self.y > height - padding:
            self.y = height - padding
            self.heading = -math.pi / 2.0

    def enforce_boundaries(self, config: Config) -> None:
        """Legacy compatibility wrapper."""
        self.enforce_world_bounds(config.world_width, config.world_height, config.boundary_padding)

    def get_terrain_speed_mult(self, terrain: TerrainMap) -> float:
        props = terrain.get_properties_at(self.x, self.y)
        mult = props.base_speed_mult

        if self.profile.is_mountain_climber and props.biome_type.value == "Rocky Highlands":
            return 1.0

        if props.biome_type.value == "Thickets & Briars":
            return 0.90 if self.profile.is_small_refuge else 0.45

        return mult

    def update_behavior(
        self,
        dt: float,
        terrain: Optional[TerrainMap] = None,
        rng: Optional[random.Random] = None,
        threat: Optional[Animal] = None,
        quarry: Optional[Animal] = None,
        world_width: float = 1200.0,
        world_height: float = 800.0,
        config: Optional[Config] = None,
        nearest_predator: Optional[Animal] = None,
        nearest_prey: Optional[Animal] = None,
    ) -> Optional[Animal]:
        """Updates biology, territorial tethering, stamina, thirst, and hunting/fleeing."""
        if not self.alive:
            return None

        # Resolve legacy parameter mappings
        if threat is None and nearest_predator is not None:
            threat = nearest_predator
        if quarry is None and nearest_prey is not None:
            quarry = nearest_prey
        if terrain is None:
            terrain = TerrainMap(world_width, world_height)
        if rng is None:
            rng = random.Random(42)
        if config is not None:
            world_width, world_height = config.world_width, config.world_height

        self.age += dt
        self.thirst += 0.8 * dt
        if self.reproduction_cooldown > 0:
            self.reproduction_cooldown = max(0.0, self.reproduction_cooldown - dt)

        # Natural old age
        if self.age >= self.profile.max_age:
            self.alive = False
            self.state = AnimalState.DIE
            return None

        speed_mult = self.get_terrain_speed_mult(terrain)
        props = terrain.get_properties_at(self.x, self.y)

        # 1. Handling Eating / Feasting State
        if self.eat_timer > 0:
            self.eat_timer = max(0.0, self.eat_timer - dt)
            self.state = AnimalState.EAT
            self.energy -= self.profile.energy_decay_wander * dt
            if self.energy <= 0:
                self.alive = False
                self.state = AnimalState.DIE
            return None

        # 2. Thirst & Drinking
        if props.is_water:
            if self.thirst > 15.0:
                self.thirst = max(0.0, self.thirst - 30.0 * dt)
                self.state = AnimalState.DRINK
                self.speed = 0.0
                return None

        # 3. Stamina Recovery or Burn
        is_sprinting = self.state in [AnimalState.CHASE, AnimalState.FLEE]
        if is_sprinting:
            stamina_cost = 22.0 * dt * (1.0 if self.profile.is_mountain_climber else props.stamina_drain_mult)
            self.stamina = max(0.0, self.stamina - stamina_cost)
        else:
            self.stamina = min(100.0, self.stamina + 18.0 * dt)

        exhausted = self.stamina < 10.0

        # 4. Reaction to Threats (Fleeing)
        if threat and threat.alive:
            dist = self.distance_to(threat)
            effective_sight = self.profile.vision_radius * (1.0 - props.cover_density * 0.5)
            if dist <= effective_sight:
                self.state = AnimalState.FLEE
                away_angle = self.angle_to(threat.x, threat.y) + math.pi
                self.heading = away_angle % (2.0 * math.pi)
                self.speed = self.profile.wander_speed if exhausted else self.profile.sprint_speed
                self.energy -= self.profile.energy_decay_sprint * dt
                self._move_forward(dt, speed_mult)
                self.enforce_world_bounds(world_width, world_height)
                return None

        # 5. Predatory Pursuit (Hunting)
        caught_victim = None
        if quarry and quarry.alive:
            dist = self.distance_to(quarry)
            effective_sight = self.profile.vision_radius * (1.0 - props.cover_density * 0.4)
            if dist <= effective_sight:
                self.target_prey_id = quarry.entity_id

                # Catch check
                if dist <= self.profile.catch_radius:
                    caught_victim = quarry
                    self.energy = min(
                        self.profile.max_energy,
                        self.energy + self.profile.energy_gain_feed
                    )
                    self.eat_timer = 0.65  # Feasting pause
                    self.state = AnimalState.EAT
                    self.target_prey_id = None
                    return caught_victim

                # Pursue
                self.state = AnimalState.CHASE
                self.heading = self.angle_to(quarry.x, quarry.y)
                self.speed = self.profile.wander_speed if exhausted else self.profile.sprint_speed
                self.energy -= self.profile.energy_decay_sprint * dt
                self._move_forward(dt, speed_mult)
                self.enforce_world_bounds(world_width, world_height)

                if self.energy <= 0:
                    self.alive = False
                    self.state = AnimalState.DIE
                return caught_victim

        # 6. Routine Foraging, Grazing & Territorial Leash
        self.target_prey_id = None
        self.state = AnimalState.WANDER
        self.speed = self.profile.wander_speed
        self.energy -= self.profile.energy_decay_wander * dt

        # Herbivore grazing
        if self.profile.trophic_role == TrophicRole.HERBIVORE and self.energy < self.profile.max_energy * 0.8:
            consumed = terrain.graze_grass(self.x, self.y, amount=0.15)
            if consumed > 0.05:
                self.energy = min(self.profile.max_energy, self.energy + self.profile.energy_gain_feed * consumed)

        # Starvation check
        if self.energy <= 0:
            self.alive = False
            self.state = AnimalState.DIE
            return None

        # Steering: wander with smooth drift
        delta_angle = rng.uniform(-1.5, 1.5) * dt
        self.heading = (self.heading + delta_angle) % (2.0 * math.pi)

        # Territorial leash: gently pull back towards native zone if wandering outside
        if self.home_zone and (
            self.x < self.home_zone.min_x or self.x > self.home_zone.max_x or
            self.y < self.home_zone.min_y or self.y > self.home_zone.max_y
        ):
            target_angle = self.angle_to(self.home_zone.center[0], self.home_zone.center[1])
            diff = (target_angle - self.heading + math.pi) % (2.0 * math.pi) - math.pi
            self.heading = (self.heading + diff * 1.5 * dt) % (2.0 * math.pi)

        self._move_forward(dt, speed_mult)
        self.enforce_world_bounds(world_width, world_height)
        return None

    def can_reproduce(
        self,
        current_species_count: int = 0,
        carrying_capacity: int = 150,
        config: Optional[Config] = None,
        current_prey_count: Optional[int] = None,
        rng: Optional[random.Random] = None,
        dt: Optional[float] = None,
    ) -> bool:
        """Evaluates reproduction under energy threshold and crowding."""
        if current_prey_count is not None:
            current_species_count = current_prey_count
        if config is not None:
            carrying_capacity = config.prey_carrying_capacity
        if not self.alive or self.reproduction_cooldown > 0:
            return False
        if current_species_count >= carrying_capacity:
            return False
        return self.energy >= self.profile.reproduce_threshold


def Prey(entity_id: int, x: float = 0.0, y: float = 0.0, heading: float = 0.0, speed: float = 0.0, **kwargs) -> Animal:
    return Animal(entity_id=entity_id, profile=SPECIES_REGISTRY["rabbit"], x=x, y=y, heading=heading, speed=speed, **kwargs)


def Predator(entity_id: int, x: float = 0.0, y: float = 0.0, heading: float = 0.0, speed: float = 0.0, initial_energy: Optional[float] = None, **kwargs) -> Animal:
    return Animal(entity_id=entity_id, profile=SPECIES_REGISTRY["wolf"], x=x, y=y, heading=heading, speed=speed, initial_energy=initial_energy, **kwargs)
