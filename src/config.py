"""Centralized configuration for the predator-prey ecosystem simulation.

Every tunable number lives here in a frozen dataclass to ensure zero magic numbers
across entities, rules, and tests.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    # World boundaries
    world_width: float = 1200.0
    world_height: float = 800.0

    # Simulation defaults
    step_dt: float = 1.0 / 60.0
    metrics_interval: float = 1.0
    default_seed: int = 42

    # Initial populations (tuned for balanced dynamic coexistence)
    initial_prey: int = 160
    initial_predators: int = 12

    # Prey (Rabbit) Parameters
    prey_wander_speed: float = 65.0
    prey_flee_speed: float = 130.0
    prey_vision_radius: float = 130.0
    prey_birth_rate: float = 0.48          # Base per-capita births per second
    prey_carrying_capacity: int = 300      # Crowding limit
    prey_reproduction_cooldown: float = 3.5
    prey_max_age: float = 48.0             # Natural lifespan limit

    # Predator (Fox) Parameters
    predator_wander_speed: float = 75.0
    predator_chase_speed: float = 142.0
    predator_vision_radius: float = 120.0
    predator_catch_radius: float = 18.0
    predator_initial_energy: float = 35.0
    predator_max_energy: float = 65.0
    predator_energy_decay_wander: float = 2.0   # Energy burned per sec while wandering
    predator_energy_decay_chase: float = 4.5    # Energy burned per sec while chasing
    predator_energy_gain_eat: float = 18.0      # Energy obtained from consuming prey
    predator_reproduce_threshold: float = 56.0  # Min energy required to reproduce
    predator_reproduce_cost: float = 32.0       # Energy transferred to offspring
    predator_reproduction_cooldown: float = 10.0
    predator_max_age: float = 52.0

    # Steering and movement
    wander_heading_change_rate: float = 1.5     # Radians per second drift
    boundary_padding: float = 20.0             # Soft padding near borders
