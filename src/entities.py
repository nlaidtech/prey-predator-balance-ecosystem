"""Entity models for the predator-prey ecosystem.

Implements the Animal base class and the specialized Prey and Predator classes.
The simulation core updates entity states, positions, and interactions without
performing any drawing or rendering.
"""

from __future__ import annotations
import math
import random
from enum import Enum
from typing import Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from src.config import Config

try:
    import pygame
    BaseSprite = pygame.sprite.Sprite
except ImportError:  # Fallback if running in a minimal environment without pygame
    class BaseSprite:
        def __init__(self, *groups):
            pass


class AnimalState(str, Enum):
    WANDER = "wander"
    CHASE = "chase"
    FLEE = "flee"
    EAT = "eat"
    DIE = "die"


class Animal(BaseSprite):
    """Base class for all animals in the ecosystem.
    
    Manages position, heading, movement vector, age, behavior state,
    and boundary steering.
    """

    def __init__(
        self,
        entity_id: int,
        x: float,
        y: float,
        heading: float = 0.0,
        speed: float = 0.0,
    ) -> None:
        super().__init__()
        self.entity_id = entity_id
        self.x = float(x)
        self.y = float(y)
        self.heading = float(heading)  # Radians: 0 pointing right (east)
        self.speed = float(speed)
        self.age = 0.0
        self.alive = True
        self.state = AnimalState.WANDER
        self.reproduction_cooldown = 0.0

    @property
    def pos(self) -> Tuple[float, float]:
        return (self.x, self.y)

    def distance_to(self, other: Animal) -> float:
        return math.hypot(other.x - self.x, other.y - self.y)

    def angle_to(self, target_x: float, target_y: float) -> float:
        return math.atan2(target_y - self.y, target_x - self.x)

    def wander(self, rng: random.Random, dt: float, turn_rate: float, speed: float) -> None:
        """Perturbs heading with a smooth random walk and moves forward."""
        delta_angle = rng.uniform(-turn_rate, turn_rate) * dt
        self.heading = (self.heading + delta_angle) % (2.0 * math.pi)
        self.speed = speed
        self._move_forward(dt)

    def move_toward(self, target_x: float, target_y: float, speed: float, dt: float) -> None:
        """Directs heading toward target coordinates and advances."""
        self.heading = self.angle_to(target_x, target_y)
        self.speed = speed
        self._move_forward(dt)

    def move_away_from(self, threat_x: float, threat_y: float, speed: float, dt: float) -> None:
        """Directs heading away from threat coordinates and advances."""
        away_angle = self.angle_to(threat_x, threat_y) + math.pi
        self.heading = away_angle % (2.0 * math.pi)
        self.speed = speed
        self._move_forward(dt)

    def _move_forward(self, dt: float) -> None:
        self.x += math.cos(self.heading) * self.speed * dt
        self.y += math.sin(self.heading) * self.speed * dt

    def enforce_boundaries(self, config: Config) -> None:
        """Steers gently away from walls or clamps if outside."""
        pad = config.boundary_padding
        w, h = config.world_width, config.world_height

        # Turn inward if approaching boundaries
        if self.x < pad:
            self.x = pad
            self.heading = 0.0  # Turn right
        elif self.x > w - pad:
            self.x = w - pad
            self.heading = math.pi  # Turn left

        if self.y < pad:
            self.y = pad
            self.heading = math.pi / 2.0  # Turn down
        elif self.y > h - pad:
            self.y = h - pad
            self.heading = -math.pi / 2.0  # Turn up


