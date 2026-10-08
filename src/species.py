"""Species profiles, trophic classification, and diet matrix.

Centralizes biological traits, movement parameters, dietary prey targets,
and social behavior modes for all 6 wildlife species.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Set


class TrophicRole(str, Enum):
    HERBIVORE = "Herbivore"
    CARNIVORE = "Carnivore"
    OMNIVORE = "Omnivore"


class SocialMode(str, Enum):
    SOLITARY = "Solitary"
    HERD = "Herd"
    PACK = "Pack"


@dataclass(frozen=True)
class SpeciesProfile:
    name: str
    display_name: str
    trophic_role: TrophicRole
    social_mode: SocialMode
    native_zone: str              # Key matching resident_species in terrain.py
    scale: float                  # Renderer sprite scale
    wander_speed: float
    sprint_speed: float
    vision_radius: float
    catch_radius: float
    initial_energy: float
    max_energy: float
    energy_decay_wander: float
    energy_decay_sprint: float
    energy_gain_feed: float
    reproduce_threshold: float
    reproduce_cost: float
    reproduction_cooldown: float
    max_age: float
    diet_prey: Set[str] = field(default_factory=set)  # Species names this animal hunts/eats
    is_small_refuge: bool = False                      # Can slip through thickets unhindered
    is_mountain_climber: bool = False                  # Immune to rocky mountain fatigue


SPECIES_REGISTRY: Dict[str, SpeciesProfile] = {
    "rabbit": SpeciesProfile(
        name="rabbit",
        display_name="Rabbit",
        trophic_role=TrophicRole.HERBIVORE,
        social_mode=SocialMode.HERD,
        native_zone="rabbit",
        scale=0.38,
        wander_speed=65.0,
        sprint_speed=130.0,
        vision_radius=135.0,
        catch_radius=10.0,
        initial_energy=40.0,
        max_energy=60.0,
        energy_decay_wander=1.2,
        energy_decay_sprint=3.0,
        energy_gain_feed=25.0,         # From grazing grass
        reproduce_threshold=42.0,
        reproduce_cost=18.0,
        reproduction_cooldown=3.5,
        max_age=45.0,
        diet_prey=set(),               # Eats grass from terrain
        is_small_refuge=True,
    ),
    "deer": SpeciesProfile(
        name="deer",
        display_name="Deer",
        trophic_role=TrophicRole.HERBIVORE,
        social_mode=SocialMode.HERD,
        native_zone="deer",
        scale=0.54,
        wander_speed=60.0,
        sprint_speed=145.0,           # Fast sprint in open plains
        vision_radius=150.0,
        catch_radius=14.0,
        initial_energy=60.0,
        max_energy=90.0,
        energy_decay_wander=1.4,
        energy_decay_sprint=4.0,
        energy_gain_feed=35.0,
        reproduce_threshold=65.0,
        reproduce_cost=30.0,
        reproduction_cooldown=7.0,
        max_age=60.0,
        diet_prey=set(),
    ),
    "goat": SpeciesProfile(
        name="goat",
        display_name="Mountain Goat",
        trophic_role=TrophicRole.HERBIVORE,
        social_mode=SocialMode.HERD,
        native_zone="goat",
        scale=0.48,
        wander_speed=55.0,
        sprint_speed=125.0,
        vision_radius=140.0,
        catch_radius=12.0,
        initial_energy=55.0,
        max_energy=80.0,
        energy_decay_wander=1.3,
        energy_decay_sprint=3.5,
        energy_gain_feed=30.0,
        reproduce_threshold=60.0,
        reproduce_cost=25.0,
        reproduction_cooldown=6.0,
        max_age=55.0,
        diet_prey=set(),
        is_mountain_climber=True,      # Scales rock at 100% speed!
    ),
    "fox": SpeciesProfile(
        name="fox",
        display_name="Fox",
        trophic_role=TrophicRole.CARNIVORE,
        social_mode=SocialMode.SOLITARY,
        native_zone="fox",
        scale=0.42,
        wander_speed=72.0,
        sprint_speed=136.0,
        vision_radius=130.0,
        catch_radius=16.0,
        initial_energy=35.0,
        max_energy=65.0,
        energy_decay_wander=1.8,
        energy_decay_sprint=4.0,
        energy_gain_feed=24.0,
        reproduce_threshold=52.0,
        reproduce_cost=25.0,
        reproduction_cooldown=9.0,
        max_age=50.0,
        diet_prey={"rabbit"},
        is_small_refuge=True,          # Navigates thickets smoothly
    ),
    "wolf": SpeciesProfile(
        name="wolf",
        display_name="Wolf",
        trophic_role=TrophicRole.CARNIVORE,
        social_mode=SocialMode.PACK,
        native_zone="wolf",
        scale=0.52,
        wander_speed=75.0,
        sprint_speed=142.0,
        vision_radius=130.0,
        catch_radius=18.0,
        initial_energy=40.0,
        max_energy=75.0,
        energy_decay_wander=1.9,
        energy_decay_sprint=4.2,
        energy_gain_feed=26.0,
        reproduce_threshold=56.0,
        reproduce_cost=30.0,
        reproduction_cooldown=10.0,
        max_age=55.0,
        diet_prey={"rabbit", "deer", "goat", "fox"},
    ),
    "bear": SpeciesProfile(
        name="bear",
        display_name="Bear",
        trophic_role=TrophicRole.OMNIVORE,
        social_mode=SocialMode.SOLITARY,
        native_zone="bear",
        scale=0.62,                   # Largest apex beast
        wander_speed=52.0,
        sprint_speed=132.0,
        vision_radius=125.0,
        catch_radius=22.0,
        initial_energy=60.0,
        max_energy=110.0,
        energy_decay_wander=1.5,
        energy_decay_sprint=4.8,
        energy_gain_feed=35.0,
        reproduce_threshold=80.0,
        reproduce_cost=40.0,
        reproduction_cooldown=14.0,
        max_age=70.0,
        diet_prey={"deer", "goat", "rabbit", "wolf"},
    ),
}
