"""Unit tests for Collective AI: Reynolds Boids Herds and Wolf Pack Tactics (Phase 6)."""

import math
import os
import unittest
import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()

from src.entities import Animal, AnimalState
from src.flocking import (
    check_herd_alarm,
    compute_boids_steering,
    compute_pack_flanking_angle,
    share_pack_kill,
)
from src.simulation import Simulation, SpatialGrid
from src.species import SPECIES_REGISTRY


class TestReynoldsBoidsFlocking(unittest.TestCase):
    """Verifies Separation, Alignment, Cohesion vectors and Herd Alarm propagation."""

    def setUp(self):
        self.profile = SPECIES_REGISTRY["deer"]

    def test_empty_flockmates_returns_none(self):
        deer = Animal(entity_id=1, profile=self.profile, x=100.0, y=100.0, heading=0.0)
        steer = compute_boids_steering(deer, [])
        self.assertIsNone(steer)

    def test_separation_force(self):
        # Deer 1 at (100, 100), Deer 2 at (105, 105) (close neighbor on diagonal)
        deer1 = Animal(entity_id=1, profile=self.profile, x=100.0, y=100.0, heading=0.0)
        deer2 = Animal(entity_id=2, profile=self.profile, x=105.0, y=105.0, heading=0.0)

        steer = compute_boids_steering(deer1, [deer2], separation_dist=25.0)
        self.assertIsNotNone(steer)
        # Steer should turn away from Deer 2
        self.assertNotEqual(steer, 0.0)

    def test_check_herd_alarm_detection(self):
        deer1 = Animal(entity_id=1, profile=self.profile, x=100.0, y=100.0)
        deer2 = Animal(entity_id=2, profile=self.profile, x=120.0, y=100.0)
        deer2.state = AnimalState.WANDER

        # No alarm when wandering
        alarm = check_herd_alarm(deer1, [deer2])
        self.assertIsNone(alarm)

        # Alarm detected when peer enters FLEE
        deer2.state = AnimalState.FLEE
        alarm = check_herd_alarm(deer1, [deer2])
        self.assertIsNotNone(alarm)
        self.assertEqual(alarm.entity_id, 2)

    def test_herd_panic_propagation(self):
        # Deer 1 is alarmed (in FLEE state), Deer 2 wanders nearby with no direct predator threat
        deer1 = Animal(entity_id=1, profile=self.profile, x=200.0, y=200.0, heading=math.pi)
        deer1.state = AnimalState.FLEE

        deer2 = Animal(entity_id=2, profile=self.profile, x=220.0, y=200.0, heading=0.0)
        deer2.state = AnimalState.WANDER

        # Update deer2 behavior with deer1 as nearby ally and threat=None
        deer2.update_behavior(dt=0.1, threat=None, nearby_allies=[deer1])
        # Deer 2 should have caught the panic and entered FLEE state with matching flight direction
        self.assertEqual(deer2.state, AnimalState.FLEE)
        self.assertEqual(deer2.heading, deer1.heading)


class TestWolfPackTactics(unittest.TestCase):
    """Verifies tactical flanking pursuit angles and pack feasting kill sharing."""

    def setUp(self):
        self.wolf_prof = SPECIES_REGISTRY["wolf"]
        self.deer_prof = SPECIES_REGISTRY["deer"]

    def test_flanking_pursuit_angles(self):
        quarry = Animal(entity_id=99, profile=self.deer_prof, x=500.0, y=500.0)

        # Lead wolf is at (400, 500) (dist = 100)
        lead_wolf = Animal(entity_id=1, profile=self.wolf_prof, x=400.0, y=500.0)
        lead_wolf.target_prey_id = 99

        # Flanker wolf 1 is at (350, 500) (dist = 150)
        flank1_wolf = Animal(entity_id=2, profile=self.wolf_prof, x=350.0, y=500.0)
        flank1_wolf.target_prey_id = 99

        # Flanker wolf 2 is at (300, 500) (dist = 200)
        flank2_wolf = Animal(entity_id=3, profile=self.wolf_prof, x=300.0, y=500.0)
        flank2_wolf.target_prey_id = 99

        pack = [lead_wolf, flank1_wolf, flank2_wolf]

        # Lead wolf pursues directly
        lead_angle = compute_pack_flanking_angle(lead_wolf, quarry, pack)
        direct_to_quarry = lead_wolf.angle_to(quarry.x, quarry.y)
        self.assertAlmostEqual(lead_angle, direct_to_quarry, places=4)

        # Flanker 1 takes +35 deg offset
        f1_angle = compute_pack_flanking_angle(flank1_wolf, quarry, pack)
        self.assertNotEqual(f1_angle, flank1_wolf.angle_to(quarry.x, quarry.y))

        # Flanker 2 takes -35 deg offset
        f2_angle = compute_pack_flanking_angle(flank2_wolf, quarry, pack)
        self.assertNotEqual(f2_angle, flank2_wolf.angle_to(quarry.x, quarry.y))

    def test_pack_kill_energy_sharing(self):
        killer = Animal(entity_id=1, profile=self.wolf_prof, x=300.0, y=300.0)
        victim = Animal(entity_id=99, profile=self.deer_prof, x=302.0, y=300.0)

        # Pack mate in close feasting range (dist = 20)
        mate_close = Animal(entity_id=2, profile=self.wolf_prof, x=320.0, y=300.0)
        mate_close.energy = 30.0

        # Pack mate far away (dist = 200)
        mate_far = Animal(entity_id=3, profile=self.wolf_prof, x=500.0, y=300.0)
        mate_far.energy = 30.0

        feasters = share_pack_kill(killer, victim, [mate_close, mate_far], feasting_radius=60.0)
        self.assertIn(mate_close, feasters)
        self.assertNotIn(mate_far, feasters)

        # Mate close should now be in EAT state and have gained energy
        self.assertEqual(mate_close.state, AnimalState.EAT)
        self.assertGreater(mate_close.energy, 30.0)


class TestSpatialGridFindAllCandidates(unittest.TestCase):
    """Verifies SpatialGrid.find_all_candidates range queries."""

    def test_find_all_candidates(self):
        grid = SpatialGrid(cell_size=100.0)
        prof = SPECIES_REGISTRY["rabbit"]

        a1 = Animal(entity_id=1, profile=prof, x=50.0, y=50.0)
        a2 = Animal(entity_id=2, profile=prof, x=70.0, y=50.0)
        a3 = Animal(entity_id=3, profile=prof, x=400.0, y=400.0)

        grid.insert(a1)
        grid.insert(a2)
        grid.insert(a3)

        near_a1 = grid.find_all_candidates(50.0, 50.0, radius=50.0)
        self.assertIn(a1, near_a1)
        self.assertIn(a2, near_a1)
        self.assertNotIn(a3, near_a1)


if __name__ == "__main__":
    unittest.main()