class Prey(Animal):
    """Rabbit agent.
    
    Wanders when safe, flees when predators approach, and reproduces
    with logistic crowding control.
    """

    def __init__(
        self,
        entity_id: int,
        x: float,
        y: float,
        heading: float = 0.0,
        speed: float = 0.0,
    ) -> None:
        super().__init__(entity_id, x, y, heading, speed)

    def update_behavior(
        self,
        dt: float,
        config: Config,
        rng: random.Random,
        nearest_predator: Optional[Predator],
    ) -> None:
        if not self.alive:
            return

        self.age += dt
        if self.reproduction_cooldown > 0:
            self.reproduction_cooldown = max(0.0, self.reproduction_cooldown - dt)

        # Check natural old-age death
        if self.age >= config.prey_max_age:
            self.alive = False
            self.state = AnimalState.DIE
            return

        # Flee if a predator is within detection radius
        if nearest_predator and nearest_predator.alive:
            dist = self.distance_to(nearest_predator)
            if dist <= config.prey_vision_radius:
                self.state = AnimalState.FLEE
                self.move_away_from(nearest_predator.x, nearest_predator.y, config.prey_flee_speed, dt)
                self.enforce_boundaries(config)
                return

        # Otherwise wander peacefully
        self.state = AnimalState.WANDER
        self.wander(rng, dt, config.wander_heading_change_rate, config.prey_wander_speed)
        self.enforce_boundaries(config)

    def can_reproduce(self, config: Config, current_prey_count: int, rng: random.Random, dt: float) -> bool:
        """Determines reproduction under logistic crowding pressure."""
        if not self.alive or self.reproduction_cooldown > 0:
            return False

        # Crowding penalty: birth rate drops linearly as population approaches carrying capacity
        crowding_factor = max(0.0, 1.0 - (current_prey_count / config.prey_carrying_capacity))
        effective_rate = config.prey_birth_rate * crowding_factor
        prob = effective_rate * dt
        return rng.random() < prob


class Predator(Animal):
    """Fox agent.
    
    Hunts prey to replenish energy, burns energy over time, reproduces when full,
    and starves if energy depletes.
    """

    def __init__(
        self,
        entity_id: int,
        x: float,
        y: float,
        heading: float = 0.0,
        speed: float = 0.0,
        initial_energy: Optional[float] = None,
    ) -> None:
        super().__init__(entity_id, x, y, heading, speed)
        self.energy = 35.0 if initial_energy is None else float(initial_energy)
        self.eat_timer = 0.0
        self.target_prey_id: Optional[int] = None

    def update_behavior(
        self,
        dt: float,
        config: Config,
        rng: random.Random,
        nearest_prey: Optional[Prey],
    ) -> Optional[Prey]:
        """Updates predator movement, hunting, and energy.
        
        Returns the Prey instance if one was caught this frame, else None.
        """
        if not self.alive:
            return None

        self.age += dt
        if self.reproduction_cooldown > 0:
            self.reproduction_cooldown = max(0.0, self.reproduction_cooldown - dt)

        # Check natural old-age death
        if self.age >= config.predator_max_age:
            self.alive = False
            self.state = AnimalState.DIE
            return None

        # Handling eating state pause (plays attack/feed animation over caught prey)
        if self.eat_timer > 0:
            self.eat_timer = max(0.0, self.eat_timer - dt)
            self.state = AnimalState.EAT
            # Burn base metabolic energy while eating
            self.energy -= config.predator_energy_decay_wander * dt
            if self.energy <= 0:
                self.alive = False
                self.state = AnimalState.DIE
            return None

        caught_prey = None

        # Chase prey if detected within vision range
        if nearest_prey and nearest_prey.alive:
            dist = self.distance_to(nearest_prey)
            if dist <= config.predator_vision_radius:
                self.target_prey_id = nearest_prey.entity_id

                # Check if prey is caught
                if dist <= config.predator_catch_radius:
                    caught_prey = nearest_prey
                    self.energy = min(
                        config.predator_max_energy,
                        self.energy + config.predator_energy_gain_eat
                    )
                    self.eat_timer = 0.65  # Full attack/feasting animation sequence
                    self.state = AnimalState.EAT
                    self.target_prey_id = None
                    return caught_prey

                # Relentless pursuit
                self.state = AnimalState.CHASE
                self.move_toward(nearest_prey.x, nearest_prey.y, config.predator_chase_speed, dt)
                self.energy -= config.predator_energy_decay_chase * dt
                self.enforce_boundaries(config)
            else:
                self.target_prey_id = None
                self._wander_and_burn(rng, dt, config)
        else:
            self.target_prey_id = None
            self._wander_and_burn(rng, dt, config)

        # Starvation check
        if self.energy <= 0:
            self.alive = False
            self.state = AnimalState.DIE

        return caught_prey

    def _wander_and_burn(self, rng: random.Random, dt: float, config: Config) -> None:
        self.state = AnimalState.WANDER
        self.wander(rng, dt, config.wander_heading_change_rate, config.predator_wander_speed)
        self.energy -= config.predator_energy_decay_wander * dt
        self.enforce_boundaries(config)

    def can_reproduce(self, config: Config) -> bool:
        return (
            self.alive
            and self.reproduction_cooldown <= 0
            and self.energy >= config.predator_reproduce_threshold
        )
